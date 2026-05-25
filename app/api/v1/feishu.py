from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.feishu_service import feishu_service
from app.services.model_gateway import model_gateway
import json

router = APIRouter()

class FeishuMessageEvent(BaseModel):
    schema: str = "2.0"
    header: dict
    event: dict

@router.get("/webhook")
def feishu_webhook_verify(
    challenge: str = None,
    token: str = None,
    type: str = None
):
    if not feishu_service.enabled:
        raise HTTPException(status_code=400, detail="Feishu is not enabled")

    result = feishu_service.verify_webhook(challenge, token, type)
    if result:
        return JSONResponse(content=result)
    raise HTTPException(status_code=400, detail="Verification failed")

@router.post("/webhook")
async def feishu_webhook_event(request: Request):
    if not feishu_service.enabled:
        raise HTTPException(status_code=400, detail="Feishu is not enabled")

    body = await request.json()
    header = body.get("header", {})
    event_type = header.get("event_type")

    if event_type == "im.message.receive_v1":
        event = body.get("event", {})
        message = event.get("message", {})
        sender = event.get("sender", {})

        if message.get("msg_type") != "text":
            return {"code": 0}

        open_id = sender.get("open_id")
        content = json.loads(message.get("content", "{}"))
        text = content.get("text", "").strip()

        if text.startswith("/"):
            command = text[1:].split()
            if command[0] == "help":
                help_text = "AI Agent Bot commands:\n/help - Show this help\n/chat <message> - Chat with AI\n/models - List available models"
                await feishu_service.send_text_message(open_id, help_text)
            elif command[0] == "models":
                models_text = "Available models:\n- MiniMax\n- DeepSeek\n- GPT-4"
                await feishu_service.send_text_message(open_id, models_text)
            elif command[0] == "chat" and len(command) > 1:
                user_message = " ".join(command[1:])
                try:
                    response = await model_gateway.chat("minimax", [{"role": "user", "content": user_message}])
                    await feishu_service.send_text_message(open_id, response)
                except Exception as e:
                    await feishu_service.send_text_message(open_id, f"Error: {str(e)}")
            else:
                await feishu_service.send_text_message(open_id, "Unknown command. Type /help for help.")
        else:
            try:
                response = await model_gateway.chat("minimax", [{"role": "user", "content": text}])
                await feishu_service.send_text_message(open_id, response)
            except Exception as e:
                await feishu_service.send_text_message(open_id, f"Error: {str(e)}")

    return {"code": 0}

@router.get("/config")
def get_feishu_config():
    return {
        "enabled": feishu_service.enabled,
        "bot_name": feishu_service.bot_name if feishu_service.enabled else None
    }