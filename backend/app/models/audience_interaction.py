"""
Audience Interaction Model - 玩家天道互动模型
记录玩家预测、干预、打赏等互动行为
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class AudiencePrediction(Base):
    __tablename__ = "audience_predictions"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)
    user_id = Column(String, nullable=False, default="anonymous")  # 玩家标识

    # 预测内容
    prediction_type = Column(String, nullable=False)  # winner(最终赢家), next_war(下回合战争), annexation(吞并), alliance(结盟)
    target_sect_id = Column(String, nullable=True)  # 预测目标宗门
    target_sect_name = Column(String, default="")
    predicted_turn = Column(Integer, nullable=True)  # 预测发生的回合

    # 预测状态
    status = Column(String, nullable=False, default="pending")  # pending, correct, wrong, cancelled
    resolved_turn = Column(Integer, nullable=True)
    reward_points = Column(Integer, default=0)  # 预测正确奖励积分

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="audience_predictions")


class AudienceIntervention(Base):
    __tablename__ = "audience_interventions"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)
    turn = Column(Integer, nullable=False)
    user_id = Column(String, nullable=False, default="anonymous")

    # 干预类型
    intervention_type = Column(String, nullable=False)
    # bless(天佑), curse(天罚), resource_rain(资源雨), revelation(天机启示), disaster(天灾)

    # 目标
    target_sect_id = Column(String, nullable=True)
    target_sect_name = Column(String, default="")
    target_region_id = Column(String, nullable=True)

    # 干预内容
    title = Column(String, default="")
    description = Column(Text, default="")

    # 效果
    effects_json = Column(Text, nullable=False, default="{}")
    # 例如: {"military_power": +20, "spirit_stones": +500, "stability": -0.1}

    # 消耗与奖励
    cost_points = Column(Integer, default=0)
    popularity_gain = Column(Integer, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="audience_interventions")
