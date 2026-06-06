import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class Sect(Base):
    __tablename__ = "sects"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)
    name = Column(String, nullable=False)
    sect_type = Column(String, nullable=False)
    leader_name = Column(String, default="")
    model_name = Column(String, default="")
    status = Column(String, nullable=False, default="active")  # active, destroyed, annexed, vassal

    # Resources as JSON
    resources_json = Column(Text, nullable=False, default="{}")
    # Stats as JSON
    stats_json = Column(Text, nullable=False, default="{}")
    # Personality as JSON
    personality_json = Column(Text, nullable=False, default="{}")
    # Memory as JSON
    memory_json = Column(Text, nullable=False, default="[]")
    # Controlled regions
    controlled_regions_json = Column(Text, nullable=False, default="[]")

    strategy_summary = Column(Text, default="")
    win_score = Column(Float, default=0.0)
    reliability = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="sects")
    characters = relationship("Character", back_populates="sect", cascade="all, delete-orphan")
