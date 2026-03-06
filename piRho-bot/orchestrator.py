"""
Bot Orchestrator for Multi-User Multi-Bot Trading System
Manages multiple trading bots as asyncio tasks with database synchronization
"""

import logging
import asyncio
import signal
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Set, Tuple
from aiohttp import web

from db_client import get_db_client, DatabaseClient
from bot_instance import TradingBotInstance

logger = logging.getLogger(__name__)


class BotOrchestrator:
    """
    Manages multiple trading bots as asyncio tasks.
    Synchronizes with database to start/stop bots based on their status.
    """
    
    def __init__(self, poll_interval: int = 10):
        """
        Initialize the bot orchestrator.
        
        Args:
            poll_interval: Seconds between database polls
        """
        self.instance_id = str(uuid.uuid4())[:8]
        self.poll_interval = poll_interval
        self.is_running = False
        
        # Active bots: bot_id -> (task, instance)
        self.active_bots: Dict[str, tuple[asyncio.Task, TradingBotInstance]] = {}
        
        # Failed bots: bot_id -> (failure_count, last_failure_time, error_message)
        # Prevents infinite retry loops for bots that can't initialize
        self.failed_bots: Dict[str, tuple[int, datetime, str]] = {}
        self.max_failures = 3  # Max failures before giving up
        self.failure_cooldown = 300  # 5 minutes cooldown after max failures
        
        # Database client
        self.db_client: Optional[DatabaseClient] = None
        
        # Global configuration
        self.global_config: Dict = {}
        
        # Shutdown event
        self._shutdown_event = asyncio.Event()
        
        # Health check server
        self._health_server: Optional[web.Application] = None
        self._health_runner: Optional[web.AppRunner] = None
        
        logger.info(f"[Orchestrator:{self.instance_id}] Initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize the orchestrator and database connection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[Orchestrator:{self.instance_id}] Starting initialization...")
            
            # Initialize database client
            self.db_client = get_db_client()
            
            # Get global configuration
            self.global_config = await self.db_client.get_global_config()
            
            # Acquire orchestrator lock (for distributed setups)
            if not await self.db_client.get_orchestrator_lock(self.instance_id):
                logger.error("Another orchestrator instance is already running")
                return False
            
            # Start health check server
            await self._start_health_server()
            
            logger.info(f"[Orchestrator:{self.instance_id}] Initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"[Orchestrator:{self.instance_id}] Initialization failed: {e}", exc_info=True)
            return False
    
    async def _start_health_server(self):
        """Start HTTP health check server on port 8000."""
        try:
            app = web.Application()
            
            async def health_check(request):
                """Health check endpoint."""
                return web.json_response({
                    'status': 'healthy',
                    'instance_id': self.instance_id,
                    'is_running': self.is_running,
                    'active_bots': len(self.active_bots)
                })
            
            app.router.add_get('/health', health_check)
            app.router.add_get('/', health_check)  # Root also serves health check
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', 8000)
            await site.start()
            
            self._health_runner = runner
            logger.info(f"[Orchestrator:{self.instance_id}] Health check server started on port 8000")
            
        except Exception as e:
            logger.warning(f"[Orchestrator:{self.instance_id}] Failed to start health server: {e}")
            # Don't fail initialization if health server fails
    
    async def sync_with_database(self):
        """
        Synchronize running bots with database state.
        Starts new bots and stops removed/paused bots.
        """
        try:
            # Get all running bots from database
            db_bots = await self.db_client.get_running_bots()
            db_bot_ids: Set[str] = {bot['id'] for bot in db_bots}
            
            # Get currently active bot IDs
            active_bot_ids: Set[str] = set(self.active_bots.keys())
            
            # Find bots to start (in DB but not active)
            bots_to_start = db_bot_ids - active_bot_ids
            
            # Find bots to stop (active but not in DB as running)
            bots_to_stop = active_bot_ids - db_bot_ids
            
            # Clear failed status for bots that were stopped (user may retry later)
            for bot_id in list(self.failed_bots.keys()):
                if bot_id not in db_bot_ids:
                    del self.failed_bots[bot_id]
            
            # Start new bots (skip if in cooldown from failures)
            started_count = 0
            skipped_count = 0
            for bot_data in db_bots:
                if bot_data['id'] in bots_to_start:
                    if self._should_skip_bot(bot_data['id']):
                        skipped_count += 1
                        continue
                    if await self.start_bot(bot_data):
                        started_count += 1
            
            # Stop removed bots
            for bot_id in bots_to_stop:
                await self.stop_bot(bot_id)
            
            if started_count or bots_to_stop or skipped_count:
                msg = f"[Orchestrator:{self.instance_id}] Sync: Started {started_count}"
                if skipped_count:
                    msg += f", Skipped {skipped_count} (failed)"
                msg += f", Stopped {len(bots_to_stop)}, Active: {len(self.active_bots)}"
                logger.info(msg)
                
        except Exception as e:
            logger.error(f"[Orchestrator:{self.instance_id}] Sync failed: {e}", exc_info=True)
    
    def _should_skip_bot(self, bot_id: str) -> bool:
        """Check if bot should be skipped due to repeated failures."""
        if bot_id not in self.failed_bots:
            return False
        
        failure_count, last_failure, error = self.failed_bots[bot_id]
        
        # If exceeded max failures, check cooldown
        if failure_count >= self.max_failures:
            elapsed = (datetime.now(timezone.utc) - last_failure).total_seconds()
            if elapsed < self.failure_cooldown:
                # Still in cooldown
                return True
            else:
                # Cooldown expired, reset and allow retry
                logger.info(f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} cooldown expired, allowing retry")
                del self.failed_bots[bot_id]
                return False
        
        return False
    
    def _record_bot_failure(self, bot_id: str, error: str):
        """Record a bot initialization failure."""
        if bot_id in self.failed_bots:
            count, _, _ = self.failed_bots[bot_id]
            self.failed_bots[bot_id] = (count + 1, datetime.now(timezone.utc), error)
        else:
            self.failed_bots[bot_id] = (1, datetime.now(timezone.utc), error)
        
        count = self.failed_bots[bot_id][0]
        if count >= self.max_failures:
            logger.warning(
                f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} failed {count} times, "
                f"entering {self.failure_cooldown}s cooldown"
            )
    
    async def start_bot(self, bot_data: Dict) -> bool:
        """
        Start a bot as an asyncio task.
        
        Args:
            bot_data: Bot configuration from database
            
        Returns:
            True if started successfully, False otherwise
        """
        bot_id = bot_data['id']
        
        if bot_id in self.active_bots:
            logger.warning(f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} already running")
            return False
        
        try:
            logger.info(f"[Orchestrator:{self.instance_id}] Starting bot {bot_id[:8]}...")
            
            # Create bot instance
            instance = TradingBotInstance(
                bot_id=bot_id,
                tenant_id=bot_data['tenant_id'],
                bot_name=bot_data['name'],
                symbol=bot_data['symbol'],
                strategy_name=bot_data['strategy'],
                bot_config=bot_data.get('config', {}),
                credentials=bot_data['credentials'],
                global_config=self.global_config,
                db_client=self.db_client
            )
            
            # Initialize bot
            if not await instance.initialize():
                error_msg = instance.last_error or "Initialization failed"
                logger.error(f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} failed to initialize: {error_msg}")
                
                # Record failure to prevent infinite retries
                self._record_bot_failure(bot_id, error_msg)
                
                # Try to update status to 'error' in database
                await self.db_client.update_bot_status(bot_id, 'error', error_msg)
                return False
            
            # Create task with status callback
            task = asyncio.create_task(
                instance.run_loop(status_callback=self._on_bot_status_update),
                name=f"bot_{bot_id[:8]}"
            )
            
            # Store reference
            self.active_bots[bot_id] = (task, instance)
            
            # Clear any previous failures on successful start
            if bot_id in self.failed_bots:
                del self.failed_bots[bot_id]
            
            logger.info(
                f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} started: "
                f"{bot_data['symbol']} / {bot_data['strategy']}"
            )
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[Orchestrator:{self.instance_id}] Failed to start bot {bot_id[:8]}: {e}", exc_info=True)
            self._record_bot_failure(bot_id, error_msg)
            await self.db_client.update_bot_status(bot_id, 'error', error_msg)
            return False
    
    async def stop_bot(self, bot_id: str, reason: str = "stopped"):
        """
        Stop a running bot gracefully.
        
        Args:
            bot_id: Bot identifier
            reason: Reason for stopping
        """
        if bot_id not in self.active_bots:
            logger.warning(f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} not in active bots")
            return
        
        try:
            task, instance = self.active_bots.get(bot_id)
            if not task or not instance:
                logger.warning(f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} entry invalid")
                if bot_id in self.active_bots:
                    del self.active_bots[bot_id]
                return
            
            logger.info(f"[Orchestrator:{self.instance_id}] Stopping bot {bot_id[:8]}...")
            
            # Signal the bot to stop
            try:
                await instance.stop()
            except Exception as e:
                logger.warning(f"[Orchestrator:{self.instance_id}] Error calling stop on bot {bot_id[:8]}: {e}")
            
            # Cancel the task
            if not task.done():
                task.cancel()
                
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} did not stop gracefully")
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.warning(f"[Orchestrator:{self.instance_id}] Error waiting for bot {bot_id[:8]} task: {e}")
            
            # Remove from active bots (use pop to avoid KeyError)
            self.active_bots.pop(bot_id, None)
            
            logger.info(f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} stopped ({reason})")
            
        except KeyError as e:
            # Bot already removed, this is fine
            logger.debug(f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} already removed: {e}")
            self.active_bots.pop(bot_id, None)
        except Exception as e:
            logger.error(f"[Orchestrator:{self.instance_id}] Error stopping bot {bot_id[:8]}: {e}", exc_info=True)
            # Ensure it's removed from tracking
            self.active_bots.pop(bot_id, None)
    
    async def _on_bot_status_update(self, bot_id: str, status: Dict):
        """
        Callback for bot status updates.
        Updates the database with heartbeat and metrics.
        
        Args:
            bot_id: Bot identifier
            status: Status dictionary from bot instance
        """
        try:
            await self.db_client.update_bot_heartbeat(
                bot_id=bot_id,
                heartbeat_at=datetime.now(timezone.utc),
                error_message=status.get('last_error'),
                trades_count=status.get('trades_count'),
                pnl_total=status.get('total_pnl')
            )
        except Exception as e:
            logger.error(f"[Orchestrator:{self.instance_id}] Status update failed for {bot_id[:8]}: {e}")
    
    async def _check_daily_reset(self):
        """Check if we need to reset daily counters (at midnight UTC)."""
        now = datetime.now(timezone.utc)
        if now.hour == 0 and now.minute < 1:
            for _, instance in self.active_bots.values():
                instance.reset_daily_counters()
    
    async def run(self):
        """
        Main orchestrator loop.
        Continuously syncs with database and monitors active bots.
        """
        if not await self.initialize():
            logger.error("Failed to initialize orchestrator")
            return
        
        self.is_running = True
        logger.info(f"[Orchestrator:{self.instance_id}] Running... (poll interval: {self.poll_interval}s)")
        
        # Initial sync
        await self.sync_with_database()
        
        while self.is_running and not self._shutdown_event.is_set():
            try:
                # Sync with database
                await self.sync_with_database()
                
                # Check for daily reset
                await self._check_daily_reset()
                
                # Check for dead tasks and remove them
                dead_bots = []
                for bot_id, (task, instance) in self.active_bots.items():
                    if task.done():
                        try:
                            # Check if task raised exception
                            exc = task.exception()
                            if exc:
                                logger.error(f"[Orchestrator:{self.instance_id}] Bot {bot_id[:8]} crashed: {exc}")
                                await self.db_client.update_bot_status(bot_id, 'error', str(exc))
                        except asyncio.CancelledError:
                            pass
                        dead_bots.append(bot_id)
                
                for bot_id in dead_bots:
                    del self.active_bots[bot_id]
                
                # Log status periodically
                if len(self.active_bots) > 0:
                    logger.debug(
                        f"[Orchestrator:{self.instance_id}] Active bots: {len(self.active_bots)}"
                    )
                
                # Wait for next poll
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.poll_interval
                    )
                except asyncio.TimeoutError:
                    pass  # Normal timeout, continue loop
                    
            except asyncio.CancelledError:
                logger.info(f"[Orchestrator:{self.instance_id}] Received cancellation signal")
                break
            except Exception as e:
                logger.error(f"[Orchestrator:{self.instance_id}] Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)
        
        # Shutdown
        await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown all bots and cleanup."""
        # Prevent multiple shutdown calls
        if not self.is_running:
            logger.debug(f"[Orchestrator:{self.instance_id}] Shutdown already in progress")
            return
        
        logger.info(f"[Orchestrator:{self.instance_id}] Shutting down...")
        self.is_running = False
        self._shutdown_event.set()
        
        # Stop all active bots
        stop_tasks = []
        bot_ids = list(self.active_bots.keys())  # Copy list to avoid modification during iteration
        for bot_id in bot_ids:
            stop_tasks.append(self.stop_bot(bot_id, "orchestrator_shutdown"))
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        # Stop health check server
        if self._health_runner:
            try:
                await self._health_runner.cleanup()
                logger.info(f"[Orchestrator:{self.instance_id}] Health check server stopped")
            except Exception as e:
                logger.warning(f"[Orchestrator:{self.instance_id}] Error stopping health server: {e}")
        
        # Release lock
        if self.db_client:
            try:
                await self.db_client.release_orchestrator_lock(self.instance_id)
            except Exception as e:
                logger.warning(f"[Orchestrator:{self.instance_id}] Error releasing lock: {e}")
        
        logger.info(f"[Orchestrator:{self.instance_id}] Shutdown complete")
    
    def get_status(self) -> Dict:
        """Get orchestrator status."""
        return {
            'instance_id': self.instance_id,
            'is_running': self.is_running,
            'active_bots_count': len(self.active_bots),
            'active_bots': [
                {
                    'bot_id': bot_id,
                    'status': instance.get_status()
                }
                for bot_id, (_, instance) in self.active_bots.items()
            ],
            'poll_interval': self.poll_interval,
        }


async def run_orchestrator():
    """Run the bot orchestrator with signal handling."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                'orchestrator.log',
                maxBytes=5_000_000,
                backupCount=5
            )
        ]
    )
    
    logger.info("Starting Bot Orchestrator...")
    
    orchestrator = BotOrchestrator(poll_interval=10)
    
    # Setup signal handlers
    loop = asyncio.get_running_loop()
    shutdown_called = False
    
    def signal_handler(sig):
        nonlocal shutdown_called
        if shutdown_called:
            logger.debug(f"Shutdown already initiated, ignoring signal {sig.name}")
            return
        shutdown_called = True
        logger.info(f"Received signal {sig.name}, initiating shutdown...")
        asyncio.create_task(orchestrator.shutdown())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
    
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await orchestrator.shutdown()
    except Exception as e:
        logger.exception(f"Orchestrator crashed: {e}")
        await orchestrator.shutdown()
        raise


if __name__ == "__main__":
    import logging.handlers
    asyncio.run(run_orchestrator())

