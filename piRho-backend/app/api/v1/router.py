"""API v1 router aggregating all endpoints."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, bots, trades, billing, orchestrator, backtesting

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(bots.router, prefix="/bots", tags=["Trading Bots"])
api_router.include_router(trades.router, prefix="/trades", tags=["Trades"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(orchestrator.router, prefix="/orchestrator", tags=["Orchestrator"])
api_router.include_router(backtesting.router, prefix="/backtesting", tags=["Backtesting"])

