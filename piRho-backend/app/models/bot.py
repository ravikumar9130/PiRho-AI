"""Trading bot-related Pydantic models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class BotStatus(str, Enum):
    """Bot status states."""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    PAUSED = "paused"


class ExchangeType(str, Enum):
    """Supported exchanges."""
    BYBIT = "bybit"


class BotConfig(BaseModel):
    """Bot configuration settings."""
    leverage: int = Field(default=5, ge=1, le=100)
    risk_per_trade: float = Field(default=2.0, ge=0.1, le=10.0)
    stop_loss_percent: float = Field(default=2.0, ge=0.5, le=10.0)
    take_profit_percent: float = Field(default=4.0, ge=1.0, le=20.0)
    use_trailing_stop: bool = True
    trailing_stop_percent: float = Field(default=1.5, ge=0.5, le=5.0)
    max_trades_per_day: int = Field(default=5, ge=1, le=20)
    paper_trading: bool = True


class BotCreate(BaseModel):
    """Schema for bot creation."""
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., pattern=r"^[A-Z]+USDT$")
    strategy: str
    config: BotConfig = BotConfig()


class BotUpdate(BaseModel):
    """Schema for bot update."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    strategy: Optional[str] = None
    config: Optional[BotConfig] = None


class BotResponse(BaseModel):
    """Schema for bot response."""
    id: str
    tenant_id: str
    name: str
    symbol: str
    strategy: str
    status: BotStatus = BotStatus.STOPPED
    config: dict
    created_at: datetime
    last_active_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExchangeCredentialCreate(BaseModel):
    """Schema for exchange credential creation."""
    exchange: ExchangeType = ExchangeType.BYBIT
    api_key: str = Field(..., min_length=10)
    api_secret: str = Field(..., min_length=10)
    is_testnet: bool = True


class ExchangeCredentialResponse(BaseModel):
    """Schema for exchange credential response (masked)."""
    id: str
    exchange: ExchangeType
    is_testnet: bool
    api_key_masked: str
    created_at: datetime
    last_validated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

