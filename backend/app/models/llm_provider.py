"""
LLM Provider Model - API 配置中心
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    provider_type = Column(String, nullable=False, default="openai_compatible")
    base_url = Column(String, nullable=False)
    api_key_encrypted = Column(Text, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)
    timeout_seconds = Column(Integer, nullable=False, default=60)
    max_retries = Column(Integer, nullable=False, default=2)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")
