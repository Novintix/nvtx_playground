import urllib.parse
import httpx

SLACK_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
SLACK_TOKEN_URL = "https://slack.com/api/oauth.v2.access"


def build_slack_login_url(client_id: str, redirect_uri: str, state: str):
    params = {
        "client_id": client_id,
        "scope": "chat:write",
        "redirect_uri": redirect_uri,
        "state": state
    }
    return f"{SLACK_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


async def exchange_slack_code(code: str, client_id: str, client_secret: str, redirect_uri: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            SLACK_TOKEN_URL,
            data={
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(data)

        return data["access_token"]
