"""Tenant and subscription-related Pydantic models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class PlanType(str, Enum):
    """Subscription plan types."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    FUND = "fund"


class TenantBase(BaseModel):
    """Base tenant schema."""
    name: Optional[str] = None


class TenantCreate(TenantBase):
    """Schema for tenant creation."""
    pass


class TenantResponse(TenantBase):
    """Schema for tenant response."""
    id: str
    user_id: str
    plan: PlanType = PlanType.FREE
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    created_at: datetime
    settings: dict = {}
    
    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Schema for subscription details."""
    plan: PlanType
    status: str
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    trial_ends_at: Optional[datetime] = None


class PlanLimits(BaseModel):
    """Plan feature limits."""
    max_bots: int
    max_symbols: int
    strategies: list[str]
    has_lstm: bool
    has_sentiment: bool
    api_rate_limit: int


PLAN_LIMITS: dict[PlanType, PlanLimits] = {
    PlanType.FREE: PlanLimits(
        max_bots=1, max_symbols=1, strategies=["MA_Crossover", "EMA_Cross_RSI"],
        has_lstm=False, has_sentiment=False, api_rate_limit=30
    ),
    PlanType.STARTER: PlanLimits(
        max_bots=2, max_symbols=1, strategies=[
            "MA_Crossover", "EMA_Cross_RSI", "Supertrend_MACD", 
            "BB_Squeeze_Breakout", "RSI_Divergence"
        ],
        has_lstm=False, has_sentiment=True, api_rate_limit=60
    ),
    PlanType.PRO: PlanLimits(
        max_bots=5, max_symbols=5, strategies=[
            "MA_Crossover", "EMA_Cross_RSI", "Supertrend_MACD", 
            "BB_Squeeze_Breakout", "RSI_Divergence", "LSTM_Momentum",
            "Volatility_Cluster_Reversal", "Volume_Spread_Analysis",
            "Reversal_Detector", "Momentum_VWAP_RSI", "Funding_Rate"
        ],
        has_lstm=True, has_sentiment=True, api_rate_limit=300
    ),
    PlanType.FUND: PlanLimits(
        max_bots=20, max_symbols=20, strategies=[
            "MA_Crossover", "EMA_Cross_RSI", "Supertrend_MACD", 
            "BB_Squeeze_Breakout", "RSI_Divergence", "LSTM_Momentum",
            "Volatility_Cluster_Reversal", "Volume_Spread_Analysis",
            "Reversal_Detector", "Momentum_VWAP_RSI", "Funding_Rate"
        ],
        has_lstm=True, has_sentiment=True, api_rate_limit=1000
    ),
}

