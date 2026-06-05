"""
Character Model - 角色系统
每个宗门有关键人物：掌门、长老、圣子/圣女、弟子、暗子等
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class Character(Base):
    __tablename__ = "characters"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)
    sect_id = Column(String, ForeignKey("sects.id"), nullable=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="disciple")  # leader, elder, heir, disciple, spy, prisoner, traitor, wanderer
    realm = Column(String, default="炼气")  # 炼气, 筑基, 金丹, 元婴, 化神, 炼虚, 合体, 大乘, 渡劫
    cultivation = Column(Integer, default=1)
    talent = Column(Integer, default=50)  # 0-100
    loyalty = Column(Float, default=0.5)  # 0-1
    ambition = Column(Float, default=0.5)  # 0-1
    combat_power = Column(Integer, default=10)
    luck = Column(Float, default=0.5)  # 气运
    status = Column(String, default="active")  # active, injured, captured, dead, betrayed, ascended
    traits_json = Column(Text, default="[]")  # 性格标签
    relationships_json = Column(Text, default="{}")  # 人际关系
    inventory_json = Column(Text, default="[]")  # 物品
    story_flags_json = Column(Text, default="[]")  # 剧情标记
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="characters")
    sect = relationship("Sect", back_populates="characters")
