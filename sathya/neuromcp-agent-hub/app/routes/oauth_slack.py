from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import os

from app.services.oauth.slack_oauth import build_slack_login_url, exchange_slack_code
from app.services.oauth.token_store import upsert_token
from app.utils.session import sign_state, unsign_state

router = APIRouter(prefix="/auth/slack")

@router.get("/login")
async def slack_login():
    redirect_uri = os.getenv("APP_BASE_URL") + "/auth/slack/callback"
    state = sign_state({"provider": "slack"})

    url = build_slack_login_url(os.getenv("SLACK_CLIENT_ID"), redirect_uri, state)
    return RedirectResponse(url)

@router.get("/callback")
async def slack_callback(code: str, state: str):
    unsign_state(state)

    redirect_uri = os.getenv("APP_BASE_URL") + "/auth/slack/callback"

    token = await exchange_slack_code(
        code,
        os.getenv("SLACK_CLIENT_ID"),
        os.getenv("SLACK_CLIENT_SECRET"),
        redirect_uri
    )

    await upsert_token("slack", token)

    return {"ok": True, "message": "Slack connected ✅"}
