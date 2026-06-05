import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class TurnRecord(Base):
    __tablename__ = "turn_records"

    id = Column(String, primary_key=True, default=gen_id)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)
    turn = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, running, completed, failed
    input_snapshot_json = Column(Text, nullable=False, default="{}")
    agent_actions_json = Column(Text, nullable=False, default="{}")
    resolved_results_json = Column(Text, nullable=False, default="{}")
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="turn_records")