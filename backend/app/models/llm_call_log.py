"""
LLM Call Log - 模型调用日志（用于斗蛐蛐统计）
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class LLMCallLog(Base):
    __tablename__ = "llm_call_logs"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, nullable=True)
    sect_id = Column(String, nullable=True)
    provider_id = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    agent_role = Column(String, nullable=False)
    prompt_hash = Column(String)
    prompt_preview = Column(Text)
    raw_output = Column(Text)
    parsed_output_json = Column(Text)
    success = Column(Boolean)
    error_message = Column(Text)
    latency_ms = Column(Integer)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
