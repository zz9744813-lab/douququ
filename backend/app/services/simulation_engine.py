"""
Simulation Engine - 回合模拟引擎
负责每个回合的完整流程：AI决策 → 规则校验 → 结算 → 战报生成
"""
import json
import random
import uuid
from typing import Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.world import World
from app.models.sect import Sect
from app.models.region import Region
from app.models.diplomacy import DiplomacyRelation
from app.models.turn import TurnRecord
from app.models.event import WorldEvent
from app.models.battle import Battle
from app.services.rule_engine import RuleEngine
from app.services.battle_engine import BattleEngine
from app.services.battle_replay_engine import BattleReplayEngine
from app.services.diplomacy_engine import DiplomacyEngine
from app.services.event_engine import EventEngine
from app.services.default_ai import DefaultAI
from app.services.llm_agent import LLMAgent


class SimulationEngine:
    """回合模拟引擎"""

    def __init__(self, db: Session, use_llm: bool = False):
        self.db = db
        self.rule_engine = RuleEngine()
        self.battle_engine = BattleEngine()
        self.battle_replay_engine = BattleReplayEngine()
        self.diplomacy_engine = DiplomacyEngine()
        self.event_engine = EventEngine()
        self.default_ai = DefaultAI()
        self.llm_agent = LLMAgent() if use_llm else None
        self.use_llm = use_llm

    async def run_turn(self, world_id: str) -> dict:
        """执行一个完整回合（支持异步 LLM Agent）"""
        world = self.db.query(World).filter(World.id == world_id).first()
        if not world:
            return {"error": "世界不存在"}
        if world.status == "finished":
            return {"error": "世界已结束"}

        turn = world.current_turn + 1
        world.status = "running"
        self.db.flush()

        # 1. 加载世界状态
        sects = self.db.query(Sect).filter(Sect.world_id == world_id, Sect.status == "active").all()
        regions = self.db.query(Region).filter(Region.world_id == world_id).all()
        diplomacy = self.db.query(DiplomacyRelation).filter(DiplomacyRelation.world_id == world_id).all()

        world_state = self._build_world_state(sects, regions, diplomacy)
        world_state["turn"] = turn

        # 2. 生成世界事件
        world_events = self.event_engine.generate_world_events(turn, world.world_seed)

        # 3. 保存回合快照
        input_snapshot = self._build_snapshot(sects, regions, diplomacy)

        # 4. 各宗门生成行动（支持 LLM Agent 异步并行）
        all_actions = {}
        if self.use_llm and self.llm_agent:
            # 并行调用 LLM Agent
            import asyncio
            tasks = []
            for sect in sects:
                sect_state = self._build_sect_state(sect, regions, world_state)
                tasks.append(self.llm_agent.generate_actions(sect_state, world_state, max_actions=3))
            llm_results = await asyncio.gather(*tasks, return_exceptions=True)
            for sect, result in zip(sects, llm_results):
                if isinstance(result, Exception):
                    # LLM 异常，回退到默认 AI
                    ai_output = self.default_ai.generate_actions(
                        self._build_sect_state(sect, regions, world_state), world_state, max_actions=3
                    )
                    ai_output["source"] = "fallback_exception"
                    ai_output["llm_error"] = str(result)
                    all_actions[sect.id] = ai_output
                else:
                    all_actions[sect.id] = result
        else:
            for sect in sects:
                sect_state = self._build_sect_state(sect, regions, world_state)
                ai_output = self.default_ai.generate_actions(sect_state, world_state, max_actions=3)
                all_actions[sect.id] = ai_output

        # 5. 收集并分类行动
        war_actions = []
        diplomacy_actions = []
        economy_actions = []
        other_actions = []

        for sect_id, ai_output in all_actions.items():
            for action in ai_output["actions"]:
                atype = action.get("type", "")
                entry = (sect_id, action)
                if atype == "declare_war":
                    war_actions.append(entry)
                elif atype == "diplomacy_offer":
                    diplomacy_actions.append(entry)
                elif atype in ("build_structure", "make_pills", "craft_artifacts"):
                    economy_actions.append(entry)
                else:
                    other_actions.append(entry)

        # 6. 按顺序结算：经济 → 外交 → 战争 → 其他
        all_results = []
        sect_states = {s.id: self._load_sect_dict(s) for s in sects}
        # 每个宗门每回合有 3 个行动点
        for sid in sect_states:
            sect_states[sid]["action_points"] = 3
        region_states = {r.id: self._load_region_dict(r) for r in regions}

        # 6a. 经济行动
        for sect_id, action in economy_actions:
            sect = sect_states.get(sect_id)
            if not sect:
                continue
            is_valid, reason = self.rule_engine.validate_action(action, sect, world_state)
            if is_valid:
                # 消耗行动点
                cost = self.rule_engine.ACTION_COSTS.get(action.get("type", ""), 1)
                sect["action_points"] = max(0, sect.get("action_points", 0) - cost)
                # 统一扣除资源
                self.rule_engine.deduct_cost(sect, action.get("type", ""))
                result = self.rule_engine.resolve_action(action, sect, world_state)
                self.rule_engine.apply_effects(sect["resources"], sect["stats"], result.get("effects", {}))
                all_results.append({"sect_id": sect_id, "action": action, "result": result, "valid": True})
            else:
                all_results.append({"sect_id": sect_id, "action": action, "result": {"log": reason}, "valid": False})

        # 6b. 外交行动
        for sect_id, action in diplomacy_actions:
            sect = sect_states.get(sect_id)
            if not sect:
                continue
            is_valid, reason = self.rule_engine.validate_action(action, sect, world_state)
            if not is_valid:
                all_results.append({"sect_id": sect_id, "action": action, "result": {"log": reason}, "valid": False})
                continue

            # 消耗行动点
            cost = self.rule_engine.ACTION_COSTS.get(action.get("type", ""), 1)
            sect["action_points"] = max(0, sect.get("action_points", 0) - cost)
            # 统一扣除资源
            self.rule_engine.deduct_cost(sect, action.get("type", ""))

            target_id = action.get("target_sect_id")
            target = sect_states.get(target_id)
            if not target:
                all_results.append({"sect_id": sect_id, "action": action, "result": {"log": "目标宗门不存在"}, "valid": False})
                continue

            # 找到外交关系
            rel = self._find_diplomacy_relation(diplomacy, sect_id, target_id)
            rel_state = self._load_relation_dict(rel) if rel else {"relation_type": "neutral", "relation_score": 0, "trust_score": 0.5}

            dip_result = self.diplomacy_engine.resolve_diplomacy(
                action.get("offer_type", "trade"),
                sect, target, rel_state, world_state,
            )
            # 更新外交关系
            if rel:
                rel.relation_score = min(1.0, max(-1.0, rel.relation_score + dip_result["relation_change"]))
                rel.relation_type = dip_result["new_relation_type"]
                rel.trust_score = min(1.0, max(0.0, rel.trust_score + (0.05 if dip_result["success"] else -0.05)))
                history = json.loads(rel.history_json or "[]")
                history.append({"turn": turn, "action": action.get("offer_type"), "success": dip_result["success"]})
                if len(history) > 20:
                    history = history[-20:]
                rel.history_json = json.dumps(history, ensure_ascii=False)

            all_results.append({"sect_id": sect_id, "action": action, "result": dip_result, "valid": True})

        # 6c. 资源产出
        for sect_id, sect in sect_states.items():
            owned_regions = [region_states.get(rid) for rid in sect.get("controlled_regions", [])]
            owned_regions = [r for r in owned_regions if r]
            production = self.rule_engine.calculate_resource_production(sect, owned_regions)
            for k, v in production.items():
                sect["resources"][k] = sect["resources"].get(k, 0) + v

        # 6d. 战争行动
        for sect_id, action in war_actions:
            sect = sect_states.get(sect_id)
            if not sect:
                continue
            is_valid, reason = self.rule_engine.validate_action(action, sect, world_state)
            if not is_valid:
                all_results.append({"sect_id": sect_id, "action": action, "result": {"log": reason}, "valid": False})
                continue

            # 消耗行动点
            cost = self.rule_engine.ACTION_COSTS.get(action.get("type", ""), 2)
            sect["action_points"] = max(0, sect.get("action_points", 0) - cost)

            target_id = action.get("target_sect_id")
            target = sect_states.get(target_id)
            if not target:
                continue

            # 统一扣除资源
            self.rule_engine.deduct_cost(sect, "declare_war")

            # 结算战争
            region_id = action.get("target_region_id")
            region = region_states.get(region_id) if region_id else None
            battle_result = self.battle_engine.resolve_battle(sect, target, region)

            # 应用伤亡
            sect["stats"]["military_power"] = max(0, sect["stats"].get("military_power", 0) - battle_result["losses"]["attacker_loss"])
            target["stats"]["military_power"] = max(0, target["stats"].get("military_power", 0) - battle_result["losses"]["defender_loss"])

            # 处理奖励
            rewards = battle_result["rewards"]
            if rewards.get("spirit_stones", 0) > 0:
                sect["resources"]["spirit_stones"] = sect["resources"].get("spirit_stones", 0) + rewards["spirit_stones"]
                target["resources"]["spirit_stones"] = max(0, target["resources"].get("spirit_stones", 0) - rewards["spirit_stones"])

            # 占领区域
            for rid in rewards.get("regions_captured", []):
                if rid in region_states:
                    region_states[rid]["owner_sect_id"] = sect_id
                    sect["controlled_regions"].append(rid)
                    if rid in target.get("controlled_regions", []):
                        target["controlled_regions"].remove(rid)

            # 更新外交关系
            rel = self._find_diplomacy_relation(diplomacy, sect_id, target_id)
            if rel:
                rel.relation_type = "war"
                rel.relation_score = min(rel.relation_score, -0.5)

            # 生成战斗回放
            replay = self.battle_replay_engine.generate_replay(
                sect, target, region, battle_result
            )
            battle_result["replay"] = replay

            # 保存战争记录
            battle = Battle(
                id=uuid.uuid4().hex[:12],
                world_id=world_id,
                turn=turn,
                attacker_sect_id=sect_id,
                defender_sect_id=target_id,
                region_id=region_id,
                result_type=battle_result["result_type"],
                winner_sect_id=battle_result["winner_sect_id"],
                attacker_power=battle_result["attacker_power"],
                defender_power=battle_result["defender_power"],
                losses_json=json.dumps(battle_result["losses"], ensure_ascii=False),
                rewards_json=json.dumps(rewards, ensure_ascii=False),
                battle_log=battle_result["battle_log"],
            )
            self.db.add(battle)

            all_results.append({"sect_id": sect_id, "action": action, "result": battle_result, "valid": True})

        # 6e. 其他行动
        for sect_id, action in other_actions:
            sect = sect_states.get(sect_id)
            if not sect:
                continue
            is_valid, reason = self.rule_engine.validate_action(action, sect, world_state)
            if is_valid:
                # 消耗行动点
                cost = self.rule_engine.ACTION_COSTS.get(action.get("type", ""), 1)
                sect["action_points"] = max(0, sect.get("action_points", 0) - cost)
                # 统一扣除资源
                self.rule_engine.deduct_cost(sect, action.get("type", ""))
                result = self.rule_engine.resolve_action(action, sect, world_state)
                self.rule_engine.apply_effects(sect["resources"], sect["stats"], result.get("effects", {}))
                all_results.append({"sect_id": sect_id, "action": action, "result": result, "valid": True})
            else:
                all_results.append({"sect_id": sect_id, "action": action, "result": {"log": reason}, "valid": False})

        # 7. 宗门事件
        for sect_id, sect in sect_states.items():
            sect_events = self.event_engine.generate_sect_events(sect, turn, world.world_seed)
            for evt in sect_events:
                # 应用事件效果到世界状态
                self.event_engine.apply_event_effects(evt, sect_states)
                we = WorldEvent(
                    id=uuid.uuid4().hex[:12],
                    world_id=world_id,
                    turn=turn,
                    event_type=evt["type"],
                    title=evt["title"],
                    description=evt["description"],
                    severity=evt["severity"],
                    affected_sects_json=json.dumps(evt.get("affected_sects", []), ensure_ascii=False),
                    affected_regions_json=json.dumps([], ensure_ascii=False),
                    tags_json=json.dumps([], ensure_ascii=False),
                    raw_result_json=json.dumps(evt, ensure_ascii=False),
                )
                self.db.add(we)

        # 7b. 世界事件
        for evt in world_events:
            # 应用世界事件效果
            self.event_engine.apply_event_effects(evt, sect_states)
            we = WorldEvent(
                id=uuid.uuid4().hex[:12],
                world_id=world_id,
                turn=turn,
                event_type=evt["type"],
                title=evt["title"],
                description=evt["description"],
                severity=evt["severity"],
                affected_sects_json=json.dumps(evt.get("affected_sects", []), ensure_ascii=False),
                affected_regions_json=json.dumps(evt.get("affected_regions", []), ensure_ascii=False),
                tags_json=json.dumps([], ensure_ascii=False),
                raw_result_json=json.dumps(evt, ensure_ascii=False),
            )
            self.db.add(we)

        # 8. 吞并检查
        self._check_annexation(sect_states, diplomacy, turn, world_id)

        # 9. 保存宗门状态
        for s in sects:
            if s.id in sect_states:
                st = sect_states[s.id]
                s.status = st.get("status", s.status)
                s.resources_json = json.dumps(st["resources"], ensure_ascii=False)
                s.stats_json = json.dumps(st["stats"], ensure_ascii=False)
                s.controlled_regions_json = json.dumps(st["controlled_regions"], ensure_ascii=False)
                s.strategy_summary = all_actions.get(s.id, {}).get("strategy_summary", "")
                # 更新记忆
                memory = json.loads(s.memory_json or "[]")
                for r in all_results:
                    if r["sect_id"] == s.id and r["valid"]:
                        memory.append({
                            "turn": turn,
                            "action": r["action"].get("type"),
                            "result": r["result"].get("log", ""),
                            "importance": 0.5,
                        })
                if len(memory) > 30:
                    memory = memory[-30:]
                s.memory_json = json.dumps(memory, ensure_ascii=False)

        # 10. 保存区域状态
        for r in regions:
            if r.id in region_states:
                r.owner_sect_id = region_states[r.id].get("owner_sect_id")

        # 11. 保存回合记录
        turn_record = TurnRecord(
            id=uuid.uuid4().hex[:12],
            world_id=world_id,
            turn=turn,
            status="completed",
            input_snapshot_json=json.dumps(input_snapshot, ensure_ascii=False),
            agent_actions_json=json.dumps(all_actions, ensure_ascii=False, default=str),
            resolved_results_json=json.dumps(all_results, ensure_ascii=False, default=str),
            summary=self._generate_turn_summary(all_results, world_events, turn),
        )
        self.db.add(turn_record)

        # 12. 更新世界状态
        world.current_turn = turn
        world.updated_at = datetime.now(timezone.utc)

        # 检查结束条件
        active_sects = [s for s in sect_states.values() if s.get("status") == "active"]
        if len(active_sects) <= 1:
            world.status = "finished"
        elif world.max_turns and turn >= world.max_turns:
            world.status = "finished"

        self.db.commit()

        return {
            "turn": turn,
            "world_status": world.status,
            "actions_count": len(all_actions),
            "results_count": len(all_results),
            "events_count": len(world_events),
            "summary": turn_record.summary,
        }

    def _build_world_state(self, sects: list, regions: list, diplomacy: list) -> dict:
        return {
            "sects": [self._load_sect_dict(s) for s in sects],
            "regions": [self._load_region_dict(r) for r in regions],
            "diplomacy": [self._load_relation_dict(r) for r in diplomacy],
        }

    def _build_sect_state(self, sect: Sect, regions: list, world_state: dict) -> dict:
        state = self._load_sect_dict(sect)
        state["action_points"] = 3
        state["active_treaties"] = []
        return state

    def _build_snapshot(self, sects: list, regions: list, diplomacy: list) -> dict:
        return {
            "sects": [self._load_sect_dict(s) for s in sects],
            "regions": [self._load_region_dict(r) for r in regions],
            "diplomacy": [self._load_relation_dict(r) for r in diplomacy],
        }

    def _load_sect_dict(self, sect: Sect) -> dict:
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

    def _load_region_dict(self, region: Region) -> dict:
        return {
            "id": region.id,
            "name": region.name,
            "region_type": region.region_type,
            "owner_sect_id": region.owner_sect_id,
            "resource_level": region.resource_level,
            "defense_level": region.defense_level,
            "stability": region.stability,
            "neighbors": json.loads(region.neighbors_json or "[]"),
        }

    def _load_relation_dict(self, rel: DiplomacyRelation) -> dict:
        return {
            "id": rel.id,
            "sect_a_id": rel.sect_a_id,
            "sect_b_id": rel.sect_b_id,
            "relation_type": rel.relation_type,
            "relation_score": rel.relation_score,
            "trust_score": rel.trust_score,
            "treaties": json.loads(rel.treaties_json or "[]"),
            "history": json.loads(rel.history_json or "[]"),
        }

    def _find_diplomacy_relation(self, diplomacy: list, a_id: str, b_id: str):
        for rel in diplomacy:
            if (rel.sect_a_id == a_id and rel.sect_b_id == b_id) or \
               (rel.sect_a_id == b_id and rel.sect_b_id == a_id):
                return rel
        return None

    def _check_annexation(self, sect_states: dict, diplomacy: list, turn: int, world_id: str):
        """检查吞并条件"""
        for sid, sect in sect_states.items():
            if sect.get("status") != "active":
                continue
            military = sect["stats"].get("military_power", 0)
            if military < 20:
                continue
            for tid, target in sect_states.items():
                if tid == sid or target.get("status") != "active":
                    continue
                target_military = target["stats"].get("military_power", 0)
                if military > target_military * 3 and len(target.get("controlled_regions", [])) <= 1:
                    # 吞并
                    target["status"] = "annexed"
                    for rid in target.get("controlled_regions", []):
                        if rid not in sect["controlled_regions"]:
                            sect["controlled_regions"].append(rid)
                    sect["stats"]["stability"] = max(0.1, sect["stats"].get("stability", 0.5) - 0.2)
                    evt = WorldEvent(
                        id=uuid.uuid4().hex[:12],
                        world_id=world_id,
                        turn=turn,
                        event_type="annexation",
                        title="宗门吞并",
                        description=f"{sect['name']} 吞并了 {target['name']}！",
                        severity=0.9,
                        affected_sects_json=json.dumps([sid, tid], ensure_ascii=False),
                        affected_regions_json=json.dumps([], ensure_ascii=False),
                        tags_json=json.dumps(["吞并", "灭门"], ensure_ascii=False),
                        raw_result_json=json.dumps({}, ensure_ascii=False),
                    )
                    self.db.add(evt)

    def _generate_turn_summary(self, results: list, events: list, turn: int) -> str:
        """生成回合摘要"""
        war_results = [r for r in results if r.get("action", {}).get("type") == "declare_war"]
        dip_results = [r for r in results if r.get("action", {}).get("type") == "diplomacy_offer"]
        parts = [f"第 {turn} 回合"]
        if war_results:
            parts.append(f"发生了 {len(war_results)} 场战争")
        if dip_results:
            success = sum(1 for r in dip_results if r.get("result", {}).get("success"))
            parts.append(f"{success}/{len(dip_results)} 次外交成功")
        if events:
            parts.append(f"触发了 {len(events)} 个世界事件")
        return "，".join(parts) + "。"