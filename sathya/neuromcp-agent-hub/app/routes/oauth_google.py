from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import os

from app.services.oauth.google_oauth import build_google_login_url, exchange_google_code
from app.services.oauth.token_store import upsert_token
from app.utils.session import sign_state, unsign_state

router = APIRouter(prefix="/auth/google")

@router.get("/login")
async def google_login():
    redirect_uri = os.getenv("APP_BASE_URL") + "/auth/google/callback"
    state = sign_state({"provider": "google"})

    url = build_google_login_url(os.getenv("GOOGLE_CLIENT_ID"), redirect_uri, state)
    return RedirectResponse(url)

@router.get("/callback")
async def google_callback(code: str, state: str):
    unsign_state(state)

    redirect_uri = os.getenv("APP_BASE_URL") + "/auth/google/callback"

    access_token, refresh_token = await exchange_google_code(
        code,
        os.getenv("GOOGLE_CLIENT_ID"),
        os.getenv("GOOGLE_CLIENT_SECRET"),
        redirect_uri
    )

    await upsert_token("google", access_token, refresh_token)

    return {"ok": True, "message": "Google Calendar connected ✅"}
