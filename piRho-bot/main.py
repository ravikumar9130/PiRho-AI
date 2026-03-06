#!/usr/bin/env python3
"""
piRho Crypto Trading Bot - Main Entry Point
Bybit USDT Perpetual Futures Trading with AI Strategy Selection

This bot provides:
- 24/7 automated crypto trading on Bybit perpetual futures
- AI-powered strategy selection using OpenAI
- LSTM neural network for price prediction
- Market sentiment analysis (Fear & Greed, CryptoPanic, News)
- Interactive Telegram bot interface
- Multiple trading strategies (trend following, reversal, momentum)
- Comprehensive risk management with trailing stops
- Multi-user multi-bot orchestration for SaaS deployment

Usage:
    python main.py                 # Run single trading bot (legacy mode)
    python main.py --orchestrator  # Run multi-bot orchestrator (SaaS mode)
    python main.py --telegram      # Run with Telegram bot only
    python main.py --test          # Run connectivity tests
"""

import argparse
import asyncio
import logging
import logging.handlers
import os
import sys
import io
from datetime import datetime
from typing import Optional

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    torch = None
    nn = None
    HAS_TORCH = False

from dotenv import load_dotenv

# Ensure proper UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="ignore")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="ignore")

# Load environment variables
load_dotenv()


# =============================
# LOGGER SETUP
# =============================

def setup_logging(log_file: str = "tradingbot.log", level: int = logging.INFO):
    """Configure logging for the application."""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    fh = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    fh.setLevel(level)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


# =============================
# LSTM MODEL
# =============================

if HAS_TORCH:
    class LSTMModel(nn.Module):
        """LSTM model for price prediction."""
        
        def __init__(self, input_size=4, hidden_size=64, num_layers=2, output_size=1):
            super(LSTMModel, self).__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, output_size)
        
        def forward(self, x):
            h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
            c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
            out, _ = self.lstm(x, (h0, c0))
            out = self.fc(out[:, -1, :])
            return out
else:
    LSTMModel = None


def load_lstm_model(model_path: str) -> Optional[object]:
    """Load the LSTM model for price prediction."""
    if not HAS_TORCH:
        logging.warning("PyTorch not installed - LSTM model not available")
        return None
    
    try:
        if not os.path.exists(model_path):
            logging.warning(f"LSTM model not found at {model_path}")
            return None
        
        model_data = torch.load(model_path, map_location=torch.device('cpu'))
        
        if isinstance(model_data, dict):
            model = LSTMModel()
            model.load_state_dict(model_data)
        else:
            model = model_data
        
        model.eval()
        logging.info(f"✅ LSTM model loaded from {model_path}")
        return model
        
    except Exception as e:
        logging.error(f"Failed to load LSTM model: {e}")
        return None


# =============================
# MAIN TRADING BOT
# =============================

async def run_trading_bot():
    """Run the main trading bot with all components."""
    from trading_bot import CryptoTradingBot, load_config
    from telegram_bot import TelegramTradingBot
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting piRho Crypto Trading Bot")
    
    # Load configuration
    config = load_config()
    
    # Create trading bot
    bot = CryptoTradingBot(config)
    
    # Initialize
    if not await bot.initialize():
        logger.error("❌ Failed to initialize trading bot")
        return
    
    # Create Telegram bot
    telegram_config = config.get('telegram', {})
    if telegram_config.get('bot_token'):
        telegram_bot = TelegramTradingBot(config)
        telegram_bot.set_components(
            bybit_client=bot.bybit_client,
            order_agent=bot.order_agent,
            position_agent=bot.position_agent,
            sentiment_agent=bot.sentiment_agent,
            langgraph_agent=bot.langgraph_agent
        )
        
        # Start Telegram bot
        await telegram_bot.start()
        logger.info("✅ Telegram bot started")
    else:
        telegram_bot = None
        logger.warning("⚠ Telegram bot not configured")
    
    try:
        # Run trading bot
        await bot.run()
    except KeyboardInterrupt:
        logger.info("⏹ Shutting down...")
    finally:
        if telegram_bot:
            await telegram_bot.stop()


async def run_telegram_only():
    """Run only the Telegram bot for manual trading."""
    from trading_bot import load_config
    from telegram_bot import TelegramTradingBot
    from bybit_client import BybitClient
    from agents import OrderExecutionAgent, PositionManagementAgent
    from sentiment_agent import CryptoSentimentAgent
    from langgraph_agent import LangGraphAgent
    
    logger = logging.getLogger(__name__)
    logger.info("🤖 Starting Telegram Trading Bot")
    
    # Load configuration
    config = load_config()
    
    # Initialize components
    bybit_client = BybitClient(config)
    order_agent = OrderExecutionAgent(bybit_client, config)
    position_agent = PositionManagementAgent(bybit_client, config)
    sentiment_agent = CryptoSentimentAgent(config)
    langgraph_agent = LangGraphAgent(config)
    
    # Create Telegram bot
    telegram_bot = TelegramTradingBot(config)
    telegram_bot.set_components(
        bybit_client=bybit_client,
        order_agent=order_agent,
        position_agent=position_agent,
        sentiment_agent=sentiment_agent,
        langgraph_agent=langgraph_agent
    )
    
    try:
        await telegram_bot.start()
        logger.info("✅ Telegram bot is running. Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("⏹ Shutting down...")
    finally:
        await telegram_bot.stop()


async def run_orchestrator():
    """Run the multi-bot orchestrator for SaaS mode."""
    from orchestrator import BotOrchestrator
    import signal
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Multi-Bot Orchestrator...")
    
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
        if not shutdown_called:
            shutdown_called = True
            await orchestrator.shutdown()
    except Exception as e:
        logger.exception(f"Orchestrator crashed: {e}")
        if not shutdown_called:
            shutdown_called = True
            await orchestrator.shutdown()
        raise


async def run_tests():
    """Run connectivity and component tests."""
    from trading_bot import load_config
    from bybit_client import BybitClient
    from sentiment_agent import CryptoSentimentAgent
    
    logger = logging.getLogger(__name__)
    logger.info("🧪 Running connectivity tests...")
    
    config = load_config()
    results = []
    
    # Test Bybit connection
    print("\n📊 Testing Bybit connection...")
    try:
        client = BybitClient(config)
        if client.authenticated:
            balance = await client.get_wallet_balance()
            print(f"  ✅ Bybit connected ({client.get_mode()})")
            print(f"  💰 Balance: ${balance.get('walletBalance', 0):.2f} USDT")
            results.append(("Bybit", True))
        else:
            print(f"  ⚠ Bybit connected (read-only mode)")
            results.append(("Bybit", True))
        
        # Test market data
        ticker = await client.get_ticker("BTCUSDT")
        if ticker:
            print(f"  📈 BTC Price: ${ticker.get('lastPrice', 0):.2f}")
        
    except Exception as e:
        print(f"  ❌ Bybit connection failed: {e}")
        results.append(("Bybit", False))
    
    # Test Sentiment
    print("\n📰 Testing sentiment analysis...")
    try:
        sentiment_agent = CryptoSentimentAgent(config)
        sentiment = await sentiment_agent.get_market_sentiment()
        print(f"  ✅ Sentiment: {sentiment}")
        results.append(("Sentiment", True))
    except Exception as e:
        print(f"  ❌ Sentiment analysis failed: {e}")
        results.append(("Sentiment", False))
    
    # Test LSTM model
    print("\n🧠 Testing LSTM model...")
    model_path = config.get('ai', {}).get('lstm_model_path', 'price_predictor.pt')
    model = load_lstm_model(model_path)
    if model:
        print(f"  ✅ LSTM model loaded")
        results.append(("LSTM", True))
    else:
        print(f"  ⚠ LSTM model not found (optional)")
        results.append(("LSTM", None))
    
    # Test Database connection (for orchestrator)
    print("\n🗄️ Testing database connection...")
    try:
        from db_client import get_db_client
        db = get_db_client()
        bots = await db.get_all_bot_statuses()
        print(f"  ✅ Database connected ({len(bots)} bots in system)")
        results.append(("Database", True))
    except Exception as e:
        print(f"  ⚠ Database not configured: {e}")
        results.append(("Database", None))
    
    # Summary
    print("\n" + "=" * 40)
    print("📋 Test Summary")
    print("=" * 40)
    
    for name, status in results:
        if status is True:
            print(f"  ✅ {name}: Passed")
        elif status is False:
            print(f"  ❌ {name}: Failed")
        else:
            print(f"  ⚠ {name}: Skipped")
    
    passed = sum(1 for _, s in results if s is True)
    total = sum(1 for _, s in results if s is not None)
    print(f"\n  {passed}/{total} tests passed")


# =============================
# ENTRY POINT
# =============================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="piRho Crypto Trading Bot - Bybit Perpetual Futures"
    )
    parser.add_argument(
        "--orchestrator",
        action="store_true",
        help="Run multi-bot orchestrator (SaaS mode)"
    )
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Run Telegram bot only (no automated trading)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run connectivity tests"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    log_file = "orchestrator.log" if args.orchestrator else "tradingbot.log"
    setup_logging(log_file=log_file, level=log_level)
    
    logger = logging.getLogger(__name__)
    
    # Print banner
    if args.orchestrator:
        print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🚀 piRho Multi-Bot Orchestrator                        ║
║   SaaS Mode - Managing Multiple Trading Bots             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
    else:
        print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🚀 piRho Crypto Trading Bot                            ║
║   Bybit USDT Perpetual Futures                           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
    
    try:
        if args.test:
            asyncio.run(run_tests())
        elif args.orchestrator:
            asyncio.run(run_orchestrator())
        elif args.telegram:
            asyncio.run(run_telegram_only())
        else:
            asyncio.run(run_trading_bot())
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
