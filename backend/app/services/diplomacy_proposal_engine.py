"""
Diplomacy Proposal Engine - 外交提案引擎
处理提案-响应、密约、背刺等复杂外交互动
"""
import json
import random
from typing import Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.diplomacy_proposal import DiplomacyProposal
from app.models.diplomacy import DiplomacyRelation
from app.models.event import WorldEvent
from app.models.sect import Sect
from app.services.diplomacy_engine import DiplomacyEngine


class DiplomacyProposalEngine:
    """外交提案引擎"""

    PROPOSAL_TYPES = {
        "trade": {"name": "贸易协议", "duration": 5, "relation_change": 0.1},
        "non_aggression": {"name": "互不侵犯条约", "duration": 8, "relation_change": 0.15},
        "alliance": {"name": "结盟", "duration": 10, "relation_change": 0.3},
        "vassal": {"name": "附庸关系", "duration": 15, "relation_change": 0.0},
        "secret_pact": {"name": "密约", "duration": 6, "relation_change": 0.2, "secret": True},
        "ceasefire": {"name": "停战协议", "duration": 4, "relation_change": 0.2},
        "threat": {"name": "威胁", "duration": 0, "relation_change": -0.2},
    }

    def __init__(self, db: Session):
        self.db = db
        self.diplomacy_engine = DiplomacyEngine()

    def create_proposal(
        self,
        world_id: str,
        turn: int,
        from_sect_id: str,
        to_sect_id: str,
        proposal_type: str,
        conditions: dict | None = None,
        is_secret: bool = False,
        auto_resolve: bool = True,
    ) -> dict:
        """
        创建外交提案。如果 auto_resolve=True，自动计算成功率并结算。
        """
        from_sect = self.db.query(Sect).filter(Sect.id == from_sect_id).first()
        to_sect = self.db.query(Sect).filter(Sect.id == to_sect_id).first()
        if not from_sect or not to_sect:
            return {"error": "宗门不存在"}

        # 查找外交关系
        rel = self._find_relation(world_id, from_sect_id, to_sect_id)
        rel_state = self._relation_to_dict(rel) if rel else {"relation_type": "neutral", "relation_score": 0, "trust_score": 0.5}

        # 计算成功率
        from_dict = self._sect_to_dict(from_sect)
        to_dict = self._sect_to_dict(to_sect)
        world_state = {"turn": turn}

        success_rate = self.diplomacy_engine.calculate_diplomacy_success(
            proposal_type, from_dict, to_dict, rel_state, world_state
        )

        # 密约自动设为秘密
        if proposal_type == "secret_pact":
            is_secret = True

        proposal = DiplomacyProposal(
            world_id=world_id,
            turn=turn,
            from_sect_id=from_sect_id,
            from_sect_name=from_sect.name,
            to_sect_id=to_sect_id,
            to_sect_name=to_sect.name,
            proposal_type=proposal_type,
            title=self.PROPOSAL_TYPES.get(proposal_type, {}).get("name", "外交提案"),
            description=self._generate_description(proposal_type, from_sect.name, to_sect.name),
            conditions_json=json.dumps(conditions or {}, ensure_ascii=False),
            is_secret=is_secret,
            success_rate=round(success_rate, 2),
        )
        self.db.add(proposal)
        self.db.flush()

        result = {
            "proposal_id": proposal.id,
            "success_rate": round(success_rate, 2),
            "status": "pending",
        }

        if auto_resolve:
            resolve_result = self.resolve_proposal(proposal.id, turn)
            result.update(resolve_result)

        self.db.commit()
        return result

    def resolve_proposal(self, proposal_id: str, turn: int) -> dict:
        """结算外交提案（接受/拒绝）"""
        proposal = self.db.query(DiplomacyProposal).filter(DiplomacyProposal.id == proposal_id).first()
        if not proposal:
            return {"error": "提案不存在"}
        if proposal.status != "pending":
            return {"error": f"提案已{proposal.status}"}

        roll = random.random()
        accepted = roll < proposal.success_rate

        proposal.status = "accepted" if accepted else "rejected"
        proposal.response_turn = turn
        proposal.response_message = self._generate_response_message(proposal, accepted)
        proposal.updated_at = datetime.now(timezone.utc)

        # 更新外交关系
        rel = self._find_relation(proposal.world_id, proposal.from_sect_id, proposal.to_sect_id)
        if not rel:
            rel = DiplomacyRelation(
                world_id=proposal.world_id,
                sect_a_id=proposal.from_sect_id,
                sect_b_id=proposal.to_sect_id,
            )
            self.db.add(rel)
            self.db.flush()

        if accepted:
            # 更新关系类型
            type_map = {
                "trade": "trade",
                "non_aggression": "non_aggression",
                "alliance": "alliance",
                "vassal": "vassal",
                "secret_pact": "friendly",
                "ceasefire": "neutral",
                "threat": "hostile",
            }
            rel.relation_type = type_map.get(proposal.proposal_type, rel.relation_type)
            rel.relation_score = min(1.0, rel.relation_score + self.PROPOSAL_TYPES.get(proposal.proposal_type, {}).get("relation_change", 0.05))
            rel.trust_score = min(1.0, rel.trust_score + 0.05)

            # 添加条约
            treaties = json.loads(rel.treaties_json or "[]")
            duration = self.PROPOSAL_TYPES.get(proposal.proposal_type, {}).get("duration", 5)
            treaties.append({
                "type": proposal.proposal_type,
                "from_sect_id": proposal.from_sect_id,
                "to_sect_id": proposal.to_sect_id,
                "start_turn": turn,
                "end_turn": turn + duration if duration > 0 else None,
                "proposal_id": proposal.id,
                "secret": proposal.is_secret,
            })
            rel.treaties_json = json.dumps(treaties, ensure_ascii=False)
        else:
            rel.relation_score = max(-1.0, rel.relation_score - 0.05)
            rel.trust_score = max(0.0, rel.trust_score - 0.03)

        # 记录历史
        history = json.loads(rel.history_json or "[]")
        history.append({
            "turn": turn,
            "action": proposal.proposal_type,
            "success": accepted,
            "proposal_id": proposal.id,
        })
        if len(history) > 20:
            history = history[-20:]
        rel.history_json = json.dumps(history, ensure_ascii=False)

        # 创建世界事件（非密约才公开）
        if not proposal.is_secret:
            evt = WorldEvent(
                id=uuid.uuid4().hex[:12],
                world_id=proposal.world_id,
                turn=turn,
                event_type="diplomacy",
                title=f"外交{'成功' if accepted else '失败'}：{proposal.title}",
                description=proposal.response_message,
                severity=0.3 if accepted else 0.2,
                affected_sects_json=json.dumps([proposal.from_sect_id, proposal.to_sect_id], ensure_ascii=False),
                affected_regions_json=json.dumps([], ensure_ascii=False),
                tags_json=json.dumps(["外交", proposal.proposal_type], ensure_ascii=False),
                raw_result_json=json.dumps({"proposal_id": proposal.id, "accepted": accepted}, ensure_ascii=False),
            )
            self.db.add(evt)

        self.db.commit()
        return {
            "proposal_id": proposal.id,
            "accepted": accepted,
            "status": proposal.status,
            "message": proposal.response_message,
        }

    def betray_proposal(self, proposal_id: str, betrayer_sect_id: str, turn: int, reason: str = "") -> dict:
        """背叛一个已接受的条约/密约"""
        proposal = self.db.query(DiplomacyProposal).filter(DiplomacyProposal.id == proposal_id).first()
        if not proposal:
            return {"error": "提案不存在"}
        if proposal.status != "accepted":
            return {"error": "只能背叛已接受的条约"}

        proposal.status = "betrayed"
        proposal.betrayed_by = betrayer_sect_id
        proposal.betrayal_turn = turn
        proposal.betrayal_reason = reason or "背信弃义"
        proposal.updated_at = datetime.now(timezone.utc)

        # 更新外交关系为敌对
        rel = self._find_relation(proposal.world_id, proposal.from_sect_id, proposal.to_sect_id)
        if rel:
            rel.relation_type = "hostile"
            rel.relation_score = -0.8
            rel.trust_score = max(0.0, rel.trust_score - 0.5)

            history = json.loads(rel.history_json or "[]")
            history.append({
                "turn": turn,
                "action": "betrayal",
                "betrayer": betrayer_sect_id,
                "proposal_id": proposal.id,
            })
            rel.history_json = json.dumps(history, ensure_ascii=False)

        # 创建背叛事件
        betrayer = self.db.query(Sect).filter(Sect.id == betrayer_sect_id).first()
        betrayer_name = betrayer.name if betrayer else "未知宗门"
        other_sect_id = proposal.to_sect_id if betrayer_sect_id == proposal.from_sect_id else proposal.from_sect_id
        other = self.db.query(Sect).filter(Sect.id == other_sect_id).first()
        other_name = other.name if other else "未知宗门"

        evt = WorldEvent(
            id=uuid.uuid4().hex[:12],
            world_id=proposal.world_id,
            turn=turn,
            event_type="betrayal",
            title=f"💀 背叛！{betrayer_name} 撕毁了条约",
            description=f"{betrayer_name} 背叛了与 {other_name} 的 {proposal.title}！{reason}",
            severity=0.85,
            affected_sects_json=json.dumps([proposal.from_sect_id, proposal.to_sect_id], ensure_ascii=False),
            affected_regions_json=json.dumps([], ensure_ascii=False),
            tags_json=json.dumps(["背叛", "外交破裂"], ensure_ascii=False),
            raw_result_json=json.dumps({"proposal_id": proposal.id, "betrayer": betrayer_sect_id}, ensure_ascii=False),
        )
        self.db.add(evt)
        self.db.commit()

        return {
            "proposal_id": proposal.id,
            "status": "betrayed",
            "betrayer": betrayer_sect_id,
            "message": f"{betrayer_name} 背叛了与 {other_name} 的条约！",
        }

    def check_expired_proposals(self, world_id: str, current_turn: int) -> list[dict]:
        """检查并处理过期的条约"""
        expired = []
        relations = self.db.query(DiplomacyRelation).filter(DiplomacyRelation.world_id == world_id).all()
        for rel in relations:
            treaties = json.loads(rel.treaties_json or "[]")
            active_treaties = []
            for t in treaties:
                end_turn = t.get("end_turn")
                if end_turn and current_turn > end_turn:
                    expired.append({
                        "type": t["type"],
                        "from_sect_id": t["from_sect_id"],
                        "to_sect_id": t["to_sect_id"],
                    })
                else:
                    active_treaties.append(t)
            if len(active_treaties) != len(treaties):
                rel.treaties_json = json.dumps(active_treaties, ensure_ascii=False)
        self.db.commit()
        return expired

    def get_active_treaties(self, world_id: str, sect_id: str | None = None) -> list[dict]:
        """获取有效的条约列表"""
        query = self.db.query(DiplomacyProposal).filter(
            DiplomacyProposal.world_id == world_id,
            DiplomacyProposal.status == "accepted",
        )
        if sect_id:
            query = query.filter(
                (DiplomacyProposal.from_sect_id == sect_id) | (DiplomacyProposal.to_sect_id == sect_id)
            )
        proposals = query.all()
        return [self._proposal_to_dict(p) for p in proposals]

    def get_proposal_history(self, world_id: str, sect_a_id: str | None = None, sect_b_id: str | None = None) -> list[dict]:
        """获取外交历史"""
        query = self.db.query(DiplomacyProposal).filter(DiplomacyProposal.world_id == world_id)
        if sect_a_id and sect_b_id:
            query = query.filter(
                ((DiplomacyProposal.from_sect_id == sect_a_id) & (DiplomacyProposal.to_sect_id == sect_b_id)) |
                ((DiplomacyProposal.from_sect_id == sect_b_id) & (DiplomacyProposal.to_sect_id == sect_a_id))
            )
        elif sect_a_id:
            query = query.filter(
                (DiplomacyProposal.from_sect_id == sect_a_id) | (DiplomacyProposal.to_sect_id == sect_a_id)
            )
        proposals = query.order_by(DiplomacyProposal.turn.desc()).all()
        return [self._proposal_to_dict(p) for p in proposals]

    def _find_relation(self, world_id: str, a_id: str, b_id: str) -> DiplomacyRelation | None:
        return self.db.query(DiplomacyRelation).filter(
            DiplomacyRelation.world_id == world_id,
            ((DiplomacyRelation.sect_a_id == a_id) & (DiplomacyRelation.sect_b_id == b_id)) |
            ((DiplomacyRelation.sect_a_id == b_id) & (DiplomacyRelation.sect_b_id == a_id))
        ).first()

    def _sect_to_dict(self, sect: Sect) -> dict:
        return {
            "id": sect.id,
            "name": sect.name,
            "sect_type": sect.sect_type,
            "status": sect.status,
            "resources": json.loads(sect.resources_json or "{}"),
            "stats": json.loads(sect.stats_json or "{}"),
            "personality": json.loads(sect.personality_json or "{}"),
            "controlled_regions": json.loads(sect.controlled_regions_json or "[]"),
            "enemy_sects": [],
        }

    def _relation_to_dict(self, rel: DiplomacyRelation) -> dict:
        return {
            "relation_type": rel.relation_type,
            "relation_score": rel.relation_score,
            "trust_score": rel.trust_score,
        }

    def _proposal_to_dict(self, p: DiplomacyProposal) -> dict:
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

    def _generate_description(self, proposal_type: str, from_name: str, to_name: str) -> str:
        templates = {
            "trade": f"{from_name} 提议与 {to_name} 建立贸易关系，互通有无。",
            "non_aggression": f"{from_name} 向 {to_name} 提议签订互不侵犯条约，和平共处。",
            "alliance": f"{from_name} 希望与 {to_name} 结为盟友，共同进退。",
            "vassal": f"{from_name} 向 {to_name} 提出附庸关系，寻求庇护。",
            "secret_pact": f"{from_name} 与 {to_name} 暗中达成密约...",
            "ceasefire": f"{from_name} 向 {to_name} 提议停战，休养生息。",
            "threat": f"{from_name} 向 {to_name} 发出威胁，若不服从将兵戎相见！",
        }
        return templates.get(proposal_type, f"{from_name} 向 {to_name} 提出外交提案。")

    def _generate_response_message(self, proposal: DiplomacyProposal, accepted: bool) -> str:
        if accepted:
            templates = {
                "trade": f"{proposal.to_sect_name} 欣然接受了贸易协议。",
                "non_aggression": f"{proposal.to_sect_name} 同意签订互不侵犯条约。",
                "alliance": f"{proposal.to_sect_name} 与 {proposal.from_sect_name} 正式结盟！",
                "vassal": f"{proposal.to_sect_name} 接受了附庸请求。",
                "secret_pact": f"密约达成，双方心照不宣。",
                "ceasefire": f"双方同意停火，暂时休战。",
                "threat": f"{proposal.to_sect_name} 被迫屈服于威胁。",
            }
        else:
            templates = {
                "trade": f"{proposal.to_sect_name} 拒绝了贸易请求。",
                "non_aggression": f"{proposal.to_sect_name} 对互不侵犯条约不感兴趣。",
                "alliance": f"{proposal.to_sect_name} 婉拒了结盟请求。",
                "vassal": f"{proposal.to_sect_name} 严词拒绝了附庸要求。",
                "secret_pact": f"密约谈判破裂。",
                "ceasefire": f"{proposal.to_sect_name} 拒绝停火，战斗继续！",
                "threat": f"{proposal.to_sect_name} 毫不畏惧，正面回应挑战！",
            }
        return templates.get(proposal.proposal_type, f"{proposal.to_sect_name} {'接受' if accepted else '拒绝'}了提案。")
