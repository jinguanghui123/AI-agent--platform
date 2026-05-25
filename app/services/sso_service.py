import httpx
import secrets
from typing import Optional, Dict
from app.core.sso import sso_settings
from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash
import urllib.parse

class SSOService:
    def __init__(self):
        self.enabled = sso_settings.SSO_ENABLED
        self.provider = sso_settings.SSO_PROVIDER
        self.client_id = sso_settings.SSO_CLIENT_ID
        self.client_secret = sso_settings.SSO_CLIENT_SECRET
        self.authorize_url = sso_settings.SSO_AUTHORIZE_URL
        self.token_url = sso_settings.SSO_TOKEN_URL
        self.userinfo_url = sso_settings.SSO_USERINFO_URL
        self.redirect_uri = sso_settings.SSO_REDIRECT_URI
        self.scopes = sso_settings.SSO_SCOPES

    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scopes,
            "state": state
        }

        url = f"{self.authorize_url}?{urllib.parse.urlencode(params)}"
        return url, state

    async def exchange_code_for_token(self, code: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri
                }
            )
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code != 200:
                raise Exception(f"User info fetch failed: {response.text}")
            return response.json()

    def get_or_create_user(self, db, user_info: Dict) -> User:
        email = user_info.get("email")
        username = user_info.get("name") or user_info.get("preferred_username") or email.split("@")[0]
        sub = user_info.get("sub")

        user = db.query(User).filter(
            (User.email == email) | (User.sso_provider == self.provider)
        ).first()

        if not user:
            user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                sso_provider=self.provider,
                sso_id=sub
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        elif not user.sso_provider:
            user.sso_provider = self.provider
            user.sso_id = sub
            db.commit()
            db.refresh(user)

        return user

sso_service = SSOService()