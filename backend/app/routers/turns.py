"""Turns API Router"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.simulation_engine import SimulationEngine
from app.models.world import World

router = APIRouter(prefix="/api/worlds", tags=["turns"])


class TurnResult(BaseModel):
    turn: int
    world_status: str
    actions_count: int
    results_count: int
    events_count: int
    summary: str


@router.post("/{world_id}/turns/next", response_model=TurnResult)
def advance_turn(world_id: str, db: Session = Depends(get_db)):
    """推进一个回合"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    if world.status == "finished":
        raise HTTPException(status_code=400, detail="世界已结束")

    engine = SimulationEngine(db)
    result = engine.run_turn(world_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{world_id}/turns/auto-run")
def auto_run(world_id: str, turns: int = 10, db: Session = Depends(get_db)):
    """自动运行多个回合"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    if world.status == "finished":
        raise HTTPException(status_code=400, detail="世界已结束")

    results = []
    engine = SimulationEngine(db)
    for _ in range(min(turns, 50)):
        if world.status == "finished":
            break
        result = engine.run_turn(world_id)
        if "error" in result:
            break
        results.append(result)
        # Refresh world
        db.refresh(world)
    return {"turns_run": len(results), "results": results}


@router.post("/{world_id}/turns/pause")
def pause_world(world_id: str, db: Session = Depends(get_db)):
    """暂停世界"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    world.status = "paused"
    db.commit()
    return {"ok": True, "status": "paused"}


@router.post("/{world_id}/turns/resume")
def resume_world(world_id: str, db: Session = Depends(get_db)):
    """恢复世界"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    world.status = "running"
    db.commit()
    return {"ok": True, "status": "running"}