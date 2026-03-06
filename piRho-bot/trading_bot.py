"""
Bybit USDT Perpetual Futures Trading Bot Orchestrator
24/7 automated trading with AI strategy selection and sentiment analysis
"""

import logging
import yaml
import os
import asyncio
import datetime
import pandas as pd

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    torch = None
    nn = None
    HAS_TORCH = False

from typing import Optional, Dict, Any
from dotenv import load_dotenv

from bybit_client import BybitClient
from agents import OrderExecutionAgent, PositionManagementAgent
from sentiment_agent import CryptoSentimentAgent
from langgraph_agent import LangGraphAgent
from strategy_factory import get_strategy, get_available_strategies
from indicators import calculate_all_indicators
from reporting import send_daily_report, initialize_trade_log, log_trade
from lstm_predictor import get_model_manager

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load configuration from YAML file and environment variables."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables
    bybit = config.get('bybit', {})
    bybit['api_key'] = os.getenv('BYBIT_API_KEY', bybit.get('api_key', ''))
    bybit['api_secret'] = os.getenv('BYBIT_API_SECRET', bybit.get('api_secret', ''))
    bybit['testnet'] = os.getenv('BYBIT_TESTNET', str(bybit.get('testnet', True))).lower() == 'true'
    config['bybit'] = bybit
    
    telegram = config.get('telegram', {})
    telegram['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN', telegram.get('bot_token', ''))
    telegram['chat_id'] = os.getenv('TELEGRAM_CHAT_ID', telegram.get('chat_id', ''))
    config['telegram'] = telegram
    
    ai = config.get('ai', {})
    ai['openai_api_key'] = os.getenv('OPENAI_API_KEY', ai.get('openai_api_key', ''))
    config['ai'] = ai
    
    sentiment = config.get('sentiment', {})
    sentiment['news_api_key'] = os.getenv('NEWS_API_KEY', sentiment.get('news_api_key', ''))
    sentiment['cryptopanic_api_key'] = os.getenv('CRYPTOPANIC_API_KEY', sentiment.get('cryptopanic_api_key', ''))
    config['sentiment'] = sentiment
    
    return config


# LSTM model loading is now handled by LSTMModelManager in lstm_predictor.py


class CryptoTradingBot:
    """
    Main trading bot orchestrator for Bybit perpetual futures.
    Handles 24/7 trading with AI strategy selection.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the trading bot.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.trading_config = config.get('trading', {})
        self.flags = config.get('trading_flags', {})
        
        # State
        self.bot_state = "STARTING"
        self.active_strategy_name = "None"
        self.active_strategy = None
        self.day_sentiment = "Neutral"
        self.trades_today_count = 0
        self.last_processed_timestamp = None
        self.last_strategy_assessment = None
        self.signal_cooldowns: Dict[str, datetime.datetime] = {}
        
        # Components (initialized in setup)
        self.bybit_client: Optional[BybitClient] = None
        self.order_agent: Optional[OrderExecutionAgent] = None
        self.position_agent: Optional[PositionManagementAgent] = None
        self.sentiment_agent: Optional[CryptoSentimentAgent] = None
        self.langgraph_agent: Optional[LangGraphAgent] = None
        self.lstm_manager = None  # LSTMModelManager instance
        
        # Trading symbols
        self.symbols = self.trading_config.get('symbols', ['BTCUSDT'])
        self.current_symbol = self.trading_config.get('default_symbol', 'BTCUSDT')
    
    async def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("🚀 Initializing Crypto Trading Bot...")
        
        try:
            # Initialize Bybit client
            self.bybit_client = BybitClient(self.config)
            
            if not self.bybit_client.authenticated:
                logger.warning("⚠ Bybit client not authenticated - running in read-only mode")
            else:
                mode = self.bybit_client.get_mode()
                logger.info(f"✅ Connected to Bybit ({mode})")
            
            # Initialize agents
            self.order_agent = OrderExecutionAgent(self.bybit_client, self.config)
            self.position_agent = PositionManagementAgent(self.bybit_client, self.config)
            self.sentiment_agent = CryptoSentimentAgent(self.config)
            self.langgraph_agent = LangGraphAgent(self.config)
            
            # Initialize LSTM model manager if enabled
            if self.flags.get('use_lstm_model', True):
                self.lstm_manager = get_model_manager(self.config)
                logger.info("✅ LSTM Model Manager initialized (supports per-symbol models)")
            else:
                logger.info("LSTM model disabled in config")
            
            # Initialize trade log
            initialize_trade_log()
            
            self.bot_state = "INITIALIZED"
            logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}", exc_info=True)
            return False
    
    async def setup_trading_session(self) -> bool:
        """
        Set up a new trading session with strategy selection.
        
        Returns:
            True if successful, False otherwise
        """
        self.bot_state = "SETUP"
        logger.info("--- Starting Trading Session Setup ---")
        
        try:
            # Get market sentiment
            if self.flags.get('enable_sentiment_analysis', True):
                self.day_sentiment = await self.sentiment_agent.get_market_sentiment(self.current_symbol)
            else:
                self.day_sentiment = "Neutral"
            
            logger.info(f"📊 Market Sentiment: {self.day_sentiment}")
            
            # Get market conditions
            market_conditions = await self._get_market_conditions()
            
            # Select strategy using AI
            if self.flags.get('enable_ai_strategy_selection', True):
                self.active_strategy_name = await self.langgraph_agent.get_recommended_strategy(
                    market_conditions=market_conditions,
                    sentiment=self.day_sentiment,
                    symbol=self.current_symbol
                )
            else:
                # Default to LSTM_Momentum if manager available, otherwise use Supertrend_MACD
                if self.lstm_manager is not None:
                    self.active_strategy_name = "LSTM_Momentum"
                else:
                    self.active_strategy_name = "Supertrend_MACD"
                    logger.info("Using Supertrend_MACD as default (LSTM manager not available)")
            
            # Initialize strategy
            self.active_strategy = get_strategy(
                self.active_strategy_name,
                self.config,
                self.lstm_manager
            )
            
            # Set LSTM manager and symbol if applicable
            if hasattr(self.active_strategy, 'set_lstm_manager'):
                self.active_strategy.set_lstm_manager(self.lstm_manager, self.current_symbol)
            
            # Auto-train model if it doesn't exist and auto-train is enabled
            if (self.active_strategy_name == "LSTM_Momentum" and 
                self.lstm_manager is not None and 
                self.lstm_manager.auto_train):
                if not self.lstm_manager.model_exists(self.current_symbol):
                    logger.info(f"🤖 Auto-training LSTM model for {self.current_symbol}...")
                    # Fetch historical data for training
                    df = await self.bybit_client.get_market_data(
                        self.current_symbol,
                        interval=self.trading_config.get('chart_timeframe', '15'),
                        limit=500  # Get enough data for training
                    )
                    if not df.empty and len(df) >= 200:
                        success = await self.lstm_manager.train_model(
                            self.current_symbol,
                            df,
                            epochs=self.lstm_manager.train_epochs
                        )
                        if success:
                            logger.info(f"✅ Auto-trained LSTM model for {self.current_symbol}")
                        else:
                            logger.warning(f"⚠️ Auto-training failed for {self.current_symbol}")
                    else:
                        logger.warning(f"⚠️ Not enough data to auto-train model for {self.current_symbol}")
            
            self.last_strategy_assessment = datetime.datetime.now()
            
            self.bot_state = "AWAITING_SIGNAL"
            logger.info(f"✅ Setup complete. Active strategy: {self.active_strategy_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}", exc_info=True)
            return False
    
    async def _get_market_conditions(self) -> Dict[str, Any]:
        """Get current market conditions for strategy selection."""
        conditions = {}
        
        try:
            # Get recent price data
            df = await self.bybit_client.get_market_data(
                self.current_symbol,
                interval=self.trading_config.get('chart_timeframe', '15'),
                limit=100
            )
            
            if df.empty:
                return conditions
            
            df = calculate_all_indicators(df, self.config)
            current = df.iloc[-1]
            
            # Trend
            if current.get('ema_50', 0) > current.get('ema_200', 0):
                conditions['trend'] = 'Bullish'
            elif current.get('ema_50', 0) < current.get('ema_200', 0):
                conditions['trend'] = 'Bearish'
            else:
                conditions['trend'] = 'Neutral'
            
            # Volatility
            atr = current.get('atr', 0)
            atr_ma = current.get('atr_ma', atr)
            if atr > atr_ma * 1.5:
                conditions['volatility'] = 'High'
            elif atr < atr_ma * 0.5:
                conditions['volatility'] = 'Low'
            else:
                conditions['volatility'] = 'Normal'
            
            # RSI condition
            rsi = current.get('rsi', 50)
            if rsi > 70:
                conditions['rsi_state'] = 'Overbought'
            elif rsi < 30:
                conditions['rsi_state'] = 'Oversold'
            else:
                conditions['rsi_state'] = 'Neutral'
            
            # Supertrend
            st_dir = current.get('supertrend_direction', 0)
            conditions['supertrend'] = 'Bullish' if st_dir == 1 else 'Bearish'
            
            # Funding rate
            funding = await self.bybit_client.get_funding_rate(self.current_symbol)
            funding_rate = funding.get('fundingRate', 0)
            if abs(funding_rate) > 0.0005:
                conditions['funding'] = 'Extreme' if funding_rate > 0 else 'Negative Extreme'
            else:
                conditions['funding'] = 'Normal'
            
        except Exception as e:
            logger.warning(f"Error getting market conditions: {e}")
        
        return conditions
    
    async def run_trading_cycle(self) -> Optional[str]:
        """
        Run a single trading cycle.
        
        Returns:
            Signal ("BUY", "SELL", "HOLD") or None if error
        """
        try:
            # Fetch market data
            df = await self.bybit_client.get_market_data(
                self.current_symbol,
                interval=self.trading_config.get('chart_timeframe', '15'),
                limit=self.trading_config.get('analysis_lookback', 200)
            )
            
            if df.empty:
                logger.warning("No market data available")
                return None
            
            # Calculate indicators
            df = calculate_all_indicators(df, self.config)
            
            # Check for new candle
            latest_timestamp = df.index[-1]
            if self.last_processed_timestamp and latest_timestamp <= self.last_processed_timestamp:
                return "HOLD"  # Same candle, no action needed
            
            self.last_processed_timestamp = latest_timestamp
            
            # Get funding rate for funding rate strategy
            funding_rate = None
            if self.active_strategy_name == "Funding_Rate":
                funding = await self.bybit_client.get_funding_rate(self.current_symbol)
                funding_rate = funding.get('fundingRate')
            
            # Generate signal (pass symbol for LSTM strategies)
            signal = self.active_strategy.generate_signals(
                df,
                sentiment=self.day_sentiment,
                funding_rate=funding_rate,
                symbol=self.current_symbol
            )
            
            # Log status
            status_msg = self.active_strategy.get_status_message(
                df, 
                self.day_sentiment, 
                symbol=self.current_symbol
            )
            logger.debug(status_msg)
            
            current_price = df['close'].iloc[-1]
            logger.info(f"📊 {self.current_symbol}: ${current_price:.2f} | Signal: {signal} | Sentiment: {self.day_sentiment}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)
            return None
    
    def _check_signal_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in signal cooldown period."""
        if symbol not in self.signal_cooldowns:
            return True
        
        cooldown_minutes = self.trading_config.get('signal_cooldown_minutes', 30)
        last_signal = self.signal_cooldowns[symbol]
        elapsed = (datetime.datetime.now() - last_signal).total_seconds() / 60
        
        return elapsed >= cooldown_minutes
    
    def _update_signal_cooldown(self, symbol: str):
        """Update signal cooldown timestamp."""
        self.signal_cooldowns[symbol] = datetime.datetime.now()
    
    async def run(self):
        """
        Main trading loop - runs 24/7.
        """
        logger.info("🤖 Starting Crypto Trading Bot...")
        
        # Initialize
        if not await self.initialize():
            logger.error("Failed to initialize bot")
            return
        
        # Setup trading session
        if not await self.setup_trading_session():
            logger.error("Failed to setup trading session")
            return
        
        is_paper = self.flags.get('paper_trading', True)
        mode_str = "PAPER TRADING" if is_paper else "LIVE TRADING"
        logger.info(f"🎯 Bot running in {mode_str} mode")
        
        # Get initial balance
        balance = await self.bybit_client.get_wallet_balance()
        starting_balance = balance.get('walletBalance', 0)
        logger.info(f"💰 Starting balance: ${starting_balance:.2f} USDT")
        
        # Main loop
        loop_interval = 30  # seconds
        reassess_hours = self.trading_config.get('strategy_reassessment_hours', 4)
        
        while True:
            try:
                # Check for strategy reassessment
                if self.last_strategy_assessment:
                    elapsed = (datetime.datetime.now() - self.last_strategy_assessment).total_seconds() / 3600
                    if elapsed >= reassess_hours:
                        logger.info(f"🔄 Reassessing strategy after {reassess_hours} hours...")
                        await self.setup_trading_session()
                
                # Handle different states
                if self.bot_state == "AWAITING_SIGNAL":
                    # Check trade limits
                    max_trades = self.trading_config.get('max_trades_per_day', 5)
                    if self.trades_today_count >= max_trades:
                        logger.info(f"Max trades ({max_trades}) reached for today")
                        await asyncio.sleep(loop_interval * 10)
                        continue
                    
                    # Run trading cycle
                    signal = await self.run_trading_cycle()
                    
                    if signal in ['BUY', 'SELL'] and self._check_signal_cooldown(self.current_symbol):
                        logger.info(f"🎯 Signal detected: {signal}")
                        
                        # Execute trade
                        if is_paper:
                            trade_details = await self.order_agent.get_paper_trade_details(
                                signal, self.current_symbol
                            )
                        else:
                            trade_details = await self.order_agent.place_trade(
                                signal, self.current_symbol
                            )
                        
                        if trade_details:
                            trade_details['Strategy'] = self.active_strategy_name
                            self.position_agent.start_trade(trade_details)
                            self.trades_today_count += 1
                            self._update_signal_cooldown(self.current_symbol)
                            self.bot_state = "IN_POSITION"
                            
                            logger.info(f"✅ Trade opened: {signal} {self.current_symbol}")
                
                elif self.bot_state == "IN_POSITION":
                    # Get market data for position management
                    df = await self.bybit_client.get_market_data(
                        self.current_symbol,
                        interval=self.trading_config.get('chart_timeframe', '15'),
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
                        log_trade(status)
                        
                        # Analyze losing trade
                        if status.get('ProfitLoss', 0) < 0 and self.flags.get('enable_loss_analysis', True):
                            analysis = await self.langgraph_agent.analyze_trade_loss(status)
                            logger.info(f"📝 Loss Analysis: {analysis}")
                        
                        self.bot_state = "AWAITING_SIGNAL"
                        logger.info("🔄 Returning to signal awaiting state")
                
                # Reset daily counter at midnight UTC
                now = datetime.datetime.utcnow()
                if now.hour == 0 and now.minute < 1:
                    self.trades_today_count = 0
                
                await asyncio.sleep(loop_interval)
                
            except KeyboardInterrupt:
                logger.info("⏹ Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(60)
        
        # Cleanup
        logger.info("🔚 Trading bot shutdown complete")


async def main():
    """Main entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                'tradingbot.log',
                maxBytes=2_000_000,
                backupCount=3
            )
        ]
    )
    
    # Load configuration
    config = load_config()
    
    # Create and run bot
    bot = CryptoTradingBot(config)
    await bot.run()


if __name__ == "__main__":
    import logging.handlers
    asyncio.run(main())
