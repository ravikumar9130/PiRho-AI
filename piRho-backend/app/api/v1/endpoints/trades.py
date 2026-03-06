"""Trade history and position endpoints."""
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.core.database import get_db
from app.api.v1.deps import get_current_tenant
from app.models.trade import TradeResponse, PerformanceStats, SignalLogResponse

router = APIRouter()


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    symbol: Optional[str] = None,
    bot_id: Optional[str] = None,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """List trade history with pagination and filters."""
    query = db.table("trades").select("*").eq("tenant_id", tenant["id"])
    
    if symbol:
        query = query.eq("symbol", symbol)
    if bot_id:
        query = query.eq("bot_id", bot_id)
    
    result = query.order("opened_at", desc=True).range(offset, offset + limit - 1).execute()
    return [TradeResponse(**trade) for trade in result.data or []]


@router.get("/performance", response_model=PerformanceStats)
async def get_performance_stats(
    days: int = Query(default=30, le=365),
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Get trading performance statistics."""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    result = db.table("trades").select("*").eq("tenant_id", tenant["id"]).gte("closed_at", start_date).not_.is_("closed_at", "null").execute()
    
    trades = result.data or []
    
    if not trades:
        return PerformanceStats(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_profit_loss=0.0,
            average_profit=0.0,
            average_loss=0.0,
            max_drawdown=0.0,
            profit_factor=0.0
        )
    
    # Calculate stats
    profits = [t["profit_loss"] for t in trades if (t.get("profit_loss") or 0) > 0]
    losses = [abs(t["profit_loss"]) for t in trades if (t.get("profit_loss") or 0) < 0]
    
    total_profit = sum(profits) if profits else 0
    total_loss = sum(losses) if losses else 0
    
    # Max drawdown calculation
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in sorted(trades, key=lambda x: x["closed_at"]):
        cumulative += t.get("profit_loss") or 0
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    
    return PerformanceStats(
        total_trades=len(trades),
        winning_trades=len(profits),
        losing_trades=len(losses),
        win_rate=(len(profits) / len(trades) * 100) if trades else 0,
        total_profit_loss=total_profit - total_loss,
        average_profit=(total_profit / len(profits)) if profits else 0,
        average_loss=(total_loss / len(losses)) if losses else 0,
        max_drawdown=max_dd,
        profit_factor=(total_profit / total_loss) if total_loss > 0 else 0
    )


@router.get("/daily-summary")
async def get_daily_summary(
    days: int = Query(default=7, le=30),
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Get daily P&L summary."""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    result = db.table("trades").select("closed_at, profit_loss").eq("tenant_id", tenant["id"]).gte("closed_at", start_date).not_.is_("closed_at", "null").execute()
    
    # Group by date
    daily_pnl = {}
    for trade in result.data or []:
        date = trade["closed_at"][:10]  # Extract YYYY-MM-DD
        daily_pnl[date] = daily_pnl.get(date, 0) + (trade.get("profit_loss") or 0)
    
    # Fill missing dates
    summary = []
    for i in range(days):
        date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        summary.append({
            "date": date,
            "pnl": daily_pnl.get(date, 0)
        })
    
    return {"summary": sorted(summary, key=lambda x: x["date"])}


@router.get("/signals", response_model=list[SignalLogResponse])
async def list_signal_logs(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    bot_id: Optional[str] = None,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """List signal logs with pagination and filters."""
    query = db.table("signal_logs").select("*").eq("tenant_id", tenant["id"])
    
    if bot_id:
        query = query.eq("bot_id", bot_id)
    
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return [SignalLogResponse(**log) for log in result.data or []]

