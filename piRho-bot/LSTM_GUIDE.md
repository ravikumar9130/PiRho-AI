# 🧠 LSTM Model Guide - How to Run

This guide explains how to train and use the enhanced LSTM models in the piRho trading bot.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Automatic Training](#automatic-training)
3. [Manual Training](#manual-training)
4. [Running the Bot with LSTM](#running-the-bot-with-lstm)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Option 1: Automatic Training (Recommended)

The bot will automatically train models when needed if enabled in config:

1. **Enable auto-training** in `config.yaml`:
```yaml
ai:
  lstm_auto_train: true  # Set to true
```

2. **Start the bot**:
```bash
python trading_bot.py
```

3. **The bot will**:
   - Check if a model exists for the current symbol
   - If missing, automatically fetch data and train
   - Use the trained model for predictions

### Option 2: Manual Training

Train models before starting the bot:

```bash
python train_lstm_enhanced.py
```

This will train models for BTCUSDT, ETHUSDT, and SOLUSDT.

---

## 🤖 Automatic Training

### How It Works

When the bot starts and selects the `LSTM_Momentum` strategy:

1. Checks if model exists for the current symbol
2. If missing and `lstm_auto_train: true`:
   - Fetches 500 candles of historical data
   - Trains the model (takes 5-15 minutes)
   - Saves to `models/lstm_{SYMBOL}.pt`
3. Uses the model for predictions

### Configuration

In `config.yaml`:
```yaml
ai:
  lstm_auto_train: true        # Enable/disable auto-training
  lstm_train_epochs: 100       # Training epochs (more = better but slower)
  lstm_sequence_length: 30    # Input sequence length
  lstm_confidence_threshold: 0.65  # Signal confidence threshold
```

---

## 🛠️ Manual Training

### Using the Enhanced Training Script

```bash
python train_lstm_enhanced.py
```

### Customize Training

Edit `train_lstm_enhanced.py`:

```python
# Configuration
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]  # Symbols to train
days = 60      # Days of historical data
interval = "15"  # Timeframe: 1, 3, 5, 15, 30, 60, 240, D
epochs = 100   # Training epochs (None = use config default)
```

### Training a Single Symbol

```python
import asyncio
from train_lstm_enhanced import train_symbol_model

asyncio.run(train_symbol_model("BTCUSDT", days=60, epochs=100))
```

### Training via Python Script

```python
import asyncio
from bybit_client import BybitClient
from lstm_predictor import get_model_manager
from trading_bot import load_config

async def train_custom():
    config = load_config()
    client = BybitClient(config)
    manager = get_model_manager(config)
    
    # Fetch data
    df = await client.get_market_data("BTCUSDT", interval="15", limit=500)
    
    # Train
    success = await manager.train_model("BTCUSDT", df, epochs=100)
    print(f"Training {'successful' if success else 'failed'}")

asyncio.run(train_custom())
```

---

## 🎯 Running the Bot with LSTM

### Step 1: Ensure Models Exist

**Option A**: Let auto-training handle it (set `lstm_auto_train: true`)

**Option B**: Train manually first:
```bash
python train_lstm_enhanced.py
```

### Step 2: Configure the Bot

In `config.yaml`:
```yaml
trading_flags:
  use_lstm_model: true  # Enable LSTM

ai:
  lstm_auto_train: true
  lstm_confidence_threshold: 0.65
```

### Step 3: Start the Bot

```bash
python trading_bot.py
```

Or:
```bash
python main.py
```

### Step 4: Strategy Selection

The bot will automatically select `LSTM_Momentum` if:
- `use_lstm_model: true`
- Model exists or auto-training succeeds

Or manually force it by setting in `config.yaml`:
```yaml
trading_flags:
  enable_ai_strategy_selection: false  # Disable AI selection
```

Then the bot defaults to LSTM_Momentum if available.

---

## ⚙️ Configuration

### LSTM Settings in `config.yaml`

```yaml
ai:
  # LSTM Model Configuration
  lstm_sequence_length: 30      # Input sequence length (20-60 recommended)
  lstm_confidence_threshold: 0.65  # Signal threshold (0.0-1.0)
  lstm_auto_train: true         # Auto-train missing models
  lstm_train_epochs: 100        # Training epochs
```

### Model Storage

- **Location**: `models/` directory
- **Format**: `models/lstm_{SYMBOL}.pt`
- **Normalization**: `models/lstm_{SYMBOL}_norm.json`

Example:
- `models/lstm_BTCUSDT.pt`
- `models/lstm_ETHUSDT.pt`
- `models/lstm_SOLUSDT.pt`

---

## 🔍 Troubleshooting

### Issue: "PyTorch not installed"

**Solution**:
```bash
pip install torch
```

### Issue: "No LSTM model found"

**Solutions**:
1. Enable auto-training: `lstm_auto_train: true`
2. Train manually: `python train_lstm_enhanced.py`
3. Check model exists: `ls models/lstm_*.pt`

### Issue: "Not enough data for training"

**Solutions**:
- Increase `days` parameter (try 60-90 days)
- Use a longer timeframe (e.g., "60" instead of "15")
- Check API connection

### Issue: Training is slow

**Solutions**:
- Reduce `lstm_train_epochs` (try 50-100)
- Use GPU if available (PyTorch will auto-detect)
- Reduce `days` of historical data

### Issue: Model predictions seem wrong

**Solutions**:
- Retrain with more data: increase `days` to 90-120
- Increase training epochs: `lstm_train_epochs: 150`
- Adjust confidence threshold: `lstm_confidence_threshold: 0.70`

### Issue: Auto-training fails

**Check**:
1. API credentials are set (`.env` file)
2. Internet connection
3. Bybit API is accessible
4. Sufficient data available (need 200+ candles)

---

## 📊 Model Features

The enhanced LSTM model includes:

- **12 Technical Indicators**: RSI, MACD, EMA, Bollinger Bands, ATR, etc.
- **Attention Mechanism**: Focuses on important patterns
- **Direction + Magnitude**: Predicts both direction and price change %
- **Per-Symbol Models**: Each symbol has its own optimized model
- **Auto-Normalization**: Features are automatically normalized

---

## 🎓 Best Practices

1. **Training Data**: Use 60-90 days of data for best results
2. **Timeframe**: 15-minute candles work well for most symbols
3. **Epochs**: 100 epochs is a good balance (more = better but slower)
4. **Retraining**: Retrain models monthly or when market conditions change
5. **Multiple Symbols**: Train separate models for each symbol you trade

---

## 📝 Example Workflow

```bash
# 1. Train models for your symbols
python train_lstm_enhanced.py

# 2. Verify models were created
ls models/lstm_*.pt

# 3. Start the bot
python trading_bot.py

# 4. Bot will use LSTM_Momentum strategy automatically
# 5. Check logs for LSTM predictions
```

---

## 🔗 Related Files

- `lstm_predictor.py` - LSTM model manager and architecture
- `strategy_factory.py` - LSTM_Momentum strategy implementation
- `trading_bot.py` - Bot integration
- `train_lstm_enhanced.py` - Training script
- `config.yaml` - Configuration

---

## 💡 Tips

- **Start with BTCUSDT**: It has the most data and best patterns
- **Monitor Training**: Watch the validation accuracy during training
- **Test Different Timeframes**: 15m, 30m, 60m can give different results
- **Combine with Sentiment**: LSTM works best with sentiment analysis enabled
- **Paper Trade First**: Test the strategy before going live

---

For more help, check the main README.md or open an issue.

