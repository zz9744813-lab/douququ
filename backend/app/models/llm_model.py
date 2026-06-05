"""
LLM Model Model - 模型列表
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(String, primary_key=True, default=gen_id)
    provider_id = Column(String, ForeignKey("llm_providers.id"), nullable=False)
    model_name = Column(String, nullable=False)
    display_name = Column(String)
    model_type = Column(String, nullable=False, default="chat")
    context_window = Column(Integer, default=128000)
    input_price_per_1m = Column(Float, default=0)
    output_price_per_1m = Column(Float, default=0)
    enabled = Column(Boolean, nullable=False, default=True)
    role_tags_json = Column(Text, default="[]")
    quality_score = Column(Float, default=0)
    speed_score = Column(Float, default=0)
    stability_score = Column(Float, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    provider = relationship("LLMProvider", back_populates="models")
