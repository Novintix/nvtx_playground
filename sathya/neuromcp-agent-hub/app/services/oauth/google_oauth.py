# app/services/oauth/google_oauth.py
import urllib.parse
import httpx

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def build_google_login_url(client_id: str, redirect_uri: str, state: str):
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "prompt": "consent",
        "state": state
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


async def exchange_google_code(code: str, client_id: str, client_secret: str, redirect_uri: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        data = resp.json()

        if "error" in data:
            raise RuntimeError(data)

        return data["access_token"], data.get("refresh_token", "")


async def refresh_google_token(refresh_token: str, client_id: str, client_secret: str):
    """
    Refresh an expired Google OAuth access token using the refresh token
    
    Args:
        refresh_token: The refresh token from the initial OAuth flow
        client_id: Google OAuth client ID
        client_secret: Google OAuth client secret
    
    Returns:
        New access token (refresh token remains the same)
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token"
            }
        )
        data = resp.json()

        if "error" in data:
            raise RuntimeError(f"Token refresh failed: {data.get('error_description', data.get('error'))}")

        return data["access_token"]