from pydantic_settings import BaseSettings

class FeishuSettings(BaseSettings):
    FEISHU_ENABLED: bool = False
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_BOT_NAME: str = "AI Agent Bot"
    FEISHU_WEBHOOK_VERIFICATION_TOKEN: str = ""

    class Config:
        env_file = ".env"

feishu_settings = FeishuSettings()