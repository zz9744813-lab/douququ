import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class DiplomacyRelation(Base):
    __tablename__ = "diplomacy_relations"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)
    sect_a_id = Column(String, nullable=False)
    sect_b_id = Column(String, nullable=False)
    relation_type = Column(String, nullable=False, default="neutral")  # neutral, friendly, trade, non_aggression, alliance, vassal, hostile, war, mortal_enemy
    relation_score = Column(Float, default=0.0)
    trust_score = Column(Float, default=0.5)
    treaties_json = Column(Text, nullable=False, default="[]")
    history_json = Column(Text, nullable=False, default="[]")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="diplomacy_relations")