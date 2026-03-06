"""User management endpoints."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.database import get_db
from app.core.security import encrypt_api_key, decrypt_api_key
from app.api.v1.deps import get_current_user, get_current_tenant
from app.models.user import UserResponse, UserUpdate
from app.models.bot import ExchangeCredentialCreate, ExchangeCredentialResponse
from app.models.tenant import TenantResponse, SubscriptionResponse
from app.models.trade import DashboardStats

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user.get("name"),
        status=user.get("status", "active"),
        email_verified=user.get("email_verified", False),
        created_at=user["created_at"]
    )


@router.patch("/me", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdate,
    user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Update current user profile."""
    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update")
    
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = db.table("users").update(update_dict).eq("id", user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Update failed")
    
    updated = result.data[0]
    return UserResponse(
        id=updated["id"],
        email=updated["email"],
        name=updated.get("name"),
        status=updated.get("status", "active"),
        email_verified=updated.get("email_verified", False),
        created_at=updated["created_at"]
    )


@router.get("/tenant", response_model=TenantResponse)
async def get_tenant(tenant: dict = Depends(get_current_tenant)):
    """Get current user's tenant details."""
    return TenantResponse(**tenant)


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(tenant: dict = Depends(get_current_tenant)):
    """Get subscription details."""
    return SubscriptionResponse(
        plan=tenant.get("plan", "free"),
        status="active" if tenant.get("stripe_subscription_id") else "trial",
        trial_ends_at=tenant.get("trial_ends_at"),
        cancel_at_period_end=False
    )


@router.post("/exchange-credentials", response_model=ExchangeCredentialResponse)
async def add_exchange_credentials(
    creds: ExchangeCredentialCreate,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Add exchange API credentials (encrypted)."""
    # Encrypt API keys
    encrypted_key = encrypt_api_key(creds.api_key)
    encrypted_secret = encrypt_api_key(creds.api_secret)
    
    # Mask API key for response
    masked_key = creds.api_key[:4] + "****" + creds.api_key[-4:]
    
    cred_data = {
        "tenant_id": tenant["id"],
        "exchange": creds.exchange.value,
        "encrypted_api_key": encrypted_key,
        "encrypted_api_secret": encrypted_secret,
        "is_testnet": creds.is_testnet,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    result = db.table("exchange_credentials").insert(cred_data).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save credentials")
    
    saved = result.data[0]
    return ExchangeCredentialResponse(
        id=saved["id"],
        exchange=creds.exchange,
        is_testnet=creds.is_testnet,
        api_key_masked=masked_key,
        created_at=saved["created_at"]
    )


@router.get("/exchange-credentials", response_model=list[ExchangeCredentialResponse])
async def list_exchange_credentials(
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """List all exchange credentials for tenant."""
    result = db.table("exchange_credentials").select("*").eq("tenant_id", tenant["id"]).execute()
    
    credentials = []
    for cred in result.data or []:
        # Decrypt to get first/last 4 chars for masking
        try:
            decrypted = decrypt_api_key(cred["encrypted_api_key"])
            masked = decrypted[:4] + "****" + decrypted[-4:]
        except Exception:
            masked = "****"
        
        credentials.append(ExchangeCredentialResponse(
            id=cred["id"],
            exchange=cred["exchange"],
            is_testnet=cred.get("is_testnet", True),
            api_key_masked=masked,
            created_at=cred["created_at"],
            last_validated_at=cred.get("last_validated_at")
        ))
    
    return credentials


@router.delete("/exchange-credentials/{cred_id}")
async def delete_exchange_credentials(
    cred_id: str,
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Delete exchange credentials."""
    result = db.table("exchange_credentials").delete().eq("id", cred_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credentials not found")
    return {"message": "Credentials deleted"}


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Get dashboard overview statistics."""
    tenant_id = tenant["id"]
    
    # Count running bots
    bots_result = db.table("bots").select("id", count="exact").eq("tenant_id", tenant_id).eq("status", "running").execute()
    running_bots = bots_result.count or 0
    
    # Get today's trades
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()
    trades_result = db.table("trades").select("*").eq("tenant_id", tenant_id).gte("opened_at", today_start).execute()
    
    today_trades = trades_result.data or []
    today_pnl = sum(t.get("profit_loss", 0) or 0 for t in today_trades if t.get("closed_at"))
    
    # Get 7-day win rate
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    week_trades = db.table("trades").select("profit_loss").eq("tenant_id", tenant_id).gte("closed_at", week_ago).execute()
    
    week_data = week_trades.data or []
    if week_data:
        wins = sum(1 for t in week_data if (t.get("profit_loss") or 0) > 0)
        win_rate = (wins / len(week_data)) * 100
    else:
        win_rate = 0.0
    
    # Count active positions (open trades)
    positions = db.table("trades").select("id", count="exact").eq("tenant_id", tenant_id).is_("closed_at", "null").execute()
    
    return DashboardStats(
        total_balance=0.0,  # Fetched from exchange
        unrealized_pnl=0.0,
        today_pnl=today_pnl,
        active_positions=positions.count or 0,
        running_bots=running_bots,
        total_trades_today=len(today_trades),
        win_rate_7d=win_rate
    )

