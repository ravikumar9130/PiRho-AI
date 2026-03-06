"""Trading bot management endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.database import get_db
from app.api.v1.deps import get_current_tenant, verify_bot_limit, get_plan_limits
from app.models.bot import BotCreate, BotUpdate, BotResponse, BotStatus
from app.models.tenant import PlanLimits

router = APIRouter()


@router.get("", response_model=list[BotResponse])
async def list_bots(
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """List all trading bots for current tenant."""
    result = db.table("bots").select("*").eq("tenant_id", tenant["id"]).order("created_at", desc=True).execute()
    return [BotResponse(**bot) for bot in result.data or []]


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_in: BotCreate,
    tenant: dict = Depends(get_current_tenant),
    limits: PlanLimits = Depends(get_plan_limits),
    db: Client = Depends(get_db),
    _: None = Depends(verify_bot_limit)
):
    """Create a new trading bot."""
    # Validate strategy is available in plan
    if bot_in.strategy not in limits.strategies:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Strategy '{bot_in.strategy}' not available in your plan"
        )
    
    bot_data = {
        "tenant_id": tenant["id"],
        "name": bot_in.name,
        "symbol": bot_in.symbol,
        "strategy": bot_in.strategy,
        "status": BotStatus.STOPPED.value,
        "config": bot_in.config.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    result = db.table("bots").insert(bot_data).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create bot")
    
    return BotResponse(**result.data[0])


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: str,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Get a specific trading bot."""
    result = db.table("bots").select("*").eq("id", bot_id).eq("tenant_id", tenant["id"]).single().execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
    return BotResponse(**result.data)


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: str,
    bot_in: BotUpdate,
    tenant: dict = Depends(get_current_tenant),
    limits: PlanLimits = Depends(get_plan_limits),
    db: Client = Depends(get_db)
):
    """Update a trading bot configuration."""
    # Verify bot exists and belongs to tenant
    existing = db.table("bots").select("*").eq("id", bot_id).eq("tenant_id", tenant["id"]).single().execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
    
    update_dict = bot_in.model_dump(exclude_unset=True)
    
    # Validate strategy if being updated
    if "strategy" in update_dict and update_dict["strategy"] not in limits.strategies:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Strategy '{update_dict['strategy']}' not available in your plan"
        )
    
    if "config" in update_dict:
        update_dict["config"] = update_dict["config"].model_dump()
    
    result = db.table("bots").update(update_dict).eq("id", bot_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Update failed")
    
    return BotResponse(**result.data[0])


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: str,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Delete a trading bot."""
    # Check if bot is running
    existing = db.table("bots").select("status").eq("id", bot_id).eq("tenant_id", tenant["id"]).single().execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
    
    if existing.data["status"] == BotStatus.RUNNING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a running bot. Stop it first.")
    
    db.table("bots").delete().eq("id", bot_id).execute()
    return {"message": "Bot deleted"}


@router.post("/{bot_id}/start", response_model=BotResponse)
async def start_bot(
    bot_id: str,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Start a trading bot."""
    existing = db.table("bots").select("*").eq("id", bot_id).eq("tenant_id", tenant["id"]).single().execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
    
    if existing.data["status"] == BotStatus.RUNNING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bot is already running")
    
    # Check if tenant has valid exchange credentials
    creds = db.table("exchange_credentials").select("id").eq("tenant_id", tenant["id"]).execute()
    if not creds.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No exchange credentials configured. Add your API keys first."
        )
    
    result = db.table("bots").update({
        "status": BotStatus.RUNNING.value,
        "last_active_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", bot_id).execute()
    
    return BotResponse(**result.data[0])


@router.post("/{bot_id}/stop", response_model=BotResponse)
async def stop_bot(
    bot_id: str,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Stop a trading bot."""
    existing = db.table("bots").select("*").eq("id", bot_id).eq("tenant_id", tenant["id"]).single().execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
    
    result = db.table("bots").update({
        "status": BotStatus.STOPPED.value
    }).eq("id", bot_id).execute()
    
    return BotResponse(**result.data[0])


@router.get("/strategies/available")
async def list_available_strategies(limits: PlanLimits = Depends(get_plan_limits)):
    """List strategies available for current plan."""
    return {
        "strategies": limits.strategies,
        "has_lstm": limits.has_lstm,
        "has_sentiment": limits.has_sentiment
    }

