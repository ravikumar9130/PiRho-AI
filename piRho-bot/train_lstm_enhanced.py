#!/usr/bin/env python3
"""
Enhanced LSTM Model Training Script for piRho Trading Bot
Trains per-symbol LSTM models using the enhanced LSTMModelManager
Supports multiple symbols and uses advanced features with attention mechanism
"""

import logging
import sys
import asyncio
from datetime import datetime, timedelta

try:
    import torch
    HAS_TORCH = True
except ImportError:
    print("❌ PyTorch not installed. Install with: pip install torch")
    sys.exit(1)

from dotenv import load_dotenv
from bybit_client import BybitClient
from trading_bot import load_config
from lstm_predictor import get_model_manager

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fetch_training_data(client: BybitClient, symbol: str, days: int = 60, interval: str = "15"):
    """
    Fetch historical data for training.
    
    Args:
        client: BybitClient instance
        symbol: Trading symbol (e.g., "BTCUSDT")
        days: Number of days of historical data
        interval: Timeframe (1, 3, 5, 15, 30, 60, 240, D)
    
    Returns:
        DataFrame with OHLCV data
    """
    logger.info(f"📊 Fetching {days} days of {symbol} data (interval: {interval})...")
    
    # Calculate start time
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    all_data = []
    current_time = start_time
    
    # Fetch data in chunks (Bybit API limit is 200 per request)
    max_limit = 200
    limit = min(max_limit, days * 24 * (60 // int(interval)) if interval.isdigit() else max_limit)
    
    try:
        # Try to get all data at once first
        df = await client.get_market_data(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        
        if not df.empty:
            all_data.append(df)
            logger.info(f"✅ Fetched {len(df)} candles in one request")
        
        # If we need more data, fetch in chunks
        if len(df) < limit and days > 7:
            logger.info("📥 Fetching additional historical data...")
            while current_time < end_time and len(all_data) < 10:  # Limit to 10 requests
                try:
                    chunk_df = await client.get_market_data(
                        symbol=symbol,
                        interval=interval,
                        limit=limit,
                        start_time=int(current_time.timestamp() * 1000) if current_time > start_time else None
                    )
                    
                    if chunk_df.empty:
                        break
                    
                    all_data.append(chunk_df)
                    current_time = chunk_df.index[-1].to_pydatetime() + timedelta(minutes=int(interval))
                    
                    await asyncio.sleep(0.5)  # Rate limit
                    
                except Exception as e:
                    logger.warning(f"Error fetching chunk: {e}")
                    break
    
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return None
    
    if not all_data:
        logger.error("No data fetched")
        return None
    
    import pandas as pd
    combined_df = pd.concat(all_data).drop_duplicates().sort_index()
    logger.info(f"✅ Total candles fetched: {len(combined_df)}")
    
    return combined_df


async def train_symbol_model(
    symbol: str,
    days: int = 60,
    interval: str = "15",
    epochs: int = None
):
    """
    Train an LSTM model for a specific symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT", "ETHUSDT")
        days: Number of days of historical data to use
        interval: Timeframe for candles
        epochs: Number of training epochs (uses config default if None)
    """
    print(f"\n{'='*60}")
    print(f"🧠 Training LSTM Model for {symbol}")
    print(f"{'='*60}\n")
    
    try:
        # Load config
        config = load_config()
        
        # Initialize client
        client = BybitClient(config)
        
        # Get LSTM manager
        lstm_manager = get_model_manager(config)
        
        # Check if model already exists
        if lstm_manager.model_exists(symbol):
            logger.info(f"⚠️  Model for {symbol} already exists!")
            response = input(f"Do you want to retrain? (y/n): ").strip().lower()
            if response != 'y':
                logger.info("Skipping training.")
                return
        
        # Fetch training data
        df = await fetch_training_data(client, symbol, days, interval)
        
        if df is None or df.empty:
            logger.error(f"❌ Failed to fetch data for {symbol}")
            return
        
        if len(df) < 200:
            logger.error(f"❌ Not enough data. Got {len(df)} candles, need at least 200")
            return
        
        logger.info(f"📊 Training with {len(df)} candles")
        
        # Train model
        success = await lstm_manager.train_model(
            symbol=symbol,
            df=df,
            epochs=epochs
        )
        
        if success:
            logger.info(f"✅ Successfully trained model for {symbol}")
            logger.info(f"💾 Model saved to: {lstm_manager.get_model_path(symbol)}")
        else:
            logger.error(f"❌ Training failed for {symbol}")
    
    except Exception as e:
        logger.error(f"❌ Error training {symbol}: {e}", exc_info=True)


async def main():
    """Main training function."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🧠 Enhanced LSTM Model Training for piRho Bot         ║
║   Per-Symbol Models with Attention Mechanism             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Configuration - Edit these values
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]  # Symbols to train
    days = 60  # Days of historical data (more = better but slower)
    interval = "15"  # Timeframe: 1, 3, 5, 15, 30, 60, 240, D
    epochs = None  # None = use config default (100), or set a number
    
    print(f"📋 Configuration:")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Historical data: {days} days")
    print(f"   Timeframe: {interval} minutes")
    print(f"   Epochs: {epochs or 'config default'}")
    print()
    
    # Train models for each symbol
    for symbol in symbols:
        await train_symbol_model(
            symbol=symbol,
            days=days,
            interval=interval,
            epochs=epochs
        )
        print()  # Blank line between symbols
    
    print("\n✅ Training complete!")
    print("\n💡 Tips:")
    print("   - Models are saved in the 'models/' directory")
    print("   - Format: models/lstm_{SYMBOL}.pt")
    print("   - The bot will auto-train missing models if enabled in config")
    print("   - Use LSTM_Momentum strategy in the bot to use these models\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹ Training interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)

