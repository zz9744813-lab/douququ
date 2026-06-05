"""
Audience Interaction Engine - 玩家天道互动引擎
处理预测、干预、打赏等玩家互动
"""
import json
import random
from typing import Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audience_interaction import AudiencePrediction, AudienceIntervention
from app.models.event import WorldEvent
from app.models.sect import Sect
from app.models.world import World


class AudienceInteractionEngine:
    """玩家天道互动引擎"""

    INTERVENTION_TYPES = {
        "bless": {"name": "天佑", "cost": 100, "description": "赐予宗门祝福，提升军事实力", "effects": {"military_power": 30, "morale": 0.2}},
        "curse": {"name": "天罚", "cost": 150, "description": "降下天罚，削弱敌对宗门", "effects": {"military_power": -25, "stability": -0.15}},
        "resource_rain": {"name": "资源雨", "cost": 80, "description": "天降灵石雨，补充资源", "effects": {"spirit_stones": 500, "medicinal_herbs": 50}},
        "revelation": {"name": "天机启示", "cost": 120, "description": "泄露天机，提升宗门策略", "effects": {"intelligence": 0.3, "diplomacy_bonus": 0.2}},
        "disaster": {"name": "天灾", "cost": 200, "description": "引发天灾，重创目标区域", "effects": {"region_stability": -0.3, "military_power": -20, "spirit_stones": -200}},
        "divine_intervention": {"name": "神降", "cost": 500, "description": "直接干预战局，改变战争结果", "effects": {"battle_bonus": 0.5, "morale": 0.5}},
    }

    PREDICTION_REWARDS = {
        "winner": 500,      # 预测最终赢家
        "next_war": 200,    # 预测下回合战争
        "annexation": 300,  # 预测吞并
        "alliance": 150,    # 预测结盟
    }

    def __init__(self, db: Session):
        self.db = db

    # === 预测系统 ===

    def create_prediction(self, world_id: str, user_id: str, prediction_type: str, target_sect_id: str | None = None, predicted_turn: int | None = None) -> dict:
        """创建预测"""
        world = self.db.query(World).filter(World.id == world_id).first()
        if not world:
            return {"error": "世界不存在"}

        sect = None
        if target_sect_id:
            sect = self.db.query(Sect).filter(Sect.id == target_sect_id).first()

        prediction = AudiencePrediction(
            world_id=world_id,
            user_id=user_id,
            prediction_type=prediction_type,
            target_sect_id=target_sect_id,
            target_sect_name=sect.name if sect else "",
            predicted_turn=predicted_turn,
        )
        self.db.add(prediction)
        self.db.commit()

        return {
            "prediction_id": prediction.id,
            "type": prediction_type,
            "target": sect.name if sect else "未指定",
            "status": "pending",
        }

    def resolve_predictions(self, world_id: str, turn: int, world_state: dict) -> list[dict]:
        """结算本回合的预测"""
        results = []

        # 获取待结算预测
        predictions = self.db.query(AudiencePrediction).filter(
            AudiencePrediction.world_id == world_id,
            AudiencePrediction.status == "pending",
        ).all()

        active_sects = [s for s in world_state.get("sects", []) if s.get("status") == "active"]
        events = world_state.get("events", [])

        for pred in predictions:
            correct = False

            if pred.prediction_type == "winner":
                # 检查是否只剩一个宗门或达到最大回合
                if len(active_sects) <= 1:
                    winner = active_sects[0] if active_sects else None
                    if winner and winner.get("id") == pred.target_sect_id:
                        correct = True

            elif pred.prediction_type == "next_war":
                # 检查本回合是否有战争
                war_events = [e for e in events if e.get("event_type") == "battle" or e.get("type") == "battle"]
                if war_events:
                    correct = True

            elif pred.prediction_type == "annexation":
                # 检查本回合是否有吞并
                annex_events = [e for e in events if e.get("event_type") == "annexation"]
                if annex_events:
                    correct = True

            elif pred.prediction_type == "alliance":
                # 检查本回合是否有结盟
                dip_events = [e for e in events if e.get("event_type") == "diplomacy"]
                for e in dip_events:
                    desc = e.get("description", "")
                    if "结盟" in desc or "alliance" in desc:
                        correct = True
                        break

            # 如果预测了特定回合，检查是否匹配
            if pred.predicted_turn is not None and pred.predicted_turn != turn:
                correct = False

            if correct:
                pred.status = "correct"
                pred.resolved_turn = turn
                pred.reward_points = self.PREDICTION_REWARDS.get(pred.prediction_type, 100)
                results.append({
                    "prediction_id": pred.id,
                    "correct": True,
                    "reward": pred.reward_points,
                    "message": f"预测正确！获得 {pred.reward_points} 积分",
                })
            elif pred.predicted_turn is not None and turn > pred.predicted_turn:
                # 超过预测回合仍未发生
                pred.status = "wrong"
                pred.resolved_turn = turn
                results.append({
                    "prediction_id": pred.id,
                    "correct": False,
                    "reward": 0,
                    "message": "预测失败，未在指定回合发生",
                })

        self.db.commit()
        return results

    def get_user_predictions(self, world_id: str, user_id: str) -> list[dict]:
        """获取用户的预测记录"""
        preds = self.db.query(AudiencePrediction).filter(
            AudiencePrediction.world_id == world_id,
            AudiencePrediction.user_id == user_id,
        ).order_by(AudiencePrediction.created_at.desc()).all()
        return [self._prediction_to_dict(p) for p in preds]

    # === 干预系统 ===

    def create_intervention(self, world_id: str, turn: int, user_id: str, intervention_type: str, target_sect_id: str | None = None, target_region_id: str | None = None) -> dict:
        """创建天道干预"""
        world = self.db.query(World).filter(World.id == world_id).first()
        if not world:
            return {"error": "世界不存在"}

        if intervention_type not in self.INTERVENTION_TYPES:
            return {"error": f"未知干预类型: {intervention_type}"}

        config = self.INTERVENTION_TYPES[intervention_type]

        sect = None
        if target_sect_id:
            sect = self.db.query(Sect).filter(Sect.id == target_sect_id).first()

        intervention = AudienceIntervention(
            world_id=world_id,
            turn=turn,
            user_id=user_id,
            intervention_type=intervention_type,
            target_sect_id=target_sect_id,
            target_sect_name=sect.name if sect else "",
            target_region_id=target_region_id,
            title=config["name"],
            description=config["description"],
            effects_json=json.dumps(config["effects"], ensure_ascii=False),
            cost_points=config["cost"],
        )
        self.db.add(intervention)

        # 应用干预效果到宗门
        if sect and target_sect_id:
            resources = json.loads(sect.resources_json or "{}")
            stats = json.loads(sect.stats_json or "{}")
            effects = config["effects"]

            for key, value in effects.items():
                if key in ["military_power", "spirit_stones", "medicinal_herbs"]:
                    if key == "military_power":
                        stats[key] = stats.get(key, 0) + value
                    else:
                        resources[key] = resources.get(key, 0) + value
                elif key in ["stability", "morale", "intelligence"]:
                    stats[key] = max(0, min(1, stats.get(key, 0.5) + value))

            sect.resources_json = json.dumps(resources, ensure_ascii=False)
            sect.stats_json = json.dumps(stats, ensure_ascii=False)

        # 创建世界事件
        evt = WorldEvent(
            id=uuid.uuid4().hex[:12],
            world_id=world_id,
            turn=turn,
            event_type="divine_intervention",
            title=f"☁️ 天道干预：{config['name']}",
            description=f"玩家 {user_id} 发动{config['name']}，{'作用于 ' + sect.name if sect else '影响整个世界'}！",
            severity=0.6,
            affected_sects_json=json.dumps([target_sect_id] if target_sect_id else [], ensure_ascii=False),
            affected_regions_json=json.dumps([target_region_id] if target_region_id else [], ensure_ascii=False),
            tags_json=json.dumps(["天道", "玩家干预", intervention_type], ensure_ascii=False),
            raw_result_json=json.dumps(config["effects"], ensure_ascii=False),
        )
        self.db.add(evt)
        self.db.commit()

        return {
            "intervention_id": intervention.id,
            "type": intervention_type,
            "title": config["name"],
            "cost": config["cost"],
            "effects": config["effects"],
            "target": sect.name if sect else "全局",
        }

    def get_intervention_history(self, world_id: str, user_id: str | None = None) -> list[dict]:
        """获取干预历史"""
        query = self.db.query(AudienceIntervention).filter(AudienceIntervention.world_id == world_id)
        if user_id:
            query = query.filter(AudienceIntervention.user_id == user_id)
        interventions = query.order_by(AudienceIntervention.turn.desc()).all()
        return [self._intervention_to_dict(i) for i in interventions]

    def get_available_interventions(self) -> list[dict]:
        """获取可用的干预类型列表"""
        return [
            {"type": k, "name": v["name"], "cost": v["cost"], "description": v["description"], "effects": v["effects"]}
            for k, v in self.INTERVENTION_TYPES.items()
        ]

    def _prediction_to_dict(self, p: AudiencePrediction) -> dict:
        return {
            "id": p.id,
            "world_id": p.world_id,
            "user_id": p.user_id,
            "prediction_type": p.prediction_type,
            "target_sect_id": p.target_sect_id,
            "target_sect_name": p.target_sect_name,
            "predicted_turn": p.predicted_turn,
            "status": p.status,
            "resolved_turn": p.resolved_turn,
            "reward_points": p.reward_points,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }

    def _intervention_to_dict(self, i: AudienceIntervention) -> dict:
        return {
            "id": i.id,
            "world_id": i.world_id,
            "turn": i.turn,
            "user_id": i.user_id,
            "intervention_type": i.intervention_type,
            "target_sect_id": i.target_sect_id,
            "target_sect_name": i.target_sect_name,
            "title": i.title,
            "description": i.description,
            "effects": json.loads(i.effects_json or "{}"),
            "cost_points": i.cost_points,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
