import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class Region(Base):
    __tablename__ = "regions"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)
    name = Column(String, nullable=False)
    region_type = Column(String, nullable=False)
    owner_sect_id = Column(String, nullable=True)
    resource_level = Column(Integer, default=1)
    defense_level = Column(Integer, default=1)
    stability = Column(Float, default=1.0)
    neighbors_json = Column(Text, nullable=False, default="[]")
    special_flags_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="regions")