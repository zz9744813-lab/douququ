"""
Diplomacy Proposal Model - 外交提案模型
记录宗门间的外交提案、密约、背刺等互动
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class DiplomacyProposal(Base):
    __tablename__ = "diplomacy_proposals"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)
    turn = Column(Integer, nullable=False, default=0)

    # 提案方
    from_sect_id = Column(String, nullable=False)
    from_sect_name = Column(String, default="")

    # 目标方
    to_sect_id = Column(String, nullable=False)
    to_sect_name = Column(String, default="")

    # 提案类型: trade, non_aggression, alliance, vassal, secret_pact, betrayal, ceasefire, threat
    proposal_type = Column(String, nullable=False)

    # 提案内容
    title = Column(String, default="")
    description = Column(Text, default="")

    # 条件与代价
    conditions_json = Column(Text, nullable=False, default="{}")
    # 例如: {"duration_turns": 5, "resource_cost": {"spirit_stones": 100}, "territory_transfer": []}

    # 状态: pending, accepted, rejected, expired, betrayed, cancelled
    status = Column(String, nullable=False, default="pending")

    # 响应内容
    response_message = Column(Text, default="")
    response_turn = Column(Integer, nullable=True)

    # 是否为密约（不公开显示）
    is_secret = Column(Boolean, default=False)

    # 背叛相关
    betrayed_by = Column(String, nullable=True)  # 背叛方 sect_id
    betrayal_turn = Column(Integer, nullable=True)
    betrayal_reason = Column(Text, default="")

    # 成功率（计算值）
    success_rate = Column(Float, default=0.5)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="diplomacy_proposals")
