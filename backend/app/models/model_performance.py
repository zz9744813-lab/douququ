"""
Model Performance Stats - 模型表现统计
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class ModelPerformanceStats(Base):
    __tablename__ = "model_performance_stats"

    id = Column(String, primary_key=True, default=gen_id)
    model_id = Column(String, nullable=False)
    world_id = Column(String, nullable=True)
    total_calls = Column(Integer, default=0)
    success_calls = Column(Integer, default=0)
    json_error_count = Column(Integer, default=0)
    timeout_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0)
    total_cost = Column(Float, default=0)
    win_count = Column(Integer, default=0)
    lose_count = Column(Integer, default=0)
    diplomacy_score = Column(Float, default=0)
    war_score = Column(Float, default=0)
    economy_score = Column(Float, default=0)
    survival_score = Column(Float, default=0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
