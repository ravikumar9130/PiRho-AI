#!/usr/bin/env python3
"""
LSTM Model Training Script for piRho Trading Bot
Trains a simple LSTM model for price prediction using historical data from Bybit
"""

import logging
import os
import sys
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    HAS_TORCH = True
except ImportError:
    print("❌ PyTorch not installed. Install with: pip install torch")
    sys.exit(1)

from dotenv import load_dotenv
from bybit_client import BybitClient
from trading_bot import load_config

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PriceDataset(Dataset):
    """Dataset for price prediction."""
    
    def __init__(self, data, sequence_length=20):
        self.data = data
        self.sequence_length = sequence_length
    
    def __len__(self):
        return len(self.data) - self.sequence_length
    
    def __getitem__(self, idx):
        sequence = self.data[idx:idx + self.sequence_length]
        target = self.data[idx + self.sequence_length]
        return torch.FloatTensor(sequence), torch.FloatTensor([target])


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


def normalize_data(data):
    """Normalize data to 0-1 range."""
    data_min = data.min(axis=0)
    data_max = data.max(axis=0)
    normalized = (data - data_min) / (data_max - data_min + 1e-8)
    return normalized, data_min, data_max


def denormalize_data(normalized, data_min, data_max):
    """Denormalize data back to original scale."""
    return normalized * (data_max - data_min) + data_min


async def fetch_training_data(symbol="BTCUSDT", days=30, interval="15"):
    """
    Fetch historical data for training.
    
    Args:
        symbol: Trading symbol
        days: Number of days of historical data
        interval: Timeframe (1, 3, 5, 15, 30, 60, 240, D)
    
    Returns:
        DataFrame with OHLCV data
    """
    logger.info(f"📊 Fetching {days} days of {symbol} data...")
    
    config = load_config()
    client = BybitClient(config)
    
    # Calculate start time
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    all_data = []
    current_time = start_time
    
    # Fetch data in chunks (Bybit API limit)
    while current_time < end_time:
        try:
            df = await client.get_market_data(
                symbol=symbol,
                interval=interval,
                limit=200,  # Max per request
                start_time=int(current_time.timestamp() * 1000) if current_time > start_time else None
            )
            
            if df.empty:
                break
            
            all_data.append(df)
            current_time = df.index[-1].to_pydatetime() + timedelta(minutes=int(interval))
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            break
    
    if not all_data:
        raise ValueError("No data fetched")
    
    combined_df = pd.concat(all_data).drop_duplicates().sort_index()
    logger.info(f"✅ Fetched {len(combined_df)} candles")
    
    return combined_df


def prepare_features(df):
    """
    Prepare features for LSTM training.
    
    Args:
        df: DataFrame with OHLCV data
    
    Returns:
        Normalized feature array and normalization parameters
    """
    # Use OHLC as features
    features = df[['open', 'high', 'low', 'close']].values
    
    # Normalize
    normalized, data_min, data_max = normalize_data(features)
    
    return normalized, data_min, data_max


def train_model(model, train_loader, epochs=50, learning_rate=0.001):
    """
    Train the LSTM model.
    
    Args:
        model: LSTM model
        train_loader: DataLoader with training data
        epochs: Number of training epochs
        learning_rate: Learning rate
    
    Returns:
        Trained model
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    logger.info(f"🚀 Training on {device} for {epochs} epochs...")
    
    for epoch in range(epochs):
        total_loss = 0
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)
            
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        if (epoch + 1) % 10 == 0:
            avg_loss = total_loss / len(train_loader)
            logger.info(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.6f}")
    
    logger.info("✅ Training complete")
    return model


async def main():
    """Main training function."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🧠 LSTM Model Training for piRho Bot                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    symbol = "BTCUSDT"
    days = 30
    interval = "15"
    sequence_length = 20
    epochs = 50
    batch_size = 32
    model_path = "price_predictor.pt"
    
    try:
        # Fetch data
        df = await fetch_training_data(symbol, days, interval)
        
        if len(df) < sequence_length + 100:
            logger.error(f"❌ Not enough data. Need at least {sequence_length + 100} candles, got {len(df)}")
            return
        
        # Prepare features
        logger.info("📐 Preparing features...")
        features, data_min, data_max = prepare_features(df)
        
        # Create dataset
        dataset = PriceDataset(features, sequence_length)
        train_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        logger.info(f"📦 Dataset size: {len(dataset)} sequences")
        
        # Create model
        model = LSTMModel(input_size=4, hidden_size=64, num_layers=2, output_size=1)
        logger.info(f"🏗️  Model created: {sum(p.numel() for p in model.parameters())} parameters")
        
        # Train model
        trained_model = train_model(model, train_loader, epochs=epochs)
        
        # Save model
        torch.save(trained_model.state_dict(), model_path)
        logger.info(f"💾 Model saved to {model_path}")
        
        # Save normalization parameters (optional, for future use)
        norm_params = {
            'data_min': data_min.tolist(),
            'data_max': data_max.tolist()
        }
        import json
        with open('lstm_norm_params.json', 'w') as f:
            json.dump(norm_params, f)
        
        print(f"\n✅ Success! Model trained and saved to {model_path}")
        print(f"📊 Training data: {len(df)} candles from {symbol}")
        print(f"🎯 You can now use LSTM_Momentum strategy in the bot\n")
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

