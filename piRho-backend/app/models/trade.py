"""Trade and position-related Pydantic models."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class TradeSide(str, Enum):
    """Trade side."""
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(str, Enum):
    """Trade status."""
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TradeResponse(BaseModel):
    """Schema for trade response."""
    id: str
    tenant_id: str
    bot_id: Optional[str] = None
    symbol: str
    side: TradeSide
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    leverage: int = 1
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    strategy: Optional[str] = None
    exit_reason: Optional[str] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None
    is_paper: bool = False
    
    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    """Schema for current position."""
    symbol: str
    side: TradeSide
    entry_price: float
    current_price: float
    quantity: float
    leverage: int
    unrealized_pnl: float
    unrealized_pnl_percent: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class PerformanceStats(BaseModel):
    """Schema for performance statistics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit_loss: float
    average_profit: float
    average_loss: float
    max_drawdown: float
    profit_factor: float
    sharpe_ratio: Optional[float] = None


class DashboardStats(BaseModel):
    """Schema for dashboard overview stats."""
    total_balance: float
    unrealized_pnl: float
    today_pnl: float
    active_positions: int
    running_bots: int
    total_trades_today: int
    win_rate_7d: float


class SignalLogResponse(BaseModel):
    """Schema for signal log response."""
    id: str
    tenant_id: str
    bot_id: Optional[str] = None
    trade_id: Optional[str] = None
    symbol: str
    signal: str
    strategy: str
    signal_reason: Optional[str] = None
    market_data: Dict[str, Any] = {}
    sentiment: Optional[str] = None
    funding_rate: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

