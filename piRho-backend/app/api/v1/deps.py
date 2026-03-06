"""API dependencies for authentication and rate limiting."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token
from app.core.cache import rate_limiter
from app.core.database import get_db
from app.models.tenant import PlanType, PLAN_LIMITS
from supabase import Client


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Client = Depends(get_db)
) -> dict:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Fetch user from database
    result = db.table("users").select("*").eq("id", user_id).single().execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if result.data.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )
    
    return result.data


async def get_current_tenant(
    user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
) -> dict:
    """Get current user's tenant."""
    result = db.table("tenants").select("*").eq("user_id", user["id"]).single().execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return result.data


def check_rate_limit(user: dict = Depends(get_current_user)) -> bool:
    """Check if user is within rate limits."""
    user_id = user["id"]
    if not rate_limiter.is_allowed(user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    return True


def get_plan_limits(tenant: dict = Depends(get_current_tenant)):
    """Get plan limits for current tenant."""
    plan = PlanType(tenant.get("plan", "free"))
    return PLAN_LIMITS[plan]


async def verify_bot_limit(
    tenant: dict = Depends(get_current_tenant),
    db: Client = Depends(get_db)
) -> None:
    """Verify user hasn't exceeded bot limit."""
    limits = PLAN_LIMITS[PlanType(tenant.get("plan", "free"))]
    result = db.table("bots").select("id", count="exact").eq("tenant_id", tenant["id"]).execute()
    if result.count and result.count >= limits.max_bots:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Bot limit reached for {tenant['plan']} plan. Max: {limits.max_bots}",
        )

