import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class Battle(Base):
    __tablename__ = "battles"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)
    turn = Column(Integer, nullable=False)
    attacker_sect_id = Column(String, nullable=False)
    defender_sect_id = Column(String, nullable=False)
    region_id = Column(String, nullable=True)
    result_type = Column(String, nullable=False)  # decisive_victory, victory, stalemate, defeat, crushing_defeat
    winner_sect_id = Column(String, nullable=True)
    attacker_power = Column(Float, default=0.0)
    defender_power = Column(Float, default=0.0)
    losses_json = Column(Text, nullable=False, default="{}")
    rewards_json = Column(Text, nullable=False, default="{}")
    battle_log = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="battles")