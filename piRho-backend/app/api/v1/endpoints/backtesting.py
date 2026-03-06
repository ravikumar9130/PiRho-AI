"""Backtesting endpoints for running and managing strategy backtests."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from supabase import Client

from app.core.database import get_db
from app.api.v1.deps import get_current_tenant, get_plan_limits
from app.models.backtesting import (
    BacktestRequest,
    BacktestResult,
    BacktestResultSummary,
    BacktestHistoryResponse,
    BacktestMetrics,
    TradeDetail,
    EquityCurvePoint,
    DailyReturn,
    MonthlyReturn,
)
from app.models.tenant import PlanLimits

router = APIRouter()
logger = logging.getLogger(__name__)


# Available strategies for backtesting
AVAILABLE_STRATEGIES = [
    "LSTM_Momentum",
    "Supertrend_MACD",
    "Volatility_Cluster_Reversal",
    "Volume_Spread_Analysis",
    "EMA_Cross_RSI",
    "Momentum_VWAP_RSI",
    "BB_Squeeze_Breakout",
    "MA_Crossover",
    "RSI_Divergence",
    "Reversal_Detector",
    "Funding_Rate",
]

# Available symbols
AVAILABLE_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOTUSDT",
    "MATICUSDT",
]


@router.get("/strategies")
async def list_strategies(limits: PlanLimits = Depends(get_plan_limits)):
    """List available strategies for backtesting."""
    return {
        "strategies": limits.strategies if limits.strategies else AVAILABLE_STRATEGIES,
        "all_strategies": AVAILABLE_STRATEGIES
    }


@router.get("/symbols")
async def list_symbols():
    """List available symbols for backtesting."""
    return {"symbols": AVAILABLE_SYMBOLS}


@router.post("/run", response_model=BacktestResult)
async def run_backtest(
    request: BacktestRequest,
    tenant: dict = Depends(get_current_tenant),
    limits: PlanLimits = Depends(get_plan_limits),
    db: Client = Depends(get_db),
):
    """
    Run a backtest with the specified configuration.
    
    This endpoint fetches historical data, runs the strategy simulation,
    and returns comprehensive performance metrics.
    """
    import time
    start_time = time.time()
    
    # Validate strategy is available in plan
    if limits.strategies and request.strategy not in limits.strategies:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Strategy '{request.strategy}' not available in your plan"
        )
    
    # Validate date range
    if request.start_date >= request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
    
    # Limit backtest period for free tier
    max_days = 365 if limits.strategies else 90  # Free tier limited to 90 days
    days_requested = (request.end_date - request.start_date).days
    if days_requested > max_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Backtest period limited to {max_days} days for your plan"
        )
    
    # Validate symbol
    if request.symbol not in AVAILABLE_SYMBOLS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Symbol '{request.symbol}' not available. Choose from: {', '.join(AVAILABLE_SYMBOLS)}"
        )
    
    try:
        # Import the backtesting service
        from app.services.backtesting_service import BacktestingService
        
        service = BacktestingService()
        result = await service.run_backtest(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            strategy=request.strategy,
            timeframe=request.timeframe.value,
            indicators=request.indicators,
            config=request.config,
        )
        
        execution_time = time.time() - start_time
        result.execution_time_seconds = round(execution_time, 2)
        
        # Save result if requested
        if request.save_result:
            result_id = await _save_backtest_result(db, tenant["id"], result)
            result.result_id = result_id
            result.created_at = datetime.now(timezone.utc)
        
        return result
        
    except Exception as e:
        logger.error(f"Backtest execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest execution failed: {str(e)}"
        )


@router.get("/history", response_model=BacktestHistoryResponse)
async def get_backtest_history(
    limit: int = 50,
    offset: int = 0,
    symbol: Optional[str] = None,
    strategy: Optional[str] = None,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db),
):
    """Get list of saved backtest results for the current user."""
    query = db.table("backtest_results").select(
        "id, symbol, strategy, start_date, end_date, total_trades, "
        "win_rate, total_return, simple_apy, compound_apy, sharpe_ratio, "
        "max_drawdown_percent, created_at"
    ).eq("tenant_id", tenant["id"])
    
    if symbol:
        query = query.eq("symbol", symbol)
    if strategy:
        query = query.eq("strategy", strategy)
    
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
    
    result = query.execute()
    
    summaries = []
    for row in result.data or []:
        summaries.append(BacktestResultSummary(
            result_id=row["id"],
            symbol=row["symbol"],
            strategy=row["strategy"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            total_trades=row["total_trades"],
            win_rate=float(row["win_rate"]),
            total_return=float(row["total_return"]),
            simple_apy=float(row["simple_apy"]),
            compound_apy=float(row["compound_apy"]),
            sharpe_ratio=float(row["sharpe_ratio"] or 0),
            max_drawdown_percent=float(row["max_drawdown_percent"] or 0),
            created_at=row["created_at"],
        ))
    
    # Get total count
    count_result = db.table("backtest_results").select(
        "id", count="exact"
    ).eq("tenant_id", tenant["id"]).execute()
    
    return BacktestHistoryResponse(
        results=summaries,
        total=count_result.count or len(summaries)
    )


@router.get("/results/{result_id}", response_model=BacktestResult)
async def get_backtest_result(
    result_id: str,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db),
):
    """Get a specific saved backtest result."""
    result = db.table("backtest_results").select("*").eq(
        "id", result_id
    ).eq("tenant_id", tenant["id"]).single().execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest result not found"
        )
    
    row = result.data
    
    # Reconstruct the full result from stored data
    return BacktestResult(
        result_id=row["id"],
        symbol=row["symbol"],
        strategy=row["strategy"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        timeframe=row["timeframe"],
        initial_capital=float(row["initial_capital"]),
        final_capital=float(row["final_capital"]),
        config=row["config"],
        indicators=row["indicators"],
        metrics=BacktestMetrics(**row["metrics"]),
        equity_curve=[EquityCurvePoint(**p) for p in row["equity_curve"]],
        trades=[TradeDetail(**t) for t in row["trades"]],
        daily_returns=[DailyReturn(**d) for d in row["daily_returns"]],
        monthly_returns=[MonthlyReturn(**m) for m in row["monthly_returns"]],
        execution_time_seconds=float(row["execution_time_seconds"] or 0),
        data_points_analyzed=row["data_points_analyzed"] or 0,
        created_at=row["created_at"],
    )


@router.delete("/results/{result_id}")
async def delete_backtest_result(
    result_id: str,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db),
):
    """Delete a saved backtest result."""
    # Verify ownership
    existing = db.table("backtest_results").select("id").eq(
        "id", result_id
    ).eq("tenant_id", tenant["id"]).single().execute()
    
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest result not found"
        )
    
    db.table("backtest_results").delete().eq("id", result_id).execute()
    
    return {"message": "Backtest result deleted"}


async def _save_backtest_result(
    db: Client,
    tenant_id: str,
    result: BacktestResult
) -> str:
    """Save a backtest result to the database."""
    result_id = str(uuid4())
    
    record = {
        "id": result_id,
        "tenant_id": tenant_id,
        "symbol": result.symbol,
        "strategy": result.strategy,
        "timeframe": result.timeframe,
        "start_date": result.start_date.isoformat(),
        "end_date": result.end_date.isoformat(),
        "initial_capital": result.initial_capital,
        "final_capital": result.final_capital,
        "total_trades": result.metrics.total_trades,
        "winning_trades": result.metrics.winning_trades,
        "losing_trades": result.metrics.losing_trades,
        "win_rate": result.metrics.win_rate,
        "total_pnl": result.metrics.total_pnl,
        "total_return": result.metrics.total_return,
        "simple_apy": result.metrics.simple_apy,
        "compound_apy": result.metrics.compound_apy,
        "sharpe_ratio": result.metrics.sharpe_ratio,
        "max_drawdown": result.metrics.max_drawdown,
        "max_drawdown_percent": result.metrics.max_drawdown_percent,
        "profit_factor": result.metrics.profit_factor,
        "config": result.config.model_dump(),
        "indicators": result.indicators.model_dump(),
        "metrics": result.metrics.model_dump(),
        "equity_curve": [p.model_dump() for p in result.equity_curve],
        "trades": [t.model_dump() for t in result.trades],
        "daily_returns": [d.model_dump() for d in result.daily_returns],
        "monthly_returns": [m.model_dump() for m in result.monthly_returns],
        "execution_time_seconds": result.execution_time_seconds,
        "data_points_analyzed": result.data_points_analyzed,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    db.table("backtest_results").insert(record).execute()
    
    return result_id

