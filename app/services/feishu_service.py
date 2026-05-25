import httpx
import hashlib
import time
import asyncio
from typing import Optional, Dict
from app.core.feishu_config import feishu_settings

class FeishuService:
    def __init__(self):
        self.enabled = feishu_settings.FEISHU_ENABLED
        self.app_id = feishu_settings.FEISHU_APP_ID
        self.app_secret = feishu_settings.FEISHU_APP_SECRET
        self.bot_name = feishu_settings.FEISHU_BOT_NAME
        self.webhook_verification_token = feishu_settings.FEISHU_WEBHOOK_VERIFICATION_TOKEN
        self.api_base = "https://open.feishu.cn/open-apis"

    async def get_access_token(self) -> str:
        url = f"{self.api_base}/auth/v3/tenant_access_token/internal"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret
                }
            )
            data = response.json()
            if data.get("code") != 0:
                raise Exception(f"Failed to get access token: {data}")
            return data.get("tenant_access_token")

    async def send_message(self, receive_id: str, msg_type: str, content: Dict) -> Dict:
        access_token = await self.get_access_token()
        url = f"{self.api_base}/im/v1/messages"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params={"receive_id_type": "open_id"},
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "receive_id": receive_id,
                    "msg_type": msg_type,
                    "content": content
                }
            )
            return response.json()

    async def send_text_message(self, open_id: str, text: str) -> Dict:
        return await self.send_message(
            receive_id=open_id,
            msg_type="text",
            content={"text": text}
        )

    async def reply_message(self, message_id: str, msg_type: str, content: Dict) -> Dict:
        access_token = await self.get_access_token()
        url = f"{self.api_base}/im/v1/messages/{message_id}/reply"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "msg_type": msg_type,
                    "content": content
                }
            )
            return response.json()

    def verify_webhook(self, challenge: str, token: str, type: str) -> Optional[Dict]:
        if type == "url_verification" and token == self.webhook_verification_token:
            return {"challenge": challenge}
        return None

    def decrypt_event(self, header: Dict, event: Dict) -> Dict:
        return event

feishu_service = FeishuService()