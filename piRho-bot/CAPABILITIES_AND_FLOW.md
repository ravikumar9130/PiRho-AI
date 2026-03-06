# piRho Bot - Capabilities, Automation & Flow Guide

## 🎯 Capabilities Overview

### 1. **Automated Trading System**
✅ **YES, this is a fully automated trading bot** that can run 24/7 without manual intervention.

**Key Features:**
- **24/7 Automated Trading** - Runs continuously, monitoring markets and executing trades
- **Paper Trading Mode** - Test strategies safely on Bybit testnet without real money
- **Live Trading Mode** - Execute real trades on Bybit mainnet (when enabled)
- **Multi-Symbol Support** - Trade BTC, ETH, SOL, and other USDT perpetual futures
- **Leveraged Trading** - Supports up to 100x leverage (configurable, default: 5x)

### 2. **AI-Powered Strategy Selection**
- **OpenAI Integration** - AI analyzes market conditions and recommends optimal strategy
- **11 Trading Strategies** available:
  - LSTM_Momentum (Machine Learning-based)
  - Supertrend_MACD (Trend following)
  - EMA_Cross_RSI (Momentum)
  - MA_Crossover (Simple trend)
  - BB_Squeeze_Breakout (Volatility)
  - Volatility_Cluster_Reversal (Reversal)
  - Volume_Spread_Analysis (Smart money)
  - RSI_Divergence (Reversal)
  - Reversal_Detector (Reversal)
  - Momentum_VWAP_RSI (Intraday)
  - Funding_Rate (Crypto-specific)

### 3. **Market Sentiment Analysis**
- **Fear & Greed Index** - Crypto market sentiment indicator
- **News Analysis** - Analyzes crypto news for sentiment
- **CryptoPanic Integration** - Crypto-specific news aggregation
- **Real-time Sentiment** - Updates throughout the day

### 4. **Risk Management**
- **Stop Loss** - Configurable percentage-based stop loss (default: 2%)
- **Take Profit** - Configurable take profit targets (default: 4%)
- **Trailing Stop Loss** - Automatically adjusts stop loss as price moves favorably
- **Position Sizing** - Risk-based position sizing (default: 2% risk per trade)
- **Daily Trade Limits** - Maximum trades per day (default: 5)
- **Liquidation Monitoring** - Tracks position health

### 5. **Telegram Bot Interface**
- **Real-time Alerts** - Price updates and trade notifications
- **Interactive Trading** - Manual trade execution via Telegram
- **Position Monitoring** - View open positions
- **Performance Stats** - Trading statistics and reports
- **Commands Available:**
  - `/start` - Bot status
  - `/price [symbol]` - Get current price
  - `/trade` - Start interactive trade
  - `/position` - View open positions
  - `/close` - Close current position
  - `/balance` - Check wallet balance
  - `/sentiment` - Market sentiment
  - `/performance` - Trading statistics
  - `/strategies` - List strategies

### 6. **Trade Logging & Reporting**
- **Excel Trade Log** - All trades logged to `trade_log.xlsx`
- **Daily Reports** - Automatic daily performance summaries
- **Monthly Reports** - Monthly trading statistics
- **Strategy Performance** - Breakdown by strategy
- **Performance Metrics** - Win rate, profit factor, drawdown, etc.

---

## 🤖 Is This Automated Trading?

**YES!** The bot operates in three modes:

### Mode 1: Full Automated Trading
```bash
python main.py
```
- Bot runs 24/7
- Automatically analyzes market conditions
- AI selects optimal strategy
- Executes trades automatically (if `auto_execute: true` in config)
- Manages positions with stop loss/take profit
- Logs all trades

### Mode 2: Paper Trading (Recommended for Testing)
```bash
python main.py
# With paper_trading: true in config.yaml
```
- Same automation as live trading
- Uses Bybit testnet (fake money)
- Perfect for testing strategies safely
- All features work except real money

### Mode 3: Telegram-Only (Manual Trading)
```bash
python main.py --telegram
```
- Bot runs but doesn't auto-trade
- You execute trades manually via Telegram
- Good for learning and manual control

---

## 📊 How to See Backtest Results / Trade History

### ⚠️ Important Note:
The current `backtester.py` file is for a different trading system (Zerodha/NSE stocks). The crypto bot doesn't have a built-in backtesting feature yet, but you can analyze your **actual trade history** from live/paper trading.

### Method 1: View Trade Log Excel File
```bash
# Open the trade log file
open trade_log.xlsx  # Mac
# or
start trade_log.xlsx  # Windows
```

**The Excel file contains:**
- All executed trades
- Entry/exit prices
- Profit/loss
- Strategy used
- Timestamps
- Exit reasons

### Method 2: Use Python to Analyze Trade History
```python
from reporting import get_trade_history, calculate_performance_metrics

# Get last 30 days of trades
trades_df = get_trade_history(days=30)

# Calculate performance metrics
metrics = calculate_performance_metrics(trades_df)

print(f"Total Trades: {metrics['total_trades']}")
print(f"Win Rate: {metrics['win_rate']:.2f}%")
print(f"Total P&L: ${metrics['total_pnl']:.2f}")
print(f"Profit Factor: {metrics['profit_factor']:.2f}")
```

### Method 3: Check Performance via Telegram
```
/performance
```
Shows trading statistics directly in Telegram.

### Method 4: View Logs
```bash
# View the trading bot log
tail -f tradingbot.log

# Or open in text editor
cat tradingbot.log
```

---

## 🔄 Full Trading Flow Explained

### **Phase 1: Initialization**
```
1. Bot starts → Loads config.yaml
2. Connects to Bybit API (testnet or mainnet)
3. Initializes components:
   - BybitClient (API connection)
   - OrderExecutionAgent (order placement)
   - PositionManagementAgent (position tracking)
   - SentimentAgent (market sentiment)
   - LangGraphAgent (AI strategy selection)
   - LSTM Model (if available)
4. Checks wallet balance
5. Initializes trade log file
```

### **Phase 2: Strategy Selection (Every 4 Hours)**
```
1. Get Market Sentiment:
   - Fetch Fear & Greed Index
   - Analyze crypto news
   - Determine overall sentiment (Bullish/Bearish/Neutral)

2. Analyze Market Conditions:
   - Fetch recent price data (200 candles)
   - Calculate technical indicators (RSI, EMA, ATR, etc.)
   - Determine trend (Bullish/Bearish/Neutral)
   - Assess volatility (High/Normal/Low)
   - Check funding rates

3. AI Strategy Selection:
   - Send market conditions to OpenAI
   - AI analyzes and recommends best strategy
   - Bot selects recommended strategy
   - Example: "In high volatility, use BB_Squeeze_Breakout"

4. Initialize Strategy:
   - Load selected strategy class
   - Set up strategy parameters
   - Ready to generate signals
```

### **Phase 3: Signal Generation (Every 30 Seconds)**
```
1. Fetch Market Data:
   - Get latest candles (15-min timeframe by default)
   - Calculate all technical indicators
   - Check for new candle (avoid duplicate signals)

2. Generate Signal:
   - Strategy analyzes current market state
   - Considers sentiment, indicators, patterns
   - Returns: "BUY", "SELL", or "HOLD"

3. Signal Validation:
   - Check cooldown period (30 min default)
   - Verify trade limits (max 5 trades/day)
   - Validate market conditions

4. If Signal = BUY/SELL:
   - Log signal detection
   - Proceed to trade execution
```

### **Phase 4: Trade Execution**
```
1. Calculate Position Size:
   - Get wallet balance
   - Calculate risk amount (2% of balance default)
   - Determine position size based on stop loss
   - Apply leverage (5x default)

2. Place Order:
   - Paper Trading: Simulate order, log details
   - Live Trading: Place actual order on Bybit
   - Set stop loss and take profit orders

3. Start Position Management:
   - Track entry price
   - Monitor position in real-time
   - Update bot state to "IN_POSITION"
```

### **Phase 5: Position Management (Continuous)**
```
1. Monitor Position:
   - Check current price vs entry price
   - Calculate unrealized P&L
   - Update trailing stop loss (if enabled)

2. Exit Conditions Check:
   - Stop Loss Hit → Close position
   - Take Profit Hit → Close position
   - Trailing Stop Triggered → Close position
   - Strategy Signal Reversal → Close position

3. Position Closed:
   - Calculate final P&L
   - Log trade to Excel file
   - If losing trade: AI analyzes why
   - Reset bot state to "AWAITING_SIGNAL"
```

### **Phase 6: Daily Reporting**
```
1. At End of Day:
   - Generate daily summary
   - Calculate metrics:
     * Total trades
     * Win rate
     * Total P&L
     * Best/worst trades
   - Log to Excel summary sheet
   - Send report (if Telegram configured)
```

### **Visual Flow Diagram:**
```
┌─────────────────────────────────────────────────────────┐
│                    BOT STARTUP                          │
│  • Load config.yaml                                     │
│  • Connect to Bybit API                                │
│  • Initialize all agents                               │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              STRATEGY SELECTION (Every 4h)              │
│  • Get market sentiment                                │
│  • Analyze market conditions                            │
│  • AI recommends strategy                               │
│  • Initialize strategy                                 │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           SIGNAL GENERATION (Every 30s)                 │
│  • Fetch market data                                    │
│  • Calculate indicators                                 │
│  • Strategy generates signal                            │
│  • Validate signal                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    Signal=HOLD      Signal=BUY/SELL
         │                   │
         │                   ▼
         │         ┌─────────────────────┐
         │         │  TRADE EXECUTION    │
         │         │  • Calculate size   │
         │         │  • Place order      │
         │         │  • Set stop/target  │
         │         └──────────┬──────────┘
         │                   │
         │                   ▼
         │         ┌─────────────────────┐
         │         │ POSITION MANAGEMENT  │
         │         │  • Monitor price    │
         │         │  • Update stops     │
         │         │  • Check exits      │
         │         └──────────┬──────────┘
         │                   │
         │         ┌─────────┴─────────┐
         │         │                   │
         │    Position Closed    Position Active
         │         │                   │
         │         ▼                   │
         │  ┌──────────────┐           │
         │  │ LOG TRADE    │           │
         │  │ • Calculate  │           │
         │  │   P&L       │◄──────────┘
         │  │ • Save Excel│
         │  └──────────────┘
         │
         └─────────────────────────────┐
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │  AWAIT NEXT SIGNAL   │
                            └──────────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Setup Configuration
Edit `config.yaml`:
```yaml
trading_flags:
  paper_trading: true  # Start with paper trading!
  auto_execute: false  # Set to true for full automation
```

### 2. Set Environment Variables
Create `.env` file:
```env
BYBIT_API_KEY=your_testnet_key
BYBIT_API_SECRET=your_testnet_secret
TELEGRAM_BOT_TOKEN=your_token  # Optional
OPENAI_API_KEY=your_key  # Optional
```

### 3. Test Connection
```bash
python main.py --test
```

### 4. Run Bot
```bash
# Full automated trading
python main.py

# Telegram only
python main.py --telegram

# Debug mode
python main.py --debug
```

### 5. View Results
- Check `trade_log.xlsx` for all trades
- View `tradingbot.log` for detailed logs
- Use Telegram `/performance` command

---

## 📈 Performance Analysis

The bot automatically tracks:
- **Win Rate** - Percentage of profitable trades
- **Profit Factor** - Gross profit / Gross loss
- **Total P&L** - Net profit/loss
- **Average P&L** - Average per trade
- **Max Drawdown** - Largest peak-to-trough decline
- **Best/Worst Trade** - Individual trade extremes
- **Strategy Performance** - Breakdown by strategy

---

## ⚠️ Important Notes

1. **Start with Paper Trading** - Always test on testnet first
2. **Backtesting Not Available** - The bot doesn't have historical backtesting yet, only live/paper trading results
3. **Risk Management** - Never risk more than you can afford to lose
4. **API Keys** - Keep your API keys secure, never commit them to git
5. **Monitoring** - Monitor the bot regularly, especially when starting

---

## 🔧 Future Enhancements

Potential improvements:
- Add historical backtesting for crypto strategies
- Multi-timeframe analysis
- Portfolio management across multiple symbols
- Advanced risk metrics
- Strategy optimization tools

---

For more details, see `README.md` or check the code documentation.

