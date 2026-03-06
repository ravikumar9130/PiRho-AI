"""
Lightweight Trading Bot Instance for Multi-Bot Orchestration
Runs as an asyncio coroutine managed by BotOrchestrator
"""

import logging
import asyncio
import datetime
from typing import Optional, Dict, Any

from bybit_client import BybitClient
from agents import OrderExecutionAgent, PositionManagementAgent
from sentiment_agent import CryptoSentimentAgent
from strategy_factory import get_strategy
from indicators import calculate_all_indicators
from lstm_predictor import get_model_manager

logger = logging.getLogger(__name__)


class TradingBotInstance:
    """
    Lightweight trading bot instance that runs as an asyncio coroutine.
    Each instance manages a single bot with its own strategy and credentials.
    """
    
    def __init__(
        self,
        bot_id: str,
        tenant_id: str,
        bot_name: str,
        symbol: str,
        strategy_name: str,
        bot_config: Dict[str, Any],
        credentials: Dict[str, Any],
        global_config: Optional[Dict[str, Any]] = None,
        db_client = None
    ):
        """
        Initialize a trading bot instance.
        
        Args:
            bot_id: Unique bot identifier from database
            tenant_id: Owner tenant ID
            bot_name: Human-readable bot name
            symbol: Trading symbol (e.g., "BTCUSDT")
            strategy_name: Strategy to use (e.g., "LSTM_Momentum")
            bot_config: Bot-specific configuration (leverage, risk, etc.)
            credentials: Decrypted exchange credentials
            global_config: Global trading configuration (optional)
            db_client: Database client for saving trades
        """
        self.bot_id = bot_id
        self.tenant_id = tenant_id
        self.bot_name = bot_name
        self.symbol = symbol
        self.strategy_name = strategy_name
        self.bot_config = bot_config
        self.db_client = db_client
        
        # Build config for components
        self.config = self._build_config(bot_config, global_config or {})
        
        # Initialize Bybit client with user's credentials
        self.bybit_client = BybitClient({
            'bybit': {
                'api_key': credentials['api_key'],
                'api_secret': credentials['api_secret'],
                'testnet': credentials.get('is_testnet', True)
            }
        })
        
        # State
        self.state = "INITIALIZED"
        self.is_running = False
        self.active_strategy = None
        self.day_sentiment = "Neutral"
        self.trades_count = 0
        self.total_pnl = 0.0
        self.last_error: Optional[str] = None
        self.last_heartbeat: Optional[datetime.datetime] = None
        self.last_processed_timestamp = None
        self.signal_cooldown: Optional[datetime.datetime] = None
        self.current_trade_id: Optional[str] = None  # Track DB trade ID for updates
        self._last_signal_data: Optional[Dict[str, Any]] = None  # Store last signal context
        
        # Components (initialized on start)
        self.order_agent: Optional[OrderExecutionAgent] = None
        self.position_agent: Optional[PositionManagementAgent] = None
        self.sentiment_agent: Optional[CryptoSentimentAgent] = None
        self.lstm_manager = None
        
        logger.info(f"[Bot:{self.bot_id[:8]}] Created instance for {symbol} with {strategy_name}")
    
    def _build_config(self, bot_config: Dict, global_config: Dict) -> Dict:
        """Build a unified config from bot and global settings."""
        # Default trading config
        trading = {
            'default_symbol': self.symbol,
            'symbols': [self.symbol],
            'default_leverage': bot_config.get('leverage', 5),
            'max_leverage': bot_config.get('leverage', 5),
            'risk_per_trade_percent': bot_config.get('risk_per_trade', 2.0),
            'max_position_percent': 10.0,
            'max_trades_per_day': bot_config.get('max_trades_per_day', 5),
            'stop_loss_percent': bot_config.get('stop_loss_percent', 2.0),
            'take_profit_percent': bot_config.get('take_profit_percent', 4.0),
            'use_trailing_stop': bot_config.get('use_trailing_stop', True),
            'trailing_stop_percent': bot_config.get('trailing_stop_percent', 1.5),
            'chart_timeframe': global_config.get('chart_timeframe', '15'),
            'analysis_lookback': global_config.get('analysis_lookback', 200),
            'signal_cooldown_minutes': global_config.get('signal_cooldown_minutes', 30),
        }
        
        trading_flags = {
            'paper_trading': bot_config.get('paper_trading', True),
            'auto_execute': True,
            'enable_sentiment_analysis': global_config.get('enable_sentiment_analysis', True),
            'enable_ai_strategy_selection': False,  # Strategy is fixed per bot
            'use_lstm_model': self.strategy_name == 'LSTM_Momentum',
            'enable_loss_analysis': False,  # Disable for lightweight operation
        }
        
        trailing_stop = {
            'type': 'PERCENTAGE' if bot_config.get('use_trailing_stop', True) else 'NONE',
            'percentage': bot_config.get('trailing_stop_percent', 1.5) * 10,  # Convert to % distance
            'use_indicator_exit': False,
        }
        
        ai = global_config.get('ai', {})
        sentiment = global_config.get('sentiment', {})
        
        return {
            'trading': trading,
            'trading_flags': trading_flags,
            'trailing_stop_loss': trailing_stop,
            'ai': ai,
            'sentiment': sentiment,
        }
    
    async def initialize(self) -> bool:
        """
        Initialize bot components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[Bot:{self.bot_id[:8]}] Initializing...")
            
            # Check Bybit connection
            if not self.bybit_client.authenticated:
                self.last_error = "Failed to authenticate with Bybit"
                logger.error(f"[Bot:{self.bot_id[:8]}] {self.last_error}")
                return False
            
            mode = self.bybit_client.get_mode()
            logger.info(f"[Bot:{self.bot_id[:8]}] Connected to Bybit ({mode})")
            
            # Initialize agents
            self.order_agent = OrderExecutionAgent(self.bybit_client, self.config)
            self.position_agent = PositionManagementAgent(self.bybit_client, self.config)
            self.sentiment_agent = CryptoSentimentAgent(self.config)
            
            # Initialize LSTM manager if needed
            if self.config['trading_flags'].get('use_lstm_model', False):
                self.lstm_manager = get_model_manager(self.config)
                logger.info(f"[Bot:{self.bot_id[:8]}] LSTM manager initialized")
            
            # Initialize strategy
            self.active_strategy = get_strategy(
                self.strategy_name,
                self.config,
                self.lstm_manager
            )
            
            if hasattr(self.active_strategy, 'set_lstm_manager') and self.lstm_manager:
                self.active_strategy.set_lstm_manager(self.lstm_manager, self.symbol)
            
            self.state = "READY"
            logger.info(f"[Bot:{self.bot_id[:8]}] Initialized successfully")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"[Bot:{self.bot_id[:8]}] Initialization failed: {e}", exc_info=True)
            return False
    
    async def run_loop(self, status_callback=None):
        """
        Main trading loop for this bot instance.
        
        Args:
            status_callback: Optional async callback(bot_id, status_dict) for status updates
        """
        self.is_running = True
        self.state = "RUNNING"
        logger.info(f"[Bot:{self.bot_id[:8]}] Starting trading loop for {self.symbol}")
        
        # Get initial sentiment (with timeout to prevent blocking)
        try:
            if self.config['trading_flags'].get('enable_sentiment_analysis', True):
                try:
                    self.day_sentiment = await asyncio.wait_for(
                        self.sentiment_agent.get_market_sentiment(self.symbol),
                        timeout=30.0  # 30 second timeout for sentiment
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"[Bot:{self.bot_id[:8]}] Sentiment analysis timed out, using default: Neutral")
                    self.day_sentiment = "Neutral"
            logger.info(f"[Bot:{self.bot_id[:8]}] Initial sentiment: {self.day_sentiment}")
        except Exception as e:
            logger.warning(f"[Bot:{self.bot_id[:8]}] Failed to get sentiment: {e}")
        
        loop_interval = 30  # seconds
        sentiment_refresh_interval = 3600  # 1 hour
        last_sentiment_check = datetime.datetime.now()
        
        while self.is_running:
            try:
                self.last_heartbeat = datetime.datetime.now()
                
                # Refresh sentiment periodically (with timeout)
                if (datetime.datetime.now() - last_sentiment_check).seconds >= sentiment_refresh_interval:
                    try:
                        if self.config['trading_flags'].get('enable_sentiment_analysis', True):
                            try:
                                self.day_sentiment = await asyncio.wait_for(
                                    self.sentiment_agent.get_market_sentiment(self.symbol),
                                    timeout=30.0
                                )
                            except asyncio.TimeoutError:
                                logger.warning(f"[Bot:{self.bot_id[:8]}] Sentiment refresh timed out")
                        last_sentiment_check = datetime.datetime.now()
                    except Exception as e:
                        logger.warning(f"[Bot:{self.bot_id[:8]}] Sentiment refresh failed: {e}")
                
                # Handle different states
                if self.state == "RUNNING":
                    # Check trade limits
                    max_trades = self.config['trading'].get('max_trades_per_day', 5)
                    if self.trades_count >= max_trades:
                        logger.debug(f"[Bot:{self.bot_id[:8]}] Max trades ({max_trades}) reached")
                        await asyncio.sleep(loop_interval * 10)
                        continue
                    
                    # Run trading cycle
                    signal = await self._run_trading_cycle()
                    
                    if signal in ['BUY', 'SELL'] and self._check_signal_cooldown():
                        await self._execute_trade(signal)
                
                elif self.state == "IN_POSITION":
                    await self._manage_position()
                
                # Send status update if callback provided
                if status_callback:
                    try:
                        await status_callback(self.bot_id, self.get_status())
                    except Exception as e:
                        logger.warning(f"[Bot:{self.bot_id[:8]}] Status callback failed: {e}")
                
                await asyncio.sleep(loop_interval)
                
            except asyncio.CancelledError:
                logger.info(f"[Bot:{self.bot_id[:8]}] Received cancellation signal")
                break
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"[Bot:{self.bot_id[:8]}] Error in trading loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retry
        
        # Cleanup
        await self.cleanup()
    
    async def _run_trading_cycle(self) -> Optional[str]:
        """Run a single trading cycle and return signal."""
        try:
            # Fetch market data
            df = await self.bybit_client.get_market_data(
                self.symbol,
                interval=self.config['trading'].get('chart_timeframe', '15'),
                limit=self.config['trading'].get('analysis_lookback', 200)
            )
            
            if df.empty:
                logger.warning(f"[Bot:{self.bot_id[:8]}] No market data available")
                return None
            
            # Calculate indicators
            df = calculate_all_indicators(df, self.config)
            
            # Check for new candle (but still analyze even if same candle - market changes!)
            latest_timestamp = df.index[-1]
            is_new_candle = not self.last_processed_timestamp or latest_timestamp > self.last_processed_timestamp
            
            if is_new_candle:
                self.last_processed_timestamp = latest_timestamp
                logger.info(f"[Bot:{self.bot_id[:8]}] New candle: {latest_timestamp}")
            
            # Get funding rate for funding rate strategy
            funding_rate = None
            if self.strategy_name == "Funding_Rate":
                funding = await self.bybit_client.get_funding_rate(self.symbol)
                funding_rate = funding.get('fundingRate')
            
            # Generate signal (now returns tuple: signal, reason, context)
            signal_result = self.active_strategy.generate_signals(
                df,
                sentiment=self.day_sentiment,
                funding_rate=funding_rate,
                symbol=self.symbol
            )
            
            # Handle tuple return (signal, reason, context)
            if isinstance(signal_result, tuple) and len(signal_result) == 3:
                signal, signal_reason, signal_context = signal_result
            else:
                # Backward compatibility: if strategy returns just a string
                signal = signal_result if isinstance(signal_result, str) else 'HOLD'
                signal_reason = f"Signal from {self.strategy_name}"
                signal_context = {}
            
            # Enhanced logging for debugging
            current = df.iloc[-1]
            current_price = current['close']
            rsi = current.get('rsi', 0)
            ema9 = current.get('ema_9', 0)
            ema21 = current.get('ema_21', 0)
            
            # Store signal context for later use in trade execution
            self._last_signal_data = {
                'signal': signal,
                'reason': signal_reason,
                'context': signal_context,
                'price': float(current_price),
                'rsi': float(rsi),
                'ema9': float(ema9),
                'ema21': float(ema21),
                'sentiment': self.day_sentiment,
                'funding_rate': float(funding_rate) if funding_rate else None,
                'timestamp': datetime.datetime.now().isoformat(),
            }
            
            if signal in ['BUY', 'SELL']:
                logger.info(
                    f"[Bot:{self.bot_id[:8]}] 🎯 SIGNAL: {signal} | "
                    f"${current_price:.2f} | RSI={rsi:.1f} | "
                    f"EMA9={ema9:.2f} EMA21={ema21:.2f} | "
                    f"Sentiment={self.day_sentiment} | Reason: {signal_reason}"
                )
            else:
                # Log current market state every new candle for debugging
                if is_new_candle:
                    trend = "📈 Bullish" if ema9 > ema21 else "📉 Bearish"
                    funding_str = f" | Funding={funding_rate:.4%}" if funding_rate else ""
                    logger.info(
                        f"[Bot:{self.bot_id[:8]}] Market: ${current_price:.2f} | {trend} | "
                        f"RSI={rsi:.1f} | Sentiment={self.day_sentiment}{funding_str} | Signal=HOLD"
                    )
            
            return signal
            
        except Exception as e:
            logger.error(f"[Bot:{self.bot_id[:8]}] Trading cycle error: {e}", exc_info=True)
            return None
    
    async def _execute_trade(self, signal: str):
        """Execute a trade based on signal."""
        try:
            is_paper = self.config['trading_flags'].get('paper_trading', True)
            logger.info(f"[Bot:{self.bot_id[:8]}] Executing {signal} signal...")
            
            if is_paper:
                trade_details = await self.order_agent.get_paper_trade_details(
                    signal, self.symbol
                )
            else:
                trade_details = await self.order_agent.place_trade(
                    signal, self.symbol
                )
            
            if trade_details:
                trade_details['Strategy'] = self.strategy_name
                trade_details['paper_trade'] = is_paper
                self.position_agent.start_trade(trade_details)
                self.trades_count += 1
                self._update_signal_cooldown()
                self.state = "IN_POSITION"
                logger.info(f"[Bot:{self.bot_id[:8]}] Trade opened: {signal} {self.symbol}")
                
                # Save trade to database
                trade_id = None
                if self.db_client:
                    try:
                        trade_id = await self.db_client.record_open_trade(
                            tenant_id=self.tenant_id,
                            bot_id=self.bot_id,
                            trade_data=trade_details
                        )
                        if trade_id:
                            self.current_trade_id = trade_id
                            logger.info(f"[Bot:{self.bot_id[:8]}] Trade saved to database: {trade_id}")
                    except Exception as db_err:
                        logger.error(f"[Bot:{self.bot_id[:8]}] Failed to save trade to DB: {db_err}")
                
                # Record signal log with full context
                if self.db_client and self._last_signal_data:
                    try:
                        # Build comprehensive market data from signal context
                        market_data = {
                            **self._last_signal_data.get('context', {}),
                            'price': self._last_signal_data.get('price'),
                            'rsi': self._last_signal_data.get('rsi'),
                            'ema_9': self._last_signal_data.get('ema9'),
                            'ema_21': self._last_signal_data.get('ema21'),
                        }
                        
                        await self.db_client.record_signal_log(
                            tenant_id=self.tenant_id,
                            bot_id=self.bot_id,
                            signal=signal,
                            strategy=self.strategy_name,
                            symbol=self.symbol,
                            signal_reason=self._last_signal_data.get('reason', 'Signal triggered'),
                            market_data=market_data,
                            sentiment=self._last_signal_data.get('sentiment'),
                            funding_rate=self._last_signal_data.get('funding_rate'),
                            trade_id=trade_id
                        )
                        logger.info(f"[Bot:{self.bot_id[:8]}] Signal log recorded for trade {trade_id}")
                    except Exception as sig_err:
                        logger.error(f"[Bot:{self.bot_id[:8]}] Failed to record signal log: {sig_err}")
                
                # Enhance trade metadata with signal context
                if self._last_signal_data:
                    trade_details['signal_reason'] = self._last_signal_data.get('reason')
                    trade_details['signal_context'] = self._last_signal_data.get('context', {})
            else:
                logger.warning(f"[Bot:{self.bot_id[:8]}] Failed to execute trade")
                
        except Exception as e:
            logger.error(f"[Bot:{self.bot_id[:8]}] Trade execution error: {e}", exc_info=True)
    
    async def _manage_position(self):
        """Manage active position."""
        try:
            is_paper = self.config['trading_flags'].get('paper_trading', True)
            
            # Get market data for position management
            df = await self.bybit_client.get_market_data(
                self.symbol,
                interval=self.config['trading'].get('chart_timeframe', '15'),
                limit=50
            )
            df = calculate_all_indicators(df, self.config)
            
            # Manage position
            status = await self.position_agent.manage(
                is_paper_trade=is_paper,
                underlying_hist_df=df
            )
            
            if status and status != "ACTIVE":
                # Trade closed
                pnl = status.get('ProfitLoss', 0)
                self.total_pnl += pnl
                self.state = "RUNNING"
                logger.info(f"[Bot:{self.bot_id[:8]}] Position closed. P&L: ${pnl:.2f}")
                
                # Update trade in database
                if self.db_client and self.current_trade_id:
                    try:
                        await self.db_client.close_trade(
                            trade_id=self.current_trade_id,
                            exit_data=status
                        )
                        logger.info(f"[Bot:{self.bot_id[:8]}] Trade {self.current_trade_id} closed in database")
                        self.current_trade_id = None
                    except Exception as db_err:
                        logger.error(f"[Bot:{self.bot_id[:8]}] Failed to update trade in DB: {db_err}")
                
        except Exception as e:
            logger.error(f"[Bot:{self.bot_id[:8]}] Position management error: {e}", exc_info=True)
    
    def _check_signal_cooldown(self) -> bool:
        """Check if signal cooldown has passed."""
        if self.signal_cooldown is None:
            return True
        
        cooldown_minutes = self.config['trading'].get('signal_cooldown_minutes', 30)
        elapsed = (datetime.datetime.now() - self.signal_cooldown).total_seconds() / 60
        return elapsed >= cooldown_minutes
    
    def _update_signal_cooldown(self):
        """Update signal cooldown timestamp."""
        self.signal_cooldown = datetime.datetime.now()
    
    async def stop(self):
        """Stop the bot gracefully."""
        logger.info(f"[Bot:{self.bot_id[:8]}] Stopping...")
        self.is_running = False
        self.state = "STOPPING"
    
    async def cleanup(self):
        """Cleanup resources when bot stops."""
        logger.info(f"[Bot:{self.bot_id[:8]}] Cleaning up...")
        self.state = "STOPPED"
        self.is_running = False
        
        # Close any open positions if configured
        # For now, we leave positions open - they have SL/TP set
        logger.info(f"[Bot:{self.bot_id[:8]}] Cleanup complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        return {
            'bot_id': self.bot_id,
            'tenant_id': self.tenant_id,
            'name': self.bot_name,
            'symbol': self.symbol,
            'strategy': self.strategy_name,
            'state': self.state,
            'is_running': self.is_running,
            'trades_count': self.trades_count,
            'total_pnl': self.total_pnl,
            'sentiment': self.day_sentiment,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'last_error': self.last_error,
            'paper_trading': self.config['trading_flags'].get('paper_trading', True),
        }
    
    def reset_daily_counters(self):
        """Reset daily counters (called at midnight UTC)."""
        self.trades_count = 0
        logger.info(f"[Bot:{self.bot_id[:8]}] Daily counters reset")

