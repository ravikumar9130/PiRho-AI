"""Backtesting-related Pydantic models."""
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from enum import Enum


class TimeframeEnum(str, Enum):
    """Supported timeframes for backtesting."""
    M1 = "1"
    M3 = "3"
    M5 = "5"
    M15 = "15"
    M30 = "30"
    H1 = "60"
    H2 = "120"
    H4 = "240"
    H6 = "360"
    H12 = "720"
    D1 = "D"
    W1 = "W"


class IndicatorConfig(BaseModel):
    """Configuration for a single indicator."""
    enabled: bool = True
    # RSI
    rsi_period: int = Field(default=14, ge=2, le=100)
    rsi_overbought: float = Field(default=70, ge=50, le=100)
    rsi_oversold: float = Field(default=30, ge=0, le=50)
    # MACD
    macd_fast: int = Field(default=12, ge=2, le=50)
    macd_slow: int = Field(default=26, ge=5, le=100)
    macd_signal: int = Field(default=9, ge=2, le=50)
    # EMA
    ema_short: int = Field(default=9, ge=2, le=50)
    ema_medium: int = Field(default=21, ge=5, le=100)
    ema_long: int = Field(default=50, ge=10, le=200)
    ema_trend: int = Field(default=200, ge=50, le=500)
    # Bollinger Bands
    bb_period: int = Field(default=20, ge=5, le=100)
    bb_std_dev: float = Field(default=2.0, ge=0.5, le=4.0)
    # ATR
    atr_period: int = Field(default=14, ge=2, le=50)
    # Supertrend
    supertrend_period: int = Field(default=10, ge=5, le=50)
    supertrend_multiplier: float = Field(default=3.0, ge=1.0, le=10.0)
    # VWAP
    vwap_enabled: bool = True


class BacktestConfig(BaseModel):
    """Configuration for backtest execution."""
    initial_capital: float = Field(default=10000, ge=100, le=10000000)
    leverage: int = Field(default=1, ge=1, le=100)
    risk_per_trade: float = Field(default=2.0, ge=0.1, le=20.0)
    stop_loss_percent: float = Field(default=2.0, ge=0.1, le=50.0)
    take_profit_percent: float = Field(default=4.0, ge=0.1, le=100.0)
    use_trailing_stop: bool = False
    trailing_stop_percent: float = Field(default=1.5, ge=0.1, le=10.0)
    slippage_percent: float = Field(default=0.1, ge=0, le=2.0)
    commission_percent: float = Field(default=0.06, ge=0, le=1.0)
    max_trades_per_day: Optional[int] = Field(default=None, ge=1, le=100)


class BacktestRequest(BaseModel):
    """Request model for running a backtest."""
    symbol: str = Field(..., pattern=r"^[A-Z]+USDT$")
    start_date: datetime
    end_date: datetime
    strategy: str
    timeframe: TimeframeEnum = TimeframeEnum.M15
    indicators: IndicatorConfig = IndicatorConfig()
    config: BacktestConfig = BacktestConfig()
    save_result: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTCUSDT",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
                "strategy": "MA_Crossover",
                "timeframe": "15",
                "save_result": True
            }
        }


class TradeDetail(BaseModel):
    """Details of a single trade in backtest results."""
    trade_id: int
    entry_time: datetime
    exit_time: datetime
    side: str  # BUY or SELL
    entry_price: float
    exit_price: float
    quantity: float
    leverage: int
    pnl: float
    pnl_percent: float
    fees: float
    exit_reason: str
    signal_reason: Optional[str] = None
    duration_minutes: int


class EquityCurvePoint(BaseModel):
    """Single point on the equity curve."""
    timestamp: datetime
    equity: float
    drawdown: float
    drawdown_percent: float


class DailyReturn(BaseModel):
    """Daily return data."""
    date: str
    pnl: float
    return_percent: float
    trades: int


class MonthlyReturn(BaseModel):
    """Monthly return data."""
    month: str  # YYYY-MM
    pnl: float
    return_percent: float
    trades: int


class BacktestMetrics(BaseModel):
    """Comprehensive backtest performance metrics."""
    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # P&L metrics
    total_pnl: float = 0.0
    total_return: float = 0.0
    simple_apy: float = 0.0
    compound_apy: float = 0.0
    
    # Risk metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    
    # Trade quality metrics
    profit_factor: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    average_trade_duration_minutes: float = 0.0
    
    # Cost metrics
    total_fees: float = 0.0
    total_slippage: float = 0.0
    
    # Additional stats
    best_day: float = 0.0
    worst_day: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    expectancy: float = 0.0  # (win_rate * avg_win) - (loss_rate * avg_loss)


class BacktestResult(BaseModel):
    """Complete backtest result response."""
    result_id: Optional[str] = None
    symbol: str
    strategy: str
    start_date: datetime
    end_date: datetime
    timeframe: str
    initial_capital: float
    final_capital: float
    
    # Configuration used
    config: BacktestConfig
    indicators: IndicatorConfig
    
    # Metrics
    metrics: BacktestMetrics
    
    # Detailed data
    equity_curve: List[EquityCurvePoint]
    trades: List[TradeDetail]
    daily_returns: List[DailyReturn]
    monthly_returns: List[MonthlyReturn]
    
    # Execution info
    execution_time_seconds: float
    data_points_analyzed: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BacktestResultSummary(BaseModel):
    """Summary of a saved backtest result for listing."""
    result_id: str
    symbol: str
    strategy: str
    start_date: datetime
    end_date: datetime
    total_trades: int
    win_rate: float
    total_return: float
    simple_apy: float
    compound_apy: float
    sharpe_ratio: float
    max_drawdown_percent: float
    created_at: datetime


class BacktestHistoryResponse(BaseModel):
    """Response for backtest history listing."""
    results: List[BacktestResultSummary]
    total: int

