"""Audience Interaction API Router"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.audience_engine import AudienceEngine
from app.services.scoring_engine import ScoringEngine
from app.models.world import World
from app.models.sect import Sect
from app.models.battle import Battle
from app.models.diplomacy import DiplomacyRelation

router = APIRouter(prefix="/api/worlds", tags=["audience"])


class InterveneRequest(BaseModel):
    action_type: str = Field(..., description="干预类型")
    target_sect_id: str | None = Field(default=None)
    target_region_id: str | None = Field(default=None)


class PredictRequest(BaseModel):
    prediction_type: str = Field(..., description="预测类型")
    target_id: str = Field(..., description="预测目标ID")
    predicted_result: str = Field(..., description="预测结果")


@router.post("/{world_id}/audience/intervene")
def audience_intervene(world_id: str, req: InterveneRequest, db: Session = Depends(get_db)):
    """天道干预"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")

    # 加载世界状态
    sects = db.query(Sect).filter(Sect.world_id == world_id, Sect.status == "active").all()
    sect_states = {}
    for s in sects:
        sect_states[s.id] = {
            "id": s.id,
            "name": s.name,
            "status": s.status,
            "resources": json.loads(s.resources_json or "{}"),
            "stats": json.loads(s.stats_json or "{}"),
            "controlled_regions": json.loads(s.controlled_regions_json or "[]"),
        }

    world_state = {"turn": world.current_turn, "status": world.status}

    result = AudienceEngine.intervene(
        req.action_type,
        req.target_sect_id,
        req.target_region_id,
        world_state,
        sect_states,
    )

    if result["success"] and req.target_sect_id:
        # 保存修改后的宗门状态
        sect = db.query(Sect).filter(Sect.id == req.target_sect_id).first()
        if sect:
            s_state = sect_states.get(req.target_sect_id)
            if s_state:
                sect.resources_json = json.dumps(s_state["resources"], ensure_ascii=False)
                sect.stats_json = json.dumps(s_state["stats"], ensure_ascii=False)
                db.commit()

    return result


@router.post("/{world_id}/audience/predict")
def audience_predict(world_id: str, req: PredictRequest, db: Session = Depends(get_db)):
    """观众预测"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")

    # 这里简化处理，实际应该记录预测并在结果出来后结算
    return {
        "success": True,
        "message": f"预测已记录：{req.prediction_type} -> {req.predicted_result}",
        "prediction_id": f"pred_{world_id}_{req.target_id}",
        "cost": 10,
    }


@router.get("/{world_id}/leaderboard")
def get_leaderboard(world_id: str, db: Session = Depends(get_db)):
    """获取赛季排行榜"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")

    sects = db.query(Sect).filter(Sect.world_id == world_id).all()
    battles = db.query(Battle).filter(Battle.world_id == world_id).all()
    diplomacy = db.query(DiplomacyRelation).filter(DiplomacyRelation.world_id == world_id).all()

    battle_dicts = []
    for b in battles:
        battle_dicts.append({
            "id": b.id,
            "attacker_sect_id": b.attacker_sect_id,
            "defender_sect_id": b.defender_sect_id,
            "winner_sect_id": b.winner_sect_id,
            "result_type": b.result_type,
        })

    dip_history = []
    for d in diplomacy:
        history = json.loads(d.history_json or "[]")
        for h in history:
            dip_history.append({
                "sect_a_id": d.sect_a_id,
                "sect_b_id": d.sect_b_id,
                "relation_type": d.relation_type,
                "success": h.get("success", False),
            })

    sect_scores = []
    for s in sects:
        sect_dict = {
            "id": s.id,
            "name": s.name,
            "status": s.status,
            "resources": json.loads(s.resources_json or "{}"),
            "stats": json.loads(s.stats_json or "{}"),
            "controlled_regions": json.loads(s.controlled_regions_json or "[]"),
        }
        scores = ScoringEngine.calculate_sect_score(
            sect_dict,
            world.current_turn,
            world.max_turns or 100,
            battle_dicts,
            dip_history,
            [],  # decisions 暂空
        )
        scores["sect_id"] = s.id
        scores["sect_name"] = s.name
        scores["model_name"] = s.model_name or "默认AI"
        scores["status"] = s.status
        sect_scores.append(scores)

    leaderboard = ScoringEngine.generate_leaderboard(sect_scores)

    return {
        "world_id": world_id,
        "turn": world.current_turn,
        "status": world.status,
        "leaderboard": leaderboard,
    }


@router.get("/{world_id}/season-report")
def get_season_report(world_id: str, db: Session = Depends(get_db)):
    """获取赛季总结报告"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")

    # 获取排行榜数据
    leaderboard_data = get_leaderboard(world_id, db)
    leaderboard = leaderboard_data["leaderboard"]

    report = ScoringEngine.generate_season_report(
        world_id,
        world.current_turn,
        leaderboard,
    )

    return report
