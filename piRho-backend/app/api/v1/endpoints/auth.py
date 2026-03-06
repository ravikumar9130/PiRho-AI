"""Authentication endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.database import get_db
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.config import get_settings
from app.models.user import UserCreate, UserLogin, UserResponse, TokenResponse, TokenRefresh
from app.models.tenant import PlanType

router = APIRouter()
settings = get_settings()

# Valid promo codes
PROMO_CODES = {
    "rk_dev": PlanType.PRO,
}


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: Client = Depends(get_db)):
    """Register a new user account."""
    # Check if email exists
    existing = db.table("users").select("id").eq("email", user_in.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_data = {
        "email": user_in.email,
        "password_hash": get_password_hash(user_in.password),
        "name": user_in.name,
        "status": "active",
        "email_verified": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    result = db.table("users").insert(user_data).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    user = result.data[0]
    
    # Determine plan based on promo code
    plan = PlanType.FREE
    promo_code_used = None
    promo_applied_at = None
    
    if user_in.promo_code:
        code = user_in.promo_code.strip().lower()
        if code in PROMO_CODES:
            plan = PROMO_CODES[code]
            promo_code_used = code
            promo_applied_at = datetime.now(timezone.utc).isoformat()
    
    # Create tenant
    tenant_data = {
        "user_id": user["id"],
        "name": user_in.name or user_in.email.split("@")[0],
        "plan": plan.value,
        "promo_code_used": promo_code_used,
        "promo_applied_at": promo_applied_at,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "settings": {},
    }
    db.table("tenants").insert(tenant_data).execute()
    
    # Generate tokens
    token_data = {"sub": user["id"], "email": user["email"]}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin, db: Client = Depends(get_db)):
    """Authenticate user and return tokens."""
    result = db.table("users").select("*").eq("email", user_in.email).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user = result.data[0]
    
    if not verify_password(user_in.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )
    
    # Generate tokens
    token_data = {"sub": user["id"], "email": user["email"]}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_in: TokenRefresh, db: Client = Depends(get_db)):
    """Refresh access token using refresh token."""
    payload = decode_token(token_in.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    result = db.table("users").select("*").eq("id", user_id).execute()
    
    if not result.data or result.data[0].get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    user = result.data[0]
    token_data = {"sub": user["id"], "email": user["email"]}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout():
    """Logout user (client should discard tokens)."""
    return {"message": "Logged out successfully"}
