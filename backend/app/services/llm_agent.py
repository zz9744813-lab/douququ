"""
LLM Agent - LLM 驱动的宗门 Agent
使用 LLM 生成宗门行动决策。
"""
import json
from typing import Any

from app.services.llm_service import LLMService
from app.prompts.sect_agent import build_sect_prompt, SECT_SYSTEM_PROMPT
from app.services.default_ai import DefaultAI


class LLMAgent:
    """LLM Agent：使用大模型生成宗门行动"""

    def __init__(self):
        self.llm = LLMService()
        self.default_ai = DefaultAI()

    async def generate_actions(
        self,
        sect: dict,
        world_state: dict,
        max_actions: int = 3,
    ) -> dict:
        """
        使用 LLM 生成宗门行动。
        如果 LLM 调用失败，回退到默认 AI。
        """
        turn = world_state.get("turn", 1)
        user_prompt = build_sect_prompt(sect, world_state, turn)

        result = await self.llm.generate_json(
            system_prompt=SECT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema={
                "type": "object",
                "properties": {
                    "strategy_summary": {"type": "string"},
                    "actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "intensity": {"type": "string", "enum": ["low", "medium", "high"]},
                                "target_sect_id": {"type": "string"},
                                "target_region_id": {"type": "string"},
                                "offer_type": {"type": "string"},
                                "message": {"type": "string"},
                            },
                        },
                    },
                },
                "required": ["strategy_summary", "actions"],
            },
        )

        if result["success"] and result["data"]:
            data = result["data"]
            actions = data.get("actions", [])
            # 验证行动点
            total_cost = 0
            valid_actions = []
            for action in actions:
                action_type = action.get("type", "")
                cost = self.default_ai.ACTION_COSTS.get(action_type, 1)
                if total_cost + cost <= max_actions:
                    valid_actions.append(action)
                    total_cost += cost

            return {
                "strategy_summary": data.get("strategy_summary", "LLM 决策"),
                "actions": valid_actions,
                "source": "llm",
                "raw_response": result.get("raw_content", ""),
            }
        else:
            # LLM 失败，回退到默认 AI
            fallback = self.default_ai.generate_actions(sect, world_state, max_actions)
            fallback["source"] = "fallback"
            fallback["llm_error"] = result.get("error", "")
            return fallback

    def close(self):
        self.llm.close()
