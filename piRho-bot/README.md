# piRho Crypto Trading Bot

**Bybit USDT Perpetual Futures Trading Bot with AI Strategy Selection**

A sophisticated 24/7 cryptocurrency trading bot that combines:
- LSTM neural network for price prediction
- AI-powered strategy selection (OpenAI)
- Multiple technical analysis strategies
- Market sentiment analysis (Fear & Greed, CryptoPanic, News)
- Interactive Telegram bot interface
- Comprehensive risk management

## Features

### Trading Capabilities
- **24/7 Automated Trading** - No market hours restrictions
- **USDT Perpetual Futures** - Leveraged trading up to 100x
- **Multi-Symbol Support** - Trade BTC, ETH, SOL, and more
- **Paper Trading Mode** - Test strategies without real funds

### AI & Strategy
- **11 Trading Strategies** including:
  - LSTM Momentum (ML-based)
  - Supertrend + MACD
  - Bollinger Band Squeeze
  - RSI Divergence
  - EMA Crossovers
  - Volume Spread Analysis
  - Funding Rate Strategy (crypto-specific)
- **AI Strategy Selection** - OpenAI recommends optimal strategy
- **Sentiment Analysis** - Fear & Greed Index, news analysis

### Risk Management
- Configurable stop-loss and take-profit
- Trailing stop-loss (percentage-based)
- Position size based on risk percentage
- Maximum trades per day limit
- Liquidation monitoring

### Telegram Interface
- Real-time price alerts
- Interactive trade execution
- Position monitoring
- Performance statistics

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Bybit account (mainnet or testnet)
- Telegram bot token (optional)
- OpenAI API key (optional)

### 2. Installation

```bash
# Clone or navigate to the project
cd piRho-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy the example environment file and fill in your credentials:

```bash
cp env.example.txt .env
```

Edit `.env` with your credentials:

```env
# Bybit API (get from bybit.com or testnet.bybit.com)
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret

# Telegram (optional - create via @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# OpenAI (optional - for AI strategy selection)
OPENAI_API_KEY=your_openai_api_key
```

Review `config.yaml` for trading parameters:
- Trading symbols
- Leverage settings
- Risk percentage
- Strategy settings

### 4. Test Connection

```bash
python main.py --test
```

This will verify:
- Bybit API connection
- Wallet balance
- Sentiment analysis
- LSTM model (if present)

### 5. Run the Bot

**Full automated trading:**
```bash
python main.py
```

**Telegram bot only (manual trading):**
```bash
python main.py --telegram
```

**Debug mode:**
```bash
python main.py --debug
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     main.py (Entry Point)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────┐   │
│  │  trading_bot.py │    │      telegram_bot.py        │   │
│  │  (Orchestrator) │◄───│   (Interactive Interface)   │   │
│  └────────┬────────┘    └─────────────────────────────┘   │
│           │                                                 │
│  ┌────────┴────────────────────────────────────────────┐   │
│  │                    Core Components                   │   │
│  ├──────────────┬───────────────┬─────────────────────┤   │
│  │ bybit_client │   agents.py   │ strategy_factory.py │   │
│  │   (API)      │ (Order/Pos)   │   (11 Strategies)   │   │
│  └──────────────┴───────────────┴─────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │                   AI Layer                          │    │
│  ├──────────────────┬─────────────────────────────────┤    │
│  │ langgraph_agent  │      sentiment_agent.py         │    │
│  │ (Strategy AI)    │  (Fear&Greed, News, Crypto)     │    │
│  └──────────────────┴─────────────────────────────────┘    │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │               Support Modules                       │    │
│  ├─────────────┬─────────────┬────────────────────────┤    │
│  │ indicators  │  reporting  │      config.yaml       │    │
│  └─────────────┴─────────────┴────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Trading Strategies

| Strategy | Type | Description |
|----------|------|-------------|
| LSTM_Momentum | ML | Neural network prediction with technical confirmation |
| Supertrend_MACD | Trend | Supertrend direction + MACD crossover |
| EMA_Cross_RSI | Momentum | EMA 9/15 crossover with RSI confirmation |
| MA_Crossover | Trend | Simple 9/21 EMA crossover |
| BB_Squeeze_Breakout | Volatility | Bollinger Band squeeze breakouts |
| Volatility_Cluster_Reversal | Reversal | High volatility exhaustion moves |
| Volume_Spread_Analysis | Smart Money | VSA for institutional activity |
| RSI_Divergence | Reversal | RSI divergence patterns |
| Reversal_Detector | Reversal | Overextended trend reversals |
| Momentum_VWAP_RSI | Intraday | VWAP + RSI alignment |
| Funding_Rate | Crypto | Extreme funding rate contrarian |

## Configuration Reference

### config.yaml

```yaml
bybit:
  testnet: true  # Use testnet for paper trading

trading:
  symbols: ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
  default_leverage: 5
  risk_per_trade_percent: 2.0
  stop_loss_percent: 2.0
  take_profit_percent: 4.0
  max_trades_per_day: 5

trading_flags:
  paper_trading: true
  auto_execute: false
  use_lstm_model: true
  enable_sentiment_analysis: true
  enable_ai_strategy_selection: true
```

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Show bot status and commands |
| `/price [symbol]` | Get current price |
| `/trade` | Start interactive trade |
| `/position` | View open positions |
| `/close` | Close current position |
| `/balance` | Check wallet balance |
| `/sentiment` | Market sentiment analysis |
| `/performance` | Trading statistics |
| `/strategies` | List available strategies |

## Risk Warning

⚠️ **Trading cryptocurrency futures involves substantial risk of loss.**

- This bot is for educational and research purposes
- Always start with paper trading (testnet)
- Never risk more than you can afford to lose
- Past performance does not guarantee future results
- The developers are not responsible for any financial losses

## Troubleshooting

### Common Issues

**"Bybit client not authenticated"**
- Check your API key and secret in `.env`
- Ensure API key has trading permissions
- For testnet, get keys from testnet.bybit.com

**"LSTM model not found"**
- The LSTM model is optional
- Train a model or disable with `use_lstm_model: false`

**"Rate limit exceeded"**
- The bot has built-in rate limiting
- Reduce `analysis_lookback` in config if needed

**Import errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Some indicators require pandas-ta which is included

## Deployment

### Koyeb (Recommended)

See the main [KOYEB_DEPLOYMENT.md](../KOYEB_DEPLOYMENT.md) guide for detailed instructions.

Quick steps:
1. Push your code to GitHub/GitLab
2. Create a new **Worker Service** in Koyeb dashboard
3. Select your repository and set root directory to `piRho-bot`
4. Configure start command: `python main.py --orchestrator`
5. Set all environment variables from `env.example.txt`
6. Allocate at least 2GB RAM and 2 vCPU for ML workloads
7. Deploy!

**Note**: The bot runs as a background worker (not an HTTP service), so configure it as a **Worker Service** type in Koyeb.

## Development

### Project Structure

```
piRho-bot/
├── main.py                 # Entry point
├── trading_bot.py          # Main orchestrator
├── telegram_bot.py         # Telegram interface
├── bybit_client.py         # Bybit API wrapper
├── agents.py               # Order & position management
├── strategy_factory.py     # Trading strategies
├── indicators.py           # Technical indicators
├── sentiment_agent.py      # Sentiment analysis
├── langgraph_agent.py      # AI strategy selection
├── reporting.py            # Trade logging
├── config.yaml             # Configuration
├── requirements.txt        # Dependencies
└── README.md              # This file
```

### Adding a New Strategy

1. Create a class in `strategy_factory.py` extending `BaseStrategy`
2. Implement `generate_signals()` method
3. Add to the strategy dictionary in `get_strategy()`
4. Update `get_available_strategies()`

## License

This project is for educational purposes. Use at your own risk.

## Credits

- Bybit API via [pybit](https://github.com/bybit-exchange/pybit)
- Technical analysis via [pandas-ta](https://github.com/twopirllc/pandas-ta)
- AI via [OpenAI](https://platform.openai.com/)
- Telegram bot via [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
