"""
Agent Model Binding - 宗门/Agent 与模型绑定
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class AgentModelBinding(Base):
    __tablename__ = "agent_model_bindings"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, nullable=True)
    sect_id = Column(String, nullable=True)
    agent_role = Column(String, nullable=False)  # sect_master, war_advisor, diplomacy_advisor, economy_advisor, narrator, judge
    provider_id = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    locked = Column(Boolean, nullable=False, default=False)
    fallback_chain_json = Column(Text, default="[]")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
