"""Orchestrator monitoring and health check endpoints."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.core.database import get_db
from app.api.v1.deps import get_current_tenant

router = APIRouter()


class OrchestratorStatus(BaseModel):
    """Orchestrator status response."""
    instance_id: str
    status: str
    active_bots_count: int
    last_heartbeat: Optional[datetime]
    started_at: Optional[datetime]


class BotHealthStatus(BaseModel):
    """Bot health status."""
    bot_id: str
    name: str
    symbol: str
    strategy: str
    status: str
    heartbeat_at: Optional[datetime]
    is_healthy: bool
    error_message: Optional[str]
    trades_count: int
    pnl_total: float


class SystemHealthResponse(BaseModel):
    """Overall system health response."""
    is_healthy: bool
    orchestrator_running: bool
    total_bots: int
    running_bots: int
    healthy_bots: int
    stale_bots: int
    error_bots: int
    last_check: datetime


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(db: Client = Depends(get_db)):
    """
    Get overall system health status.
    This endpoint is public for monitoring tools.
    """
    try:
        # Get orchestrator status
        orchestrator_result = db.table("orchestrator_status").select("*").order(
            "last_heartbeat", desc=True
        ).limit(1).execute()
        
        orchestrator_running = False
        if orchestrator_result.data:
            orch = orchestrator_result.data[0]
            last_heartbeat = datetime.fromisoformat(orch['last_heartbeat'].replace('Z', '+00:00'))
            # Consider orchestrator running if heartbeat within last 30 seconds
            orchestrator_running = (datetime.now(timezone.utc) - last_heartbeat).seconds < 30
        
        # Get bot statistics
        bots_result = db.table("bots").select("id, status, heartbeat_at").execute()
        bots = bots_result.data or []
        
        total_bots = len(bots)
        running_bots = sum(1 for b in bots if b['status'] == 'running')
        error_bots = sum(1 for b in bots if b['status'] == 'error')
        
        # Check for stale bots (running but no heartbeat in 5 minutes)
        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        healthy_bots = 0
        stale_bots = 0
        
        for bot in bots:
            if bot['status'] == 'running':
                if bot.get('heartbeat_at'):
                    heartbeat = datetime.fromisoformat(bot['heartbeat_at'].replace('Z', '+00:00'))
                    if heartbeat > stale_threshold:
                        healthy_bots += 1
                    else:
                        stale_bots += 1
                else:
                    stale_bots += 1
        
        is_healthy = orchestrator_running and stale_bots == 0 and error_bots == 0
        
        return SystemHealthResponse(
            is_healthy=is_healthy,
            orchestrator_running=orchestrator_running,
            total_bots=total_bots,
            running_bots=running_bots,
            healthy_bots=healthy_bots,
            stale_bots=stale_bots,
            error_bots=error_bots,
            last_check=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/status", response_model=OrchestratorStatus)
async def get_orchestrator_status(db: Client = Depends(get_db)):
    """Get orchestrator instance status."""
    result = db.table("orchestrator_status").select("*").order(
        "last_heartbeat", desc=True
    ).limit(1).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orchestrator status found"
        )
    
    orch = result.data[0]
    return OrchestratorStatus(
        instance_id=orch['instance_id'],
        status=orch['status'],
        active_bots_count=orch['active_bots_count'],
        last_heartbeat=orch.get('last_heartbeat'),
        started_at=orch.get('started_at')
    )


@router.get("/bots/health", response_model=List[BotHealthStatus])
async def get_bots_health(
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Get health status of all bots for current tenant."""
    result = db.table("bots").select("*").eq("tenant_id", tenant["id"]).execute()
    
    stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
    health_statuses = []
    
    for bot in result.data or []:
        is_healthy = False
        
        if bot['status'] == 'running':
            if bot.get('heartbeat_at'):
                heartbeat = datetime.fromisoformat(bot['heartbeat_at'].replace('Z', '+00:00'))
                is_healthy = heartbeat > stale_threshold
        elif bot['status'] == 'stopped':
            is_healthy = True  # Stopped bots are considered healthy
        
        health_statuses.append(BotHealthStatus(
            bot_id=bot['id'],
            name=bot['name'],
            symbol=bot['symbol'],
            strategy=bot['strategy'],
            status=bot['status'],
            heartbeat_at=bot.get('heartbeat_at'),
            is_healthy=is_healthy,
            error_message=bot.get('error_message'),
            trades_count=bot.get('trades_count', 0),
            pnl_total=float(bot.get('pnl_total', 0))
        ))
    
    return health_statuses


@router.get("/bots/stale", response_model=List[BotHealthStatus])
async def get_stale_bots(
    minutes: int = 5,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Get bots that haven't sent a heartbeat recently."""
    stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    result = db.table("bots").select("*").eq(
        "tenant_id", tenant["id"]
    ).eq("status", "running").execute()
    
    stale_bots = []
    for bot in result.data or []:
        is_stale = True
        if bot.get('heartbeat_at'):
            heartbeat = datetime.fromisoformat(bot['heartbeat_at'].replace('Z', '+00:00'))
            is_stale = heartbeat < stale_threshold
        
        if is_stale:
            stale_bots.append(BotHealthStatus(
                bot_id=bot['id'],
                name=bot['name'],
                symbol=bot['symbol'],
                strategy=bot['strategy'],
                status=bot['status'],
                heartbeat_at=bot.get('heartbeat_at'),
                is_healthy=False,
                error_message=bot.get('error_message') or "No recent heartbeat",
                trades_count=bot.get('trades_count', 0),
                pnl_total=float(bot.get('pnl_total', 0))
            ))
    
    return stale_bots


@router.post("/bots/{bot_id}/restart")
async def request_bot_restart(
    bot_id: str,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """
    Request a bot restart by setting its status to 'running'.
    The orchestrator will pick it up and start it.
    """
    # Verify bot exists and belongs to tenant
    existing = db.table("bots").select("*").eq(
        "id", bot_id
    ).eq("tenant_id", tenant["id"]).single().execute()
    
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Check if tenant has valid exchange credentials
    creds = db.table("exchange_credentials").select("id").eq(
        "tenant_id", tenant["id"]
    ).execute()
    
    if not creds.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No exchange credentials configured"
        )
    
    # Set status to running (orchestrator will pick it up)
    db.table("bots").update({
        "status": "running",
        "error_message": None,
        "last_active_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", bot_id).execute()
    
    return {"message": "Bot restart requested", "bot_id": bot_id}


@router.post("/bots/{bot_id}/force-stop")
async def force_stop_bot(
    bot_id: str,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """
    Force stop a bot by setting its status to 'stopped'.
    The orchestrator will stop it on next sync.
    """
    # Verify bot exists and belongs to tenant
    existing = db.table("bots").select("*").eq(
        "id", bot_id
    ).eq("tenant_id", tenant["id"]).single().execute()
    
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    db.table("bots").update({
        "status": "stopped",
        "last_active_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", bot_id).execute()
    
    return {"message": "Bot force stop requested", "bot_id": bot_id}

