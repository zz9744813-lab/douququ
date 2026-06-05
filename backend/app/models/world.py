import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class World(Base):
    __tablename__ = "worlds"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, nullable=False, default="created")  # created, running, paused, finished
    current_turn = Column(Integer, nullable=False, default=0)
    max_turns = Column(Integer, nullable=True)
    world_seed = Column(Integer, nullable=False, default=42)
    mode = Column(String, nullable=False, default="season")  # season, sandbox, scenario, model_battle
    rules_json = Column(Text, nullable=False, default="{}")
    map_size = Column(String, default="medium")
    sect_count = Column(Integer, default=8)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    sects = relationship("Sect", back_populates="world", cascade="all, delete-orphan")
    regions = relationship("Region", back_populates="world", cascade="all, delete-orphan")
    events = relationship("WorldEvent", back_populates="world", cascade="all, delete-orphan")
    turn_records = relationship("TurnRecord", back_populates="world", cascade="all, delete-orphan")
    battles = relationship("Battle", back_populates="world", cascade="all, delete-orphan")
    diplomacy_relations = relationship("DiplomacyRelation", back_populates="world", cascade="all, delete-orphan")
    diplomacy_proposals = relationship("DiplomacyProposal", back_populates="world", cascade="all, delete-orphan")
    audience_predictions = relationship("AudiencePrediction", back_populates="world", cascade="all, delete-orphan")
    audience_interventions = relationship("AudienceIntervention", back_populates="world", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="world", cascade="all, delete-orphan")
