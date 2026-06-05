"""
LLMClient - OpenAI-compatible async client
支持 /chat/completions 和 /models
"""
import json
import asyncio
from typing import Any

import httpx

from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel


class LLMClientError(Exception):
    pass


class LLMClient:
    """OpenAI-compatible LLM Client"""

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=120)

    async def chat_json(
        self,
        provider: LLMProvider,
        model: LLMModel,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 60,
        response_format: dict | None = None,
    ) -> dict:
        """
        调用 LLM API，返回结构化 JSON。
        支持 response_format={"type": "json_object"}，如果不支持则通过 prompt 要求 JSON。
        """
        headers = {
            "Authorization": f"Bearer {provider.api_key_encrypted}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": model.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # 如果 provider 支持 json_object 响应格式
        if response_format and response_format.get("type") == "json_object":
            payload["response_format"] = response_format

        url = f"{provider.base_url.rstrip('/')}/chat/completions"

        try:
            resp = await self._client.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException as e:
            raise LLMClientError(f"请求超时 ({timeout}s): {e}")
        except httpx.HTTPStatusError as e:
            raise LLMClientError(f"HTTP {e.response.status_code}: {e.response.text[:500]}")
        except Exception as e:
            raise LLMClientError(f"请求失败: {e}")

        # 提取内容
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise LLMClientError(f"响应格式异常: {e}, raw={data}")

        # 尝试解析 JSON
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # 尝试修复 JSON
            parsed = self._extract_json(content)

        return {
            "parsed": parsed,
            "raw_content": content,
            "usage": data.get("usage", {}),
            "model": model.model_name,
        }

    async def list_models(self, provider: LLMProvider) -> list[dict]:
        """拉取 Provider 的模型列表"""
        headers = {
            "Authorization": f"Bearer {provider.api_key_encrypted}",
        }
        url = f"{provider.base_url.rstrip('/')}/models"

        try:
            resp = await self._client.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception as e:
            raise LLMClientError(f"拉取模型列表失败: {e}")

    async def test_connection(self, provider: LLMProvider) -> dict:
        """测试 Provider 连接"""
        start = asyncio.get_event_loop().time()
        try:
            # 尝试拉取模型列表作为连通性测试
            models = await self.list_models(provider)
            latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)
            return {
                "ok": True,
                "latency_ms": latency_ms,
                "message": "连接成功",
                "models_count": len(models),
            }
        except Exception as e:
            latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)
            return {
                "ok": False,
                "latency_ms": latency_ms,
                "message": str(e),
                "error_type": self._classify_error(str(e)),
            }

    @staticmethod
    def _classify_error(error_msg: str) -> str:
        """分类错误类型"""
        msg = error_msg.lower()
        if "401" in msg or "unauthorized" in msg or "auth" in msg:
            return "auth_error"
        if "timeout" in msg:
            return "timeout"
        if "connection" in msg:
            return "connection_error"
        if "404" in msg:
            return "not_found"
        return "unknown"

    @staticmethod
    def _extract_json(text: str) -> dict:
        """从文本中提取 JSON"""
        # 尝试找 ```json ... ``` 代码块
        import re
        patterns = [
            r"```json\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
            r"(\{.*\})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        # 最后尝试直接解析整个文本
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        return {"error": "无法解析 JSON", "raw": text[:500]}

    async def close(self):
        await self._client.aclose()
