"""Promo code and plan management endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.core.database import get_db
from app.config import get_settings
from app.api.v1.deps import get_current_user, get_current_tenant
from app.models.tenant import PlanType

router = APIRouter()
settings = get_settings()

# Valid promo codes and their plans
PROMO_CODES = {
    "rk_dev": PlanType.PRO,
}


class PromoCodeRequest(BaseModel):
    code: str


class PromoCodeResponse(BaseModel):
    success: bool
    message: str
    plan: str


@router.post("/apply-promo", response_model=PromoCodeResponse)
async def apply_promo_code(
    request: PromoCodeRequest,
    user: dict = Depends(get_current_user),
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
):
    """Apply a promo code to unlock a plan."""
    code = request.code.strip().lower()
    
    if code not in PROMO_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid promo code"
        )
    
    plan = PROMO_CODES[code]
    
    # Update tenant plan
    db.table("tenants").update({
        "plan": plan.value,
        "promo_code_used": code,
        "promo_applied_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", tenant["id"]).execute()
    
    return PromoCodeResponse(
        success=True,
        message=f"Promo code applied! You now have access to the {plan.value.title()} plan.",
        plan=plan.value
    )


@router.get("/current-plan")
async def get_current_plan(
    tenant: dict = Depends(get_current_tenant)
):
    """Get current plan details."""
    return {
        "plan": tenant.get("plan", "free"),
        "promo_code_used": tenant.get("promo_code_used"),
        "promo_applied_at": tenant.get("promo_applied_at")
    }


@router.get("/plans")
async def list_plans():
    """List available plans."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "features": ["Paper trading", "2 strategies", "1 bot", "1 symbol"]
            },
            {
                "id": "starter",
                "name": "Starter",
                "price": 49,
                "features": ["Live trading", "5 strategies", "2 bots", "1 symbol", "Sentiment analysis", "Telegram alerts"]
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 149,
                "features": ["All 11 strategies", "5 bots", "5 symbols", "LSTM models", "Priority support"],
                "promo_available": True
            },
            {
                "id": "fund",
                "name": "Fund",
                "price": 499,
                "features": ["Unlimited bots", "20 symbols", "Custom strategies", "API access", "White-label"]
            }
        ]
    }
