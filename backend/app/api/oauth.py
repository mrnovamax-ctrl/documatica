"""
OAuth API endpoints (Yandex)
"""

import os
import secrets
import httpx
from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Depends, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.models import User

router = APIRouter(tags=["OAuth"])

# Yandex OAuth settings
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID", "")
YANDEX_CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET", "")
YANDEX_REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI", "https://oplatanalogov.ru/auth/yandex/callback")

# JWT settings (same as auth.py)
SECRET_KEY = os.getenv("SECRET_KEY", "documatica-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days


def create_access_token(user_id: int) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.get("/yandex/login")
async def yandex_login(
    request: Request,
    draft_token: str = None,
    redirect_to: str = None
):
    """
    Redirect to Yandex OAuth authorization page
    """
    if not YANDEX_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Yandex OAuth not configured")
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in session/cookie for validation
    params = {
        "response_type": "code",
        "client_id": YANDEX_CLIENT_ID,
        "redirect_uri": YANDEX_REDIRECT_URI,
        "state": state,
        "scope": "login:email login:info",
    }
    
    auth_url = f"https://oauth.yandex.ru/authorize?{urlencode(params)}"
    
    response = RedirectResponse(url=auth_url)
    # Store state in cookie for validation on callback
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=600,  # 10 minutes
    )
    
    # Store draft_token if provided (for restoring document after login)
    if draft_token:
        response.set_cookie(
            key="oauth_draft_token",
            value=draft_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=600,
        )
    
    # Store redirect URL if provided
    if redirect_to:
        response.set_cookie(
            key="oauth_redirect_to",
            value=redirect_to,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=600,
        )
    
    return response


@router.get("/yandex/callback")
async def yandex_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle Yandex OAuth callback
    """
    # Check for OAuth errors
    if error:
        print(f"[YANDEX_OAUTH] Error from Yandex: {error}")
        return RedirectResponse(url="/login/?error=yandex_denied")
    
    if not code:
        print("[YANDEX_OAUTH] No code received")
        return RedirectResponse(url="/login/?error=no_code")
    
    # Validate state (CSRF protection)
    stored_state = request.cookies.get("oauth_state")
    if state != stored_state:
        print(f"[YANDEX_OAUTH] State mismatch: {state} != {stored_state}")
        return RedirectResponse(url="/login/?error=invalid_state")
    
    try:
        # Exchange code for access token
        token_data = await exchange_code_for_token(code)
        yandex_access_token = token_data.get("access_token")
        
        if not yandex_access_token:
            print(f"[YANDEX_OAUTH] No access token in response: {token_data}")
            return RedirectResponse(url="/login/?error=no_token")
        
        # Get user info from Yandex
        user_info = await get_yandex_user_info(yandex_access_token)
        yandex_id = user_info.get("id")
        email = user_info.get("default_email")
        name = user_info.get("display_name") or user_info.get("real_name") or user_info.get("first_name", "")
        phone = None
        default_phone = user_info.get("default_phone") or {}
        if isinstance(default_phone, dict):
            phone = default_phone.get("number")
        if not phone:
            phone = user_info.get("phone")
        
        if not yandex_id or not email:
            print(f"[YANDEX_OAUTH] Missing user info: {user_info}")
            return RedirectResponse(url="/login/?error=no_user_info")
        
        print(f"[YANDEX_OAUTH] User info: id={yandex_id}, email={email}, name={name}")
        
        # Find or create user
        user = db.query(User).filter(User.yandex_id == str(yandex_id)).first()
        
        if not user:
            # Check if user with this email exists
            user = db.query(User).filter(User.email == email.lower()).first()
            
            if user:
                # Link Yandex account to existing user
                user.yandex_id = str(yandex_id)
                if not user.is_verified:
                    user.is_verified = True  # Yandex email is verified
                print(f"[YANDEX_OAUTH] Linked Yandex to existing user: {user.email}")
                is_new_registration = False
            else:
                # Create new user
                user = User(
                    email=email.lower(),
                    name=name,
                    phone=phone,
                    yandex_id=str(yandex_id),
                    auth_provider="yandex",
                    is_verified=True,  # Yandex email is verified
                    password_hash=None,  # No password for OAuth users
                )
                db.add(user)
                print(f"[YANDEX_OAUTH] Created new user: {email}")
                # Mark as new registration for Yandex Metrika goal
                is_new_registration = True
        else:
            is_new_registration = False
            if phone and not user.phone:
                user.phone = phone
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        access_token = create_access_token(user.id)
        
        # Check for draft_token and redirect_to from cookies
        draft_token = request.cookies.get("oauth_draft_token")
        redirect_to = request.cookies.get("oauth_redirect_to", "/dashboard/")
        
        # Add registration flag for new users
        if is_new_registration:
            separator = "&" if "?" in redirect_to else "?"
            redirect_to = f"{redirect_to}{separator}yandex_registered=1"
        
        # If there's a draft, claim it and convert to document
        if draft_token:
            from app.models import GuestDraft
            from app.services.draft_converter import convert_draft_to_document
            
            draft = db.query(GuestDraft).filter(GuestDraft.draft_token == draft_token).first()
            if draft and not draft.is_claimed:
                # Привязываем черновик к пользователю
                draft.user_id = user.id
                draft.is_claimed = True
                draft.updated_at = datetime.utcnow()
                db.commit()
                print(f"[YANDEX_OAUTH] Claimed draft {draft_token[:8]}... for user {user.email}")
                
                # Конвертируем черновик в документ
                doc_id = convert_draft_to_document(draft, user, db)
                if doc_id:
                    print(f"[YANDEX_OAUTH] Converted draft to document {doc_id}")
                    # Редиректим в дашборд (там будет виден документ)
                    redirect_to = "/dashboard/"
        
        # Redirect to appropriate page
        response = RedirectResponse(url=redirect_to)
        
        # Set cookie
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=False,
            secure=is_production,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        )
        
        # Clear oauth state cookie
        response.delete_cookie("oauth_state")
        response.delete_cookie("oauth_draft_token")
        response.delete_cookie("oauth_redirect_to")
        
        print(f"[YANDEX_OAUTH] SUCCESS: User {user.email} logged in via Yandex")
        
        return response
        
    except Exception as e:
        print(f"[YANDEX_OAUTH] Error: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url="/login/?error=oauth_error")


async def exchange_code_for_token(code: str) -> dict:
    """
    Exchange authorization code for access token
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": YANDEX_CLIENT_ID,
                "client_secret": YANDEX_CLIENT_SECRET,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        
        if response.status_code != 200:
            print(f"[YANDEX_OAUTH] Token exchange failed: {response.status_code} {response.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        return response.json()


async def get_yandex_user_info(access_token: str) -> dict:
    """
    Get user info from Yandex API
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://login.yandex.ru/info",
            headers={
                "Authorization": f"OAuth {access_token}",
            },
            params={
                "format": "json",
                "with_phone_number": "true",
            }
        )
        
        if response.status_code != 200:
            print(f"[YANDEX_OAUTH] User info request failed: {response.status_code} {response.text}")
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        return response.json()
