from pydantic_settings import BaseSettings
from typing import Optional

class SSOSettings(BaseSettings):
    SSO_ENABLED: bool = False
    SSO_PROVIDER: str = "generic"  # generic, okta, azure, feishu
    SSO_CLIENT_ID: str = ""
    SSO_CLIENT_SECRET: str = ""
    SSO_AUTHORIZE_URL: str = ""
    SSO_TOKEN_URL: str = ""
    SSO_USERINFO_URL: str = ""
    SSO_REDIRECT_URI: str = ""
    SSO_SCOPES: str = "openid profile email"

    class Config:
        env_file = ".env"

sso_settings = SSOSettings()