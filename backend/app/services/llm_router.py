"""
LLMRouter - 模型路由 + fallback + 日志记录
根据 world_id / sect_id / agent_role 找绑定模型
"""
import json
import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
from app.models.agent_binding import AgentModelBinding
from app.models.llm_call_log import LLMCallLog
from app.models.model_performance import ModelPerformanceStats
from app.services.llm_client import LLMClient, LLMClientError


class LLMRouter:
    """LLM 路由：负责模型选择、调用、fallback、日志"""

    def __init__(self, db: Session):
        self.db = db
        self.client = LLMClient()

    async def run_agent(
        self,
        world_id: str,
        sect_id: str,
        agent_role: str,
        messages: list[dict],
        schema: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        """
        为 Agent 运行 LLM 调用。
        1. 查找绑定模型
        2. 构建候选链
        3. 逐个尝试直到成功
        4. 记录日志
        5. 返回解析后的结果
        """
        binding = self._find_binding(world_id, sect_id, agent_role)
        candidates = self._build_candidate_chain(binding)

        last_error = None
        for candidate in candidates:
            provider, model, temp, max_tok = candidate
            start_time = asyncio.get_event_loop().time()
            try:
                result = await self.client.chat_json(
                    provider=provider,
                    model=model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=max_tok,
                    timeout=provider.timeout_seconds,
                )
                latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

                # 记录成功日志
                self._log_call(
                    world_id=world_id,
                    sect_id=sect_id,
                    provider_id=provider.id,
                    model_id=model.id,
                    agent_role=agent_role,
                    messages=messages,
                    result=result,
                    success=True,
                    latency_ms=latency_ms,
                )

                # 更新模型统计
                self._update_stats(model.id, world_id, success=True, latency_ms=latency_ms)

                return result["parsed"]

            except LLMClientError as e:
                latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
                last_error = e

                # 记录失败日志
                self._log_call(
                    world_id=world_id,
                    sect_id=sect_id,
                    provider_id=provider.id,
                    model_id=model.id,
                    agent_role=agent_role,
                    messages=messages,
                    result={},
                    success=False,
                    latency_ms=latency_ms,
                    error_message=str(e),
                )

                # 更新模型统计
                self._update_stats(model.id, world_id, success=False, latency_ms=latency_ms, error=str(e))

                # 如果 locked，不再尝试 fallback
                if binding and binding.locked:
                    break

        # 所有候选都失败
        return {
            "error": "所有模型调用失败",
            "fallback": True,
            "last_error": str(last_error) if last_error else "未知错误",
        }

    def _find_binding(
        self, world_id: str, sect_id: str, agent_role: str
    ) -> AgentModelBinding | None:
        """查找最精确的绑定配置"""
        # 1. 精确匹配 world + sect + role
        binding = self.db.query(AgentModelBinding).filter(
            AgentModelBinding.world_id == world_id,
            AgentModelBinding.sect_id == sect_id,
            AgentModelBinding.agent_role == agent_role,
        ).first()
        if binding:
            return binding

        # 2. 匹配 world + sect + sect_master（默认主角色）
        if agent_role != "sect_master":
            binding = self.db.query(AgentModelBinding).filter(
                AgentModelBinding.world_id == world_id,
                AgentModelBinding.sect_id == sect_id,
                AgentModelBinding.agent_role == "sect_master",
            ).first()
            if binding:
                return binding

        # 3. 匹配 world + role（全局默认）
        binding = self.db.query(AgentModelBinding).filter(
            AgentModelBinding.world_id == world_id,
            AgentModelBinding.sect_id.is_(None),
            AgentModelBinding.agent_role == agent_role,
        ).first()
        if binding:
            return binding

        # 4. 匹配 world + sect_master（全局默认主角色）
        binding = self.db.query(AgentModelBinding).filter(
            AgentModelBinding.world_id == world_id,
            AgentModelBinding.sect_id.is_(None),
            AgentModelBinding.agent_role == "sect_master",
        ).first()

        return binding

    def _build_candidate_chain(
        self, binding: AgentModelBinding | None
    ) -> list[tuple[LLMProvider, LLMModel, float, int]]:
        """构建候选模型链"""
        candidates = []

        if binding:
            # 主模型
            provider = self.db.query(LLMProvider).filter(
                LLMProvider.id == binding.provider_id,
                LLMProvider.enabled == True,
            ).first()
            model = self.db.query(LLMModel).filter(
                LLMModel.id == binding.model_id,
                LLMModel.enabled == True,
            ).first()
            if provider and model:
                candidates.append((
                    provider,
                    model,
                    binding.temperature,
                    binding.max_tokens,
                ))

            # fallback 链
            if binding.fallback_chain_json:
                try:
                    fallback_ids = json.loads(binding.fallback_chain_json)
                    for model_id in fallback_ids:
                        model = self.db.query(LLMModel).filter(
                            LLMModel.id == model_id,
                            LLMModel.enabled == True,
                        ).first()
                        if model:
                            provider = self.db.query(LLMProvider).filter(
                                LLMProvider.id == model.provider_id,
                                LLMProvider.enabled == True,
                            ).first()
                            if provider:
                                candidates.append((
                                    provider,
                                    model,
                                    binding.temperature,
                                    binding.max_tokens,
                                ))
                except json.JSONDecodeError:
                    pass

        # 如果没有绑定或绑定失效，使用全局默认模型
        if not candidates:
            default_model = self.db.query(LLMModel).filter(
                LLMModel.enabled == True,
            ).order_by(LLMModel.quality_score.desc()).first()
            if default_model:
                provider = self.db.query(LLMProvider).filter(
                    LLMProvider.id == default_model.provider_id,
                    LLMProvider.enabled == True,
                ).first()
                if provider:
                    candidates.append((provider, default_model, 0.7, 2000))

        return candidates

    def _log_call(
        self,
        world_id: str,
        sect_id: str,
        provider_id: str,
        model_id: str,
        agent_role: str,
        messages: list[dict],
        result: dict,
        success: bool,
        latency_ms: int,
        error_message: str | None = None,
    ):
        """记录调用日志"""
        import hashlib
        prompt_text = json.dumps(messages, ensure_ascii=False)
        prompt_hash = hashlib.md5(prompt_text.encode()).hexdigest()[:16]

        usage = result.get("usage", {})
        estimated_cost = self._estimate_cost(
            model_id,
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )

        log = LLMCallLog(
            world_id=world_id,
            sect_id=sect_id,
            provider_id=provider_id,
            model_id=model_id,
            agent_role=agent_role,
            prompt_hash=prompt_hash,
            prompt_preview=prompt_text[:500],
            raw_output=result.get("raw_content", "")[:2000],
            parsed_output_json=json.dumps(result.get("parsed", {}), ensure_ascii=False)[:2000],
            success=success,
            error_message=error_message,
            latency_ms=latency_ms,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            estimated_cost=estimated_cost,
        )
        self.db.add(log)
        self.db.commit()

    def _update_stats(
        self,
        model_id: str,
        world_id: str,
        success: bool,
        latency_ms: int,
        error: str | None = None,
    ):
        """更新模型性能统计"""
        stats = self.db.query(ModelPerformanceStats).filter(
            ModelPerformanceStats.model_id == model_id,
            ModelPerformanceStats.world_id == world_id,
        ).first()

        if not stats:
            stats = ModelPerformanceStats(model_id=model_id, world_id=world_id)
            self.db.add(stats)

        stats.total_calls += 1
        if success:
            stats.success_calls += 1
        else:
            if error and "timeout" in error.lower():
                stats.timeout_count += 1
            else:
                stats.json_error_count += 1

        # 更新平均延迟
        if stats.avg_latency_ms == 0:
            stats.avg_latency_ms = latency_ms
        else:
            stats.avg_latency_ms = (stats.avg_latency_ms * (stats.total_calls - 1) + latency_ms) / stats.total_calls

        self.db.commit()

    def _estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """估算调用成本"""
        model = self.db.query(LLMModel).filter(LLMModel.id == model_id).first()
        if not model:
            return 0
        input_cost = (input_tokens / 1_000_000) * (model.input_price_per_1m or 0)
        output_cost = (output_tokens / 1_000_000) * (model.output_price_per_1m or 0)
        return round(input_cost + output_cost, 6)

    async def close(self):
        await self.client.close()
