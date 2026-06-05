"""
LLM Service - LLM 服务层
统一封装 LLM 调用，支持多 Provider（OpenAI / Claude / 本地模型）。
提供 Prompt 组装、JSON 解析、重试退避、超时控制。
"""
import json
import random
import asyncio
from typing import Any

import httpx

from app.core.config import settings


class LLMService:
    """LLM 服务：统一调用接口"""

    def __init__(self):
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        """
        调用 LLM 生成内容。
        返回: {success, content, raw_response, error}
        """
        if not self.api_key:
            return {
                "success": False,
                "content": None,
                "raw_response": None,
                "error": "LLM API key 未配置",
            }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {
                "success": True,
                "content": content,
                "raw_response": data,
                "error": None,
            }
        except httpx.TimeoutException:
            return {
                "success": False,
                "content": None,
                "raw_response": None,
                "error": "LLM 调用超时",
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "content": None,
                "raw_response": e.response.text,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "raw_response": None,
                "error": str(e),
            }

    async def generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
        temperature: float | None = None,
    ) -> dict:
        """带重试的 LLM 调用，指数退避"""
        for attempt in range(max_retries):
            result = await self.generate(system_prompt, user_prompt, temperature)
            if result["success"]:
                return result
            # 指数退避
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(wait_time)
        return result

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict | None = None,
    ) -> dict:
        """
        调用 LLM 并解析 JSON 输出。
        如果解析失败，尝试修复 JSON。
        返回: {success, data, raw_content, error}
        """
        # 在 system prompt 中注入 JSON 格式要求
        json_prompt = system_prompt + "\n\n你必须以纯 JSON 格式输出，不要包含 markdown 代码块标记（如 ```json）。"
        if schema:
            json_prompt += f"\n\nJSON Schema: {json.dumps(schema, ensure_ascii=False)}"

        result = await self.generate_with_retry(json_prompt, user_prompt)
        if not result["success"]:
            return {
                "success": False,
                "data": None,
                "raw_content": result.get("content"),
                "error": result["error"],
            }

        content = result["content"]
        # 清理可能的 markdown 代码块
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            # 去掉第一行和最后一行
            if len(lines) > 2:
                content = "\n".join(lines[1:-1])
            else:
                content = content.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(content)
            return {
                "success": True,
                "data": data,
                "raw_content": result["content"],
                "error": None,
            }
        except json.JSONDecodeError as e:
            # 尝试修复 JSON
            fixed = self._fix_json(content)
            if fixed:
                try:
                    data = json.loads(fixed)
                    return {
                        "success": True,
                        "data": data,
                        "raw_content": result["content"],
                        "error": None,
                    }
                except json.JSONDecodeError:
                    pass
            return {
                "success": False,
                "data": None,
                "raw_content": result["content"],
                "error": f"JSON 解析失败: {str(e)}",
            }

    @staticmethod
    def _fix_json(text: str) -> str | None:
        """尝试修复常见 JSON 错误"""
        # 去掉尾部逗号
        text = text.rstrip()
        if text.endswith(","):
            text = text[:-1]
        # 补齐缺失的括号
        open_braces = text.count("{") - text.count("}")
        open_brackets = text.count("[") - text.count("]")
        text += "}" * open_braces
        text += "]" * open_brackets
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            return None

    def close(self):
        """关闭 HTTP 客户端"""
        asyncio.create_task(self.client.aclose())
