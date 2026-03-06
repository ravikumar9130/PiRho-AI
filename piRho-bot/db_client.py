"""
Database Client for Bot Orchestrator
Handles Supabase connection, credential decryption, and bot status updates
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from functools import lru_cache

from dotenv import load_dotenv
from supabase import create_client, Client
from cryptography.fernet import Fernet

load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseClient:
    """
    Supabase client wrapper for the bot orchestrator.
    Handles fetching bots, credentials, and updating status.
    """
    
    def __init__(self):
        """Initialize the database client."""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')  # Use service key for full access
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY must be set for credential decryption")
        
        # Initialize Supabase client
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize encryptor
        key = self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key
        self._fernet = Fernet(key)
        
        logger.info("Database client initialized")
    
    def decrypt_credential(self, encrypted_value: str) -> str:
        """
        Decrypt an encrypted credential.
        
        Args:
            encrypted_value: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        try:
            return self._fernet.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt credential: {e}")
            raise
    
    async def get_running_bots(self) -> List[Dict[str, Any]]:
        """
        Fetch all bots with status='running' along with their credentials.
        
        Returns:
            List of bot dictionaries with decrypted credentials
        """
        try:
            # Fetch bots with status='running' and join with exchange_credentials
            # We need to get the tenant's exchange credentials for each bot
            result = self.client.table('bots').select(
                '*, tenants!inner(id, user_id, plan, exchange_credentials(*))'
            ).eq('status', 'running').execute()
            
            bots = []
            for bot_data in result.data or []:
                tenant = bot_data.get('tenants', {})
                credentials_list = tenant.get('exchange_credentials', [])
                
                if not credentials_list:
                    logger.warning(f"Bot {bot_data['id']} has no exchange credentials, skipping")
                    continue
                
                # Use the first (and usually only) credential for now
                cred = credentials_list[0]
                
                try:
                    # Decrypt credentials
                    decrypted_credentials = {
                        'api_key': self.decrypt_credential(cred['encrypted_api_key']),
                        'api_secret': self.decrypt_credential(cred['encrypted_api_secret']),
                        'is_testnet': cred.get('is_testnet', True),
                        'exchange': cred.get('exchange', 'bybit'),
                    }
                    
                    bots.append({
                        'id': bot_data['id'],
                        'tenant_id': bot_data['tenant_id'],
                        'name': bot_data['name'],
                        'symbol': bot_data['symbol'],
                        'strategy': bot_data['strategy'],
                        'config': bot_data.get('config', {}),
                        'status': bot_data['status'],
                        'credentials': decrypted_credentials,
                    })
                except Exception as e:
                    logger.error(f"Failed to process bot {bot_data['id']}: {e}")
                    continue
            
            logger.info(f"Fetched {len(bots)} running bots from database")
            return bots
            
        except Exception as e:
            logger.error(f"Failed to fetch running bots: {e}", exc_info=True)
            return []
    
    async def get_all_bot_statuses(self) -> Dict[str, str]:
        """
        Get status of all bots (for sync check).
        
        Returns:
            Dictionary mapping bot_id to status
        """
        try:
            result = self.client.table('bots').select('id, status').execute()
            return {bot['id']: bot['status'] for bot in result.data or []}
        except Exception as e:
            logger.error(f"Failed to fetch bot statuses: {e}")
            return {}
    
    async def update_bot_heartbeat(
        self,
        bot_id: str,
        heartbeat_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        trades_count: Optional[int] = None,
        pnl_total: Optional[float] = None
    ):
        """
        Update bot heartbeat and status in database.
        
        Args:
            bot_id: Bot identifier
            heartbeat_at: Heartbeat timestamp (defaults to now)
            error_message: Error message if any
            trades_count: Number of trades executed
            pnl_total: Total PnL
        """
        try:
            # Use only columns that exist in the base schema
            update_data = {
                'last_active_at': datetime.now(timezone.utc).isoformat(),
            }
            
            # Try to include optional columns (may not exist if schema not updated)
            try:
                if heartbeat_at or True:  # Always try to update heartbeat
                    update_data['heartbeat_at'] = (heartbeat_at or datetime.now(timezone.utc)).isoformat()
                if error_message is not None:
                    update_data['error_message'] = error_message
                if trades_count is not None:
                    update_data['trades_count'] = trades_count
                if pnl_total is not None:
                    update_data['pnl_total'] = pnl_total
            except Exception:
                pass  # Columns may not exist yet
            
            self.client.table('bots').update(update_data).eq('id', bot_id).execute()
            
        except Exception as e:
            # If update fails due to missing columns, try with minimal fields
            try:
                minimal_update = {'last_active_at': datetime.now(timezone.utc).isoformat()}
                self.client.table('bots').update(minimal_update).eq('id', bot_id).execute()
            except Exception as e2:
                logger.error(f"Failed to update bot {bot_id} heartbeat: {e2}")
    
    async def update_bot_status(self, bot_id: str, status: str, error_message: Optional[str] = None):
        """
        Update bot status in database.
        
        Args:
            bot_id: Bot identifier
            status: New status (stopped, running, error, paused)
            error_message: Error message if status is 'error'
        """
        try:
            # Base update data (columns that always exist)
            update_data = {
                'status': status,
                'last_active_at': datetime.now(timezone.utc).isoformat(),
            }
            
            # Try with error_message column
            if error_message:
                update_data['error_message'] = error_message
            elif status != 'error':
                update_data['error_message'] = None
            
            try:
                self.client.table('bots').update(update_data).eq('id', bot_id).execute()
                logger.info(f"Updated bot {bot_id} status to {status}")
            except Exception as e:
                # If fails (likely missing column), try without error_message
                if 'error_message' in str(e):
                    minimal_update = {
                        'status': status,
                        'last_active_at': datetime.now(timezone.utc).isoformat(),
                    }
                    self.client.table('bots').update(minimal_update).eq('id', bot_id).execute()
                    logger.info(f"Updated bot {bot_id} status to {status} (without error_message)")
                else:
                    raise
            
        except Exception as e:
            logger.error(f"Failed to update bot {bot_id} status: {e}")
    
    async def record_open_trade(
        self,
        tenant_id: str,
        bot_id: str,
        trade_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Record an open trade in the database (when position is opened).
        
        Args:
            tenant_id: Tenant identifier
            bot_id: Bot identifier
            trade_data: Trade details dictionary
            
        Returns:
            Trade ID if successful, None otherwise
        """
        try:
            record = {
                'tenant_id': tenant_id,
                'bot_id': bot_id,
                'symbol': trade_data.get('symbol'),
                'side': trade_data.get('type', trade_data.get('side')),  # BUY or SELL
                'entry_price': trade_data.get('entry_price'),
                'quantity': trade_data.get('quantity'),
                'leverage': trade_data.get('leverage', 1),
                'strategy': trade_data.get('Strategy'),
                'opened_at': trade_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'closed_at': None,  # NULL = open position
                'is_paper': trade_data.get('paper_trade', False),
                'metadata': trade_data,
            }
            
            result = self.client.table('trades').insert(record).execute()
            
            if result.data:
                trade_id = result.data[0].get('id')
                logger.info(f"Recorded open trade {trade_id} for bot {bot_id}")
                return trade_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to record open trade: {e}")
            return None
    
    async def close_trade(
        self,
        trade_id: str,
        exit_data: Dict[str, Any]
    ):
        """
        Update a trade when position is closed.
        
        Args:
            trade_id: Trade identifier
            exit_data: Exit details dictionary
        """
        try:
            update = {
                'exit_price': exit_data.get('ExitPrice'),
                'profit_loss': exit_data.get('ProfitLoss'),
                'profit_loss_percent': exit_data.get('ProfitLossPercent'),
                'exit_reason': exit_data.get('ExitReason'),
                'closed_at': datetime.now(timezone.utc).isoformat(),
            }
            
            self.client.table('trades').update(update).eq('id', trade_id).execute()
            logger.info(f"Closed trade {trade_id}")
            
        except Exception as e:
            logger.error(f"Failed to close trade {trade_id}: {e}")
    
    async def record_trade(
        self,
        tenant_id: str,
        bot_id: str,
        trade_data: Dict[str, Any]
    ):
        """
        Record a completed trade in the database (legacy method for closed trades).
        
        Args:
            tenant_id: Tenant identifier
            bot_id: Bot identifier
            trade_data: Trade details dictionary
        """
        try:
            record = {
                'tenant_id': tenant_id,
                'bot_id': bot_id,
                'symbol': trade_data.get('Symbol'),
                'side': trade_data.get('TradeType'),
                'entry_price': trade_data.get('EntryPrice'),
                'exit_price': trade_data.get('ExitPrice'),
                'quantity': trade_data.get('Quantity'),
                'leverage': trade_data.get('Leverage', 1),
                'profit_loss': trade_data.get('ProfitLoss'),
                'profit_loss_percent': trade_data.get('ProfitLossPercent'),
                'strategy': trade_data.get('Strategy'),
                'exit_reason': trade_data.get('ExitReason'),
                'opened_at': trade_data.get('OpenedAt'),
                'closed_at': datetime.now(timezone.utc).isoformat(),
                'is_paper': trade_data.get('PaperTrade', False),
                'metadata': trade_data,
            }
            
            self.client.table('trades').insert(record).execute()
            logger.info(f"Recorded trade for bot {bot_id}")
            
        except Exception as e:
            logger.error(f"Failed to record trade: {e}")
    
    async def record_signal_log(
        self,
        tenant_id: str,
        bot_id: str,
        signal: str,
        strategy: str,
        symbol: str,
        signal_reason: str,
        market_data: Dict[str, Any],
        sentiment: Optional[str] = None,
        funding_rate: Optional[float] = None,
        trade_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Record a signal log entry in the database.
        
        Args:
            tenant_id: Tenant identifier
            bot_id: Bot identifier
            signal: Signal type (BUY or SELL)
            strategy: Strategy name
            symbol: Trading symbol
            signal_reason: Human-readable reason for the signal
            market_data: Dictionary with technical indicators and market context
            sentiment: Market sentiment (optional)
            funding_rate: Funding rate if applicable (optional)
            trade_id: Associated trade ID if trade was executed (optional)
            
        Returns:
            Signal log ID if successful, None otherwise
        """
        try:
            record = {
                'tenant_id': tenant_id,
                'bot_id': bot_id,
                'symbol': symbol,
                'signal': signal,
                'strategy': strategy,
                'signal_reason': signal_reason,
                'market_data': market_data,
                'sentiment': sentiment,
                'funding_rate': funding_rate,
                'trade_id': trade_id,
                'created_at': datetime.now(timezone.utc).isoformat(),
            }
            
            result = self.client.table('signal_logs').insert(record).execute()
            
            if result.data:
                signal_log_id = result.data[0].get('id')
                logger.info(f"Recorded signal log {signal_log_id} for bot {bot_id}")
                return signal_log_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to record signal log: {e}")
            return None
    
    async def get_global_config(self) -> Dict[str, Any]:
        """
        Get global orchestrator configuration.
        For now, returns defaults. Can be extended to fetch from database.
        
        Returns:
            Global configuration dictionary
        """
        return {
            'chart_timeframe': '15',
            'analysis_lookback': 200,
            'signal_cooldown_minutes': 30,
            'enable_sentiment_analysis': True,
            'poll_interval_seconds': 10,
            'ai': {
                'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
                'lstm_sequence_length': 30,
                'lstm_confidence_threshold': 0.65,
                'lstm_auto_train': True,
            },
            'sentiment': {
                'news_api_key': os.getenv('NEWS_API_KEY', ''),
                'cryptopanic_api_key': os.getenv('CRYPTOPANIC_API_KEY', ''),
                'use_fear_greed_index': True,
            },
        }
    
    async def get_orchestrator_lock(self, instance_id: str) -> bool:
        """
        Try to acquire orchestrator lock to prevent multiple instances.
        Uses a simple row in a locks table.
        
        Args:
            instance_id: Unique identifier for this orchestrator instance
            
        Returns:
            True if lock acquired, False if another instance is running
        """
        try:
            # Check if locks table exists and if there's an active lock
            # For MVP, we'll skip the distributed lock and rely on systemd
            # to ensure only one instance runs
            return True
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False
    
    async def release_orchestrator_lock(self, instance_id: str):
        """Release orchestrator lock."""
        pass  # Placeholder for distributed locking


# Singleton instance
_db_client: Optional[DatabaseClient] = None


def get_db_client() -> DatabaseClient:
    """Get or create the database client singleton."""
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client

