"""
OAuth API endpoints (Yandex)
"""

import logging
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

logger = logging.getLogger(__name__)
router = APIRouter(tags=["OAuth"])

# Yandex OAuth settings
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID", "")
YANDEX_CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET", "")
YANDEX_REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI", "https://oplatanalogov.ru/auth/yandex/callback")

# Google OAuth settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://oplatanalogov.ru/auth/google/callback")

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
        # Яндекс OAuth не требует явных scope для базового доступа к email и info
        # Доступ настраивается в настройках приложения на https://oauth.yandex.ru
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
                    if is_new_registration:
                        redirect_to = f"{redirect_to}?yandex_registered=1"
        
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


@router.get("/google/login")
async def google_login(
    request: Request,
    draft_token: str = None,
    redirect_to: str = None
):
    """Redirect to Google OAuth authorization page."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=600,
        path="/",
    )
    if draft_token:
        response.set_cookie(key="oauth_draft_token", value=draft_token, httponly=True, secure=True, samesite="lax", max_age=600, path="/")
    if redirect_to:
        response.set_cookie(key="oauth_redirect_to", value=redirect_to, httponly=True, secure=True, samesite="lax", max_age=600, path="/")
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback."""
    if error:
        logger.warning("[GOOGLE_OAUTH] Callback with error=%s", error)
        return RedirectResponse(url="/login/?error=google_denied")
    if not code:
        logger.warning("[GOOGLE_OAUTH] No code in callback")
        return RedirectResponse(url="/login/?error=no_code")

    stored_state = request.cookies.get("oauth_state")
    if state != stored_state:
        logger.warning("[GOOGLE_OAUTH] State mismatch: state=%s stored=%s", state, stored_state)
        return RedirectResponse(url="/login/?error=invalid_state")

    try:
        logger.info("[GOOGLE_OAUTH] Exchanging code for token...")
        token_data = await exchange_code_for_google_token(code)
        access_token = token_data.get("access_token")
        if not access_token:
            logger.warning("[GOOGLE_OAUTH] No access_token in response: %s", list(token_data.keys()))
            return RedirectResponse(url="/login/?error=no_token")

        logger.info("[GOOGLE_OAUTH] Getting user info...")
        user_info = await get_google_user_info(access_token)
        google_id = user_info.get("id")
        email = user_info.get("email")
        name = (user_info.get("name") or "").strip() or user_info.get("given_name") or ""
        if isinstance(google_id, (int, float)):
            google_id = str(int(google_id))

        if not google_id or not email:
            logger.warning("[GOOGLE_OAUTH] Missing id or email: id=%s email=%s", google_id, email)
            return RedirectResponse(url="/login/?error=no_user_info")

        logger.info("[GOOGLE_OAUTH] User info: id=%s email=%s", google_id, email)

        user = db.query(User).filter(User.google_id == str(google_id)).first()
        if not user:
            user = db.query(User).filter(User.email == email.lower()).first()
            if user:
                user.google_id = str(google_id)
                user.auth_provider = "google"
                if not user.is_verified:
                    user.is_verified = True
            else:
                now = datetime.utcnow()
                user = User(
                    email=email.lower(),
                    name=name or None,
                    google_id=str(google_id),
                    auth_provider="google",
                    is_verified=True,
                    password_hash=None,
                    created_at=now,
                )
                db.add(user)

        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)

        access_token_jwt = create_access_token(user.id)
        redirect_to = request.cookies.get("oauth_redirect_to", "/dashboard/")
        draft_token = request.cookies.get("oauth_draft_token")

        if draft_token:
            from app.models import GuestDraft
            from app.services.draft_converter import convert_draft_to_document
            draft = db.query(GuestDraft).filter(GuestDraft.draft_token == draft_token).first()
            if draft and not draft.is_claimed:
                draft.user_id = user.id
                draft.is_claimed = True
                draft.updated_at = datetime.utcnow()
                db.commit()
                convert_draft_to_document(draft, user, db)
                redirect_to = "/dashboard/"

        response = RedirectResponse(url=redirect_to)
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        response.set_cookie(
            key="access_token",
            value=access_token_jwt,
            httponly=False,
            secure=is_production,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            path="/",
        )
        response.delete_cookie("oauth_state", path="/")
        response.delete_cookie("oauth_draft_token", path="/")
        response.delete_cookie("oauth_redirect_to", path="/")
        logger.info("[GOOGLE_OAUTH] Success: user %s", user.email)
        return response
    except Exception as e:
        logger.exception("[GOOGLE_OAUTH] Callback failed: %s", e)
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


async def exchange_code_for_google_token(code: str) -> dict:
    """Exchange Google authorization code for access token."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.warning("[GOOGLE_OAUTH] GOOGLE_CLIENT_ID или GOOGLE_CLIENT_SECRET пусты. Проверьте .env и что переменные передаются в контейнер (docker-compose).")
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code != 200:
            try:
                err_body = response.json()
                err_code = err_body.get("error")
                err_desc = err_body.get("error_description", "")
                logger.warning(
                    "[GOOGLE_OAUTH] Token exchange failed: status=%s error=%s description=%s",
                    response.status_code, err_code, err_desc,
                )
                if err_code == "invalid_client":
                    logger.warning(
                        "[GOOGLE_OAUTH] invalid_client: проверьте в Google Cloud Console → Credentials → OAuth 2.0 Client ID (тип Web application). Пересоздайте Client Secret и вставьте в .env без кавычек. В контейнере: client_id len=%s, client_secret len=%s",
                        len(GOOGLE_CLIENT_ID), len(GOOGLE_CLIENT_SECRET),
                    )
            except Exception:
                logger.warning("[GOOGLE_OAUTH] Token exchange failed: status=%s body=%s", response.status_code, response.text[:500])
            # Всегда вывести ответ Google в лог для отладки
            logger.warning("[GOOGLE_OAUTH] Ответ Google: status=%s body=%s", response.status_code, response.text[:400])
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        return response.json()


async def get_google_user_info(access_token: str) -> dict:
    """Get user info from Google API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        return response.json()
