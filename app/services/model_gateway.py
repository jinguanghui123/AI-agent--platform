from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings

class BaseModelAdapter(ABC):
    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        pass

class MiniMaxAdapter(BaseModelAdapter):
    def __init__(self):
        self.api_key = settings.MINIMAX_API_KEY
        self.base_url = settings.MINIMAX_BASE_URL

    def _format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化消息，支持多模态内容"""
        formatted = []
        for msg in messages:
            if isinstance(msg.get("content"), list):
                # 多模态消息直接传递
                formatted.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            else:
                # 文本消息
                formatted.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        return formatted

    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        if not self.api_key:
            return "MiniMax API密钥未配置，请联系管理员设置 MINIMAX_API_KEY 环境变量"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 格式化消息（支持多模态）
        formatted_messages = self._format_messages(messages)

        data = {
            "model": "MiniMax-M2",
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096)
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/text/chatcompletion_v2",
                headers=headers,
                json=data
            )
            result = response.json()
            if result.get("choices") is None:
                base_resp = result.get("base_resp", {})
                error_msg = base_resp.get("status_msg", "未知错误")
                raise Exception(f"MiniMax API错误: {error_msg}")
            return result["choices"][0]["message"]["content"]

class DeepSeekAdapter(BaseModelAdapter):
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.api_key:
            return "DeepSeek API密钥未配置，请联系管理员设置 DEEPSEEK_API_KEY 环境变量"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048)
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

class OpenAIAdapter(BaseModelAdapter):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.api_key:
            return "OpenAI API密钥未配置，请联系管理员设置 OPENAI_API_KEY 环境变量"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-4",
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048)
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

class ModelGateway:
    def __init__(self):
        self.adapters: Dict[str, BaseModelAdapter] = {
            "minimax": MiniMaxAdapter(),
            "deepseek": DeepSeekAdapter(),
            "openai": OpenAIAdapter(),
        }
        self.default_model = "minimax"

    async def chat(self, model_id: str, messages: List[Dict[str, str]], **kwargs) -> str:
        adapter = self.adapters.get(model_id, self.adapters[self.default_model])
        return await adapter.chat(messages, **kwargs)

    def list_models(self) -> List[Dict[str, str]]:
        models = [
            {"id": "minimax", "name": "MiniMax", "provider": "MiniMax"},
            {"id": "deepseek", "name": "DeepSeek", "provider": "DeepSeek"},
            {"id": "openai", "name": "GPT-4", "provider": "OpenAI"},
        ]
        return models

model_gateway = ModelGateway()