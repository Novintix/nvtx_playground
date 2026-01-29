from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
import os

from app.services.oauth.google_oauth import build_google_login_url, exchange_google_code
from app.services.oauth.token_store import upsert_token
from app.utils.session import sign_state, unsign_state

router = APIRouter(prefix="/auth/google")

@router.get("/debug")
async def debug_config():
    """Debug endpoint to verify OAuth configuration"""
    app_base_url = os.getenv("APP_BASE_URL")
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = app_base_url + "/auth/google/callback"
    
    return {
        "app_base_url": app_base_url,
        "client_id": client_id[:20] + "..." if client_id else None,
        "redirect_uri": redirect_uri,
        "instructions": {
            "1": "Verify APP_BASE_URL has NO trailing slash",
            "2": f"In Google Cloud Console, add this exact URL to Authorized redirect URIs: {redirect_uri}",
            "3": "Make sure GOOGLE_CLIENT_ID matches your Google Cloud project",
            "4": "After fixing, visit /auth/google/login"
        }
    }

@router.get("/login")
async def google_login():
    redirect_uri = os.getenv("APP_BASE_URL") + "/auth/google/callback"
    state = sign_state({"provider": "google"})

    url = build_google_login_url(os.getenv("GOOGLE_CLIENT_ID"), redirect_uri, state)
    return RedirectResponse(url)

@router.get("/callback")
async def google_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    # Handle OAuth errors from Google
    if error:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": f"Google OAuth error: {error}"}
        )
    
    # Check if required parameters are present
    if not code or not state:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": "Missing required parameters",
                "message": "Please start the OAuth flow by visiting /auth/google/login"
            }
        )

    try:
        unsign_state(state)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": f"Invalid state parameter: {str(e)}"}
        )

    redirect_uri = os.getenv("APP_BASE_URL") + "/auth/google/callback"

    try:
        access_token, refresh_token = await exchange_google_code(
            code,
            os.getenv("GOOGLE_CLIENT_ID"),
            os.getenv("GOOGLE_CLIENT_SECRET"),
            redirect_uri
        )

        await upsert_token("google", {
            "access_token": access_token,
            "refresh_token": refresh_token
        })

        return {"ok": True, "message": "Google Calendar connected ✅"}
    
    except RuntimeError as e:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": "Failed to exchange authorization code",
                "details": str(e),
                "hint": "The authorization code may have expired or already been used. Please try /auth/google/login again."
            }
        )
