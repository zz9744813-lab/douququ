"""Worlds API Router"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.world_service import WorldService
from app.services.diplomacy_proposal_engine import DiplomacyProposalEngine
from app.models.world import World
from app.models.sect import Sect
from app.models.region import Region
from app.models.diplomacy import DiplomacyRelation
from app.models.diplomacy_proposal import DiplomacyProposal
from app.models.event import WorldEvent
from app.models.turn import TurnRecord
from app.models.battle import Battle
from app.models.character import Character

router = APIRouter(prefix="/api/worlds", tags=["worlds"])


class CreateWorldRequest(BaseModel):
    name: str = Field(..., description="世界名称")
    description: str = Field(default="", description="世界描述")
    mode: str = Field(default="season", description="游戏模式: season, sandbox, scenario, model_battle")
    max_turns: int = Field(default=100, description="最大回合数")
    sect_count: int = Field(default=8, description="宗门数量")
    map_size: str = Field(default="medium", description="地图大小: small, medium, large")
    world_seed: int = Field(default=42, description="世界种子")
    rules: dict = Field(default_factory=dict, description="自定义规则")


@router.post("")
def create_world(req: CreateWorldRequest, db: Session = Depends(get_db)):
    """创建新世界"""
    world = WorldService.create_world(
        db=db,
        name=req.name,
        description=req.description,
        mode=req.mode,
        max_turns=req.max_turns,
        sect_count=req.sect_count,
        map_size=req.map_size,
        world_seed=req.world_seed,
        rules=req.rules,
    )
    return _world_to_dict(world)


@router.get("")
def list_worlds(db: Session = Depends(get_db)):
    """获取世界列表"""
    worlds = db.query(World).order_by(World.created_at.desc()).all()
    return [_world_to_dict(w) for w in worlds]


@router.get("/{world_id}")
def get_world(world_id: str, db: Session = Depends(get_db)):
    """获取世界详情"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    return _world_to_dict(world)


@router.delete("/{world_id}")
def delete_world(world_id: str, db: Session = Depends(get_db)):
    """删除世界"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    db.delete(world)
    db.commit()
    return {"ok": True}


@router.get("/{world_id}/sects")
def get_world_sects(world_id: str, db: Session = Depends(get_db)):
    """获取世界宗门列表"""
    sects = db.query(Sect).filter(Sect.world_id == world_id).all()
    return [_sect_to_dict(s) for s in sects]


@router.get("/{world_id}/sects/{sect_id}")
def get_sect_detail(world_id: str, sect_id: str, db: Session = Depends(get_db)):
    """获取宗门详情"""
    sect = db.query(Sect).filter(Sect.world_id == world_id, Sect.id == sect_id).first()
    if not sect:
        raise HTTPException(status_code=404, detail="宗门不存在")
    return _sect_to_dict(sect)


@router.get("/{world_id}/regions")
def get_world_regions(world_id: str, db: Session = Depends(get_db)):
    """获取世界区域列表"""
    regions = db.query(Region).filter(Region.world_id == world_id).all()
    return [_region_to_dict(r) for r in regions]


@router.get("/{world_id}/map")
def get_world_map(world_id: str, db: Session = Depends(get_db)):
    """获取世界地图数据"""
    regions = db.query(Region).filter(Region.world_id == world_id).all()
    sects = db.query(Sect).filter(Sect.world_id == world_id).all()
    sect_map = {s.id: {"id": s.id, "name": s.name, "color": _sect_color(s.sect_type)} for s in sects}
    nodes = []
    for r in regions:
        nodes.append({
            "id": r.id,
            "name": r.name,
            "region_type": r.region_type,
            "owner_sect_id": r.owner_sect_id,
            "owner_name": sect_map.get(r.owner_sect_id, {}).get("name", "") if r.owner_sect_id else "",
            "owner_color": sect_map.get(r.owner_sect_id, {}).get("color", "#888") if r.owner_sect_id else "#888",
            "resource_level": r.resource_level,
            "defense_level": r.defense_level,
            "neighbors": json.loads(r.neighbors_json or "[]"),
        })
    return {"nodes": nodes, "sects": list(sect_map.values())}


@router.get("/{world_id}/diplomacy")
def get_world_diplomacy(world_id: str, db: Session = Depends(get_db)):
    """获取外交关系"""
    relations = db.query(DiplomacyRelation).filter(DiplomacyRelation.world_id == world_id).all()
    sects = db.query(Sect).filter(Sect.world_id == world_id).all()
    sect_names = {s.id: s.name for s in sects}
    return [{
        "id": r.id,
        "sect_a_id": r.sect_a_id,
        "sect_b_id": r.sect_b_id,
        "sect_a_name": sect_names.get(r.sect_a_id, ""),
        "sect_b_name": sect_names.get(r.sect_b_id, ""),
        "relation_type": r.relation_type,
        "relation_score": r.relation_score,
        "trust_score": r.trust_score,
    } for r in relations]


@router.get("/{world_id}/diplomacy/graph")
def get_diplomacy_graph(world_id: str, db: Session = Depends(get_db)):
    """获取外交关系图数据"""
    sects = db.query(Sect).filter(Sect.world_id == world_id).all()
    relations = db.query(DiplomacyRelation).filter(DiplomacyRelation.world_id == world_id).all()
    nodes = [{"id": s.id, "name": s.name, "type": s.sect_type, "status": s.status} for s in sects]
    edges = []
    for r in relations:
        edges.append({
            "source": r.sect_a_id,
            "target": r.sect_b_id,
            "relation_type": r.relation_type,
            "score": r.relation_score,
        })
    return {"nodes": nodes, "edges": edges}


@router.get("/{world_id}/events")
def get_world_events(world_id: str, turn: int | None = None, tags: str | None = None, db: Session = Depends(get_db)):
    """获取事件列表"""
    query = db.query(WorldEvent).filter(WorldEvent.world_id == world_id)
    if turn is not None:
        query = query.filter(WorldEvent.turn == turn)
    if tags:
        # Simple tag filter using LIKE
        for tag in tags.split(","):
            query = query.filter(WorldEvent.tags_json.contains(tag.strip()))
    events = query.order_by(WorldEvent.turn.desc(), WorldEvent.severity.desc()).limit(100).all()
    return [_event_to_dict(e) for e in events]


@router.get("/{world_id}/battles")
def get_world_battles(world_id: str, db: Session = Depends(get_db)):
    """获取战争记录"""
    battles = db.query(Battle).filter(Battle.world_id == world_id).order_by(Battle.turn.desc()).all()
    return [_battle_to_dict(b) for b in battles]


@router.get("/{world_id}/turns")
def get_turn_records(world_id: str, db: Session = Depends(get_db)):
    """获取回合记录"""
    records = db.query(TurnRecord).filter(TurnRecord.world_id == world_id).order_by(TurnRecord.turn.desc()).all()
    return [{"id": r.id, "turn": r.turn, "status": r.status, "summary": r.summary} for r in records]


@router.get("/{world_id}/turns/{turn}")
def get_turn_detail(world_id: str, turn: int, db: Session = Depends(get_db)):
    """获取回合详情（含所有行动结果和战斗回放）"""
    record = db.query(TurnRecord).filter(TurnRecord.world_id == world_id, TurnRecord.turn == turn).first()
    if not record:
        raise HTTPException(status_code=404, detail="回合不存在")

    return {
        "id": record.id,
        "turn": record.turn,
        "status": record.status,
        "summary": record.summary,
        "actions": json.loads(record.agent_actions_json or "{}"),
        "results": json.loads(record.resolved_results_json or "[]"),
    }


@router.get("/{world_id}/turns/{turn}/replay")
def get_turn_replay(world_id: str, turn: int, db: Session = Depends(get_db)):
    """获取回合回放数据（按时间顺序排列的所有事件）"""
    record = db.query(TurnRecord).filter(TurnRecord.world_id == world_id, TurnRecord.turn == turn).first()
    if not record:
        raise HTTPException(status_code=404, detail="回合不存在")

    # 获取该回合的所有事件
    events = db.query(WorldEvent).filter(
        WorldEvent.world_id == world_id,
        WorldEvent.turn == turn,
    ).order_by(WorldEvent.severity.desc()).all()

    # 获取该回合的所有战斗
    battles = db.query(Battle).filter(
        Battle.world_id == world_id,
        Battle.turn == turn,
    ).all()

    # 构建时间线
    timeline = []

    # 添加事件
    for e in events:
        timeline.append({
            "type": "event",
            "event_type": e.event_type,
            "title": e.title,
            "description": e.description,
            "severity": e.severity,
            "affected_sects": json.loads(e.affected_sects_json or "[]"),
        })

    # 添加战斗（含回放）
    for b in battles:
        timeline.append({
            "type": "battle",
            "title": f"{b.battle_log[:30]}...",
            "description": b.battle_log,
            "result_type": b.result_type,
            "attacker_sect_id": b.attacker_sect_id,
            "defender_sect_id": b.defender_sect_id,
            "winner_sect_id": b.winner_sect_id,
            "attacker_power": b.attacker_power,
            "defender_power": b.defender_power,
            "losses": json.loads(b.losses_json or "{}"),
            "rewards": json.loads(b.rewards_json or "{}"),
        })

    # 按严重程度排序
    timeline.sort(key=lambda x: x.get("severity", 0.5), reverse=True)

    return {
        "turn": turn,
        "summary": record.summary,
        "timeline": timeline,
    }


@router.get("/{world_id}/characters")
def get_world_characters(world_id: str, sect_id: str | None = None, role: str | None = None, db: Session = Depends(get_db)):
    """获取世界角色列表，可按宗门或角色类型筛选"""
    query = db.query(Character).filter(Character.world_id == world_id)
    if sect_id:
        query = query.filter(Character.sect_id == sect_id)
    if role:
        query = query.filter(Character.role == role)
    chars = query.all()
    return [_character_to_dict(c) for c in chars]


@router.get("/{world_id}/characters/{char_id}")
def get_character_detail(world_id: str, char_id: str, db: Session = Depends(get_db)):
    """获取角色详情"""
    char = db.query(Character).filter(Character.world_id == world_id, Character.id == char_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    return _character_to_dict(char)


# --- 外交提案 API ---

class CreateProposalRequest(BaseModel):
    from_sect_id: str
    to_sect_id: str
    proposal_type: str = Field(..., description="trade, non_aggression, alliance, vassal, secret_pact, ceasefire, threat")
    conditions: dict = Field(default_factory=dict)
    is_secret: bool = False


@router.post("/{world_id}/diplomacy/proposals")
def create_proposal(world_id: str, req: CreateProposalRequest, db: Session = Depends(get_db)):
    """创建外交提案"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")

    engine = DiplomacyProposalEngine(db)
    result = engine.create_proposal(
        world_id=world_id,
        turn=world.current_turn,
        from_sect_id=req.from_sect_id,
        to_sect_id=req.to_sect_id,
        proposal_type=req.proposal_type,
        conditions=req.conditions,
        is_secret=req.is_secret,
        auto_resolve=True,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{world_id}/diplomacy/proposals")
def list_proposals(world_id: str, sect_id: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    """获取外交提案列表"""
    query = db.query(DiplomacyProposal).filter(DiplomacyProposal.world_id == world_id)
    if sect_id:
        query = query.filter(
            (DiplomacyProposal.from_sect_id == sect_id) | (DiplomacyProposal.to_sect_id == sect_id)
        )
    if status:
        query = query.filter(DiplomacyProposal.status == status)
    proposals = query.order_by(DiplomacyProposal.turn.desc()).all()
    return [_proposal_to_dict(p) for p in proposals]


@router.get("/{world_id}/diplomacy/proposals/{proposal_id}")
def get_proposal(world_id: str, proposal_id: str, db: Session = Depends(get_db)):
    """获取提案详情"""
    p = db.query(DiplomacyProposal).filter(DiplomacyProposal.world_id == world_id, DiplomacyProposal.id == proposal_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="提案不存在")
    return _proposal_to_dict(p)


@router.post("/{world_id}/diplomacy/proposals/{proposal_id}/resolve")
def resolve_proposal(world_id: str, proposal_id: str, db: Session = Depends(get_db)):
    """手动结算提案（接受/拒绝）"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    engine = DiplomacyProposalEngine(db)
    result = engine.resolve_proposal(proposal_id, world.current_turn)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{world_id}/diplomacy/proposals/{proposal_id}/betray")
def betray_proposal(world_id: str, proposal_id: str, betrayer_sect_id: str, reason: str = "", db: Session = Depends(get_db)):
    """背叛条约"""
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="世界不存在")
    engine = DiplomacyProposalEngine(db)
    result = engine.betray_proposal(proposal_id, betrayer_sect_id, world.current_turn, reason)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{world_id}/diplomacy/treaties")
def get_active_treaties(world_id: str, sect_id: str | None = None, db: Session = Depends(get_db)):
    """获取有效条约"""
    engine = DiplomacyProposalEngine(db)
    return engine.get_active_treaties(world_id, sect_id)


# --- Helper functions ---

def _world_to_dict(w: World) -> dict:
    return {
        "id": w.id,
        "name": w.name,
        "description": w.description,
        "status": w.status,
        "current_turn": w.current_turn,
        "max_turns": w.max_turns,
        "world_seed": w.world_seed,
        "mode": w.mode,
        "map_size": w.map_size,
        "sect_count": w.sect_count,
        "rules": json.loads(w.rules_json or "{}"),
        "created_at": w.created_at.isoformat() if w.created_at else "",
        "updated_at": w.updated_at.isoformat() if w.updated_at else "",
    }


def _sect_to_dict(s: Sect) -> dict:
    return {
        "id": s.id,
        "world_id": s.world_id,
        "name": s.name,
        "sect_type": s.sect_type,
        "leader_name": s.leader_name,
        "status": s.status,
        "resources": json.loads(s.resources_json or "{}"),
        "stats": json.loads(s.stats_json or "{}"),
        "personality": json.loads(s.personality_json or "{}"),
        "memory": json.loads(s.memory_json or "[]"),
        "controlled_regions": json.loads(s.controlled_regions_json or "[]"),
        "strategy_summary": s.strategy_summary,
        "win_score": s.win_score,
        "reliability": s.reliability,
    }


def _region_to_dict(r: Region) -> dict:
    return {
        "id": r.id,
        "world_id": r.world_id,
        "name": r.name,
        "region_type": r.region_type,
        "owner_sect_id": r.owner_sect_id,
        "resource_level": r.resource_level,
        "defense_level": r.defense_level,
        "stability": r.stability,
        "neighbors": json.loads(r.neighbors_json or "[]"),
        "special_flags": json.loads(r.special_flags_json or "[]"),
    }


def _event_to_dict(e: WorldEvent) -> dict:
    return {
        "id": e.id,
        "world_id": e.world_id,
        "turn": e.turn,
        "event_type": e.event_type,
        "title": e.title,
        "description": e.description,
        "severity": e.severity,
        "affected_sects": json.loads(e.affected_sects_json or "[]"),
        "affected_regions": json.loads(e.affected_regions_json or "[]"),
        "tags": json.loads(e.tags_json or "[]"),
    }


def _battle_to_dict(b: Battle) -> dict:
    return {
        "id": b.id,
        "world_id": b.world_id,
        "turn": b.turn,
        "attacker_sect_id": b.attacker_sect_id,
        "defender_sect_id": b.defender_sect_id,
        "region_id": b.region_id,
        "result_type": b.result_type,
        "winner_sect_id": b.winner_sect_id,
        "attacker_power": b.attacker_power,
        "defender_power": b.defender_power,
        "losses": json.loads(b.losses_json or "{}"),
        "rewards": json.loads(b.rewards_json or "{}"),
        "battle_log": b.battle_log,
    }


def _character_to_dict(c: Character) -> dict:
    return {
        "id": c.id,
        "world_id": c.world_id,
        "sect_id": c.sect_id,
        "name": c.name,
        "role": c.role,
        "realm": c.realm,
        "cultivation": c.cultivation,
        "talent": c.talent,
        "loyalty": c.loyalty,
        "ambition": c.ambition,
        "combat_power": c.combat_power,
        "luck": c.luck,
        "status": c.status,
        "traits": json.loads(c.traits_json or "[]"),
        "relationships": json.loads(c.relationships_json or "{}"),
        "inventory": json.loads(c.inventory_json or "[]"),
        "story_flags": json.loads(c.story_flags_json or "[]"),
        "created_at": c.created_at.isoformat() if c.created_at else "",
        "updated_at": c.updated_at.isoformat() if c.updated_at else "",
    }


def _proposal_to_dict(p: DiplomacyProposal) -> dict:
    return {
        "id": p.id,
        "world_id": p.world_id,
        "turn": p.turn,
        "from_sect_id": p.from_sect_id,
        "from_sect_name": p.from_sect_name,
        "to_sect_id": p.to_sect_id,
        "to_sect_name": p.to_sect_name,
        "proposal_type": p.proposal_type,
        "title": p.title,
        "description": p.description,
        "conditions": json.loads(p.conditions_json or "{}"),
        "status": p.status,
        "response_message": p.response_message,
        "response_turn": p.response_turn,
        "is_secret": p.is_secret,
        "betrayed_by": p.betrayed_by,
        "betrayal_turn": p.betrayal_turn,
        "betrayal_reason": p.betrayal_reason,
        "success_rate": p.success_rate,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _sect_color(sect_type: str) -> str:
    colors = {
        "sword": "#e74c3c",
        "alchemy": "#2ecc71",
        "formation": "#3498db",
        "demon": "#9b59b6",
        "beast": "#e67e22",
        "artifact": "#f39c12",
        "merchant": "#1abc9c",
        "hidden": "#7f8c8d",
    }
    return colors.get(sect_type, "#95a5a6")
