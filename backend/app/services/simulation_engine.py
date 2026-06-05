"""
Simulation Engine - 核心模拟引擎
整合规则、战斗、外交、事件、角色、LLM Agent
"""
import json
import random
from typing import Any
from sqlalchemy.orm import Session

from app.models.world import World
from app.models.sect import Sect
from app.models.region import Region
from app.models.event import WorldEvent
from app.models.turn import TurnRecord
from app.models.battle import Battle
from app.models.character import Character
from app.services.rule_engine import RuleEngine
from app.services.battle_engine import BattleEngine
from app.services.battle_replay_engine import BattleReplayEngine
from app.services.diplomacy_engine import DiplomacyEngine
from app.services.event_engine import EventEngine
from app.services.default_ai import DefaultAI
from app.services.llm_router import LLMRouter
from app.services.character_engine import CharacterEngine


class SimulationEngine:
    """核心模拟引擎"""

    def __init__(self, db: Session, use_llm: bool = False):
        self.db = db
        self.rule_engine = RuleEngine()
        self.battle_engine = BattleEngine()
        self.battle_replay_engine = BattleReplayEngine()
        self.diplomacy_engine = DiplomacyEngine()
        self.event_engine = EventEngine()
        self.default_ai = DefaultAI()
        self.llm_router = LLMRouter(db) if use_llm else None
        self.use_llm = use_llm
        self.character_engine = CharacterEngine()

    async def run_turn(self, world_id: str) -> dict:
        """运行一个完整回合"""
        world = self.db.query(World).filter(World.id == world_id).first()
        if not world:
            return {"error": "World not found"}

        turn = world.current_turn + 1
        if world.max_turns and turn > world.max_turns:
            world.status = "finished"
            self.db.commit()
            return {"error": "World has reached max turns"}

        # 加载世界状态
        sects = self.db.query(Sect).filter(Sect.world_id == world_id, Sect.status == "active").all()
        regions = self.db.query(Region).filter(Region.world_id == world_id).all()
        diplomacy = world.diplomacy_relations

        # 构建世界状态快照
        world_state = self._build_world_state(sects, regions, diplomacy, turn)

        # 1. 生成世界事件
        events = self.event_engine.generate_events(world_state, turn)

        # 2. 处理世界事件效果
        for event in events:
            effects = event.get("effects", {})
            for sect_id, effect in effects.items():
                sect = next((s for s in sects if s.id == sect_id), None)
                if sect:
                    self._apply_event_effect(sect, effect)

            # 保存事件
            world_event = WorldEvent(
                world_id=world_id,
                turn=turn,
                event_type=event["type"],
                title=event["title"],
                description=event["description"],
                severity=event.get("severity", 0.5),
                affected_sects_json=json.dumps(event.get("affected_sects", [])),
                effects_json=json.dumps(event.get("effects", {})),
            )
            self.db.add(world_event)

        # 3. 外交阶段
        diplomacy_results = []
        for rel in diplomacy:
            if rel.relation_type in ("alliance", "trade"):
                result = self.diplomacy_engine.process_diplomacy(rel, world_state)
                if result:
                    diplomacy_results.append(result)
                    # 更新关系
                    rel.relation_score = max(-1, min(1, rel.relation_score + result.get("score_change", 0)))
                    history = json.loads(rel.history_json or "[]")
                    history.append({
                        "turn": turn,
                        "action": result.get("action", "unknown"),
                        "success": result.get("success", False),
                        "score_change": result.get("score_change", 0),
                    })
                    rel.history_json = json.dumps(history)

        # 4. 各宗门生成行动（支持 LLM Router 异步并行）
        all_actions = {}
        if self.use_llm and self.llm_router:
            # 并行调用 LLM Router
            import asyncio
            tasks = []
            for sect in sects:
                sect_state = self._build_sect_state(sect, regions, world_state)
                messages = self._build_agent_messages(sect_state, world_state)
                tasks.append(self.llm_router.run_agent(
                    world_id=world_id,
                    sect_id=sect.id,
                    agent_role="sect_master",
                    messages=messages,
                ))
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
                elif isinstance(result, dict) and result.get("fallback"):
                    # LLMRouter 返回 fallback（所有模型都失败）
                    ai_output = self.default_ai.generate_actions(
                        self._build_sect_state(sect, regions, world_state), world_state, max_actions=3
                    )
                    ai_output["source"] = "fallback_no_model"
                    ai_output["llm_error"] = result.get("last_error", "无可用模型")
                    all_actions[sect.id] = ai_output
                else:
                    # LLM 成功返回，解析为行动格式
                    ai_output = self._parse_llm_output(result, sect)
                    ai_output["source"] = "llm"
                    all_actions[sect.id] = ai_output
        else:
            for sect in sects:
                sect_state = self._build_sect_state(sect, regions, world_state)
                ai_output = self.default_ai.generate_actions(sect_state, world_state, max_actions=3)
                all_actions[sect.id] = ai_output

        # 5. 执行行动
        results = []
        for sect in sects:
            actions = all_actions.get(sect.id, {}).get("actions", [])
            action_points = 3
            for action in actions:
                if action_points <= 0:
                    break
                cost = self.rule_engine.get_action_cost(action["type"])
                if action_points >= cost:
                    action_points -= cost
                    result = self._execute_action(sect, action, world_state, regions, diplomacy, turn)
                    if result:
                        results.append(result)

        # 6. 角色日常事件
        for sect in sects:
            chars = self._get_sect_characters(sect.id)
            rng = random.Random(world.world_seed + turn + hash(sect.id))
            char_events = self.character_engine.generate_character_events(chars, turn, rng)
            for evt in char_events:
                world_event = WorldEvent(
                    world_id=world_id,
                    turn=turn,
                    event_type=evt["event_type"],
                    title=evt["title"],
                    description=evt["description"],
                    severity=0.6,
                    affected_sects_json=json.dumps([sect.id]),
                )
                self.db.add(world_event)

        # 7. 结算和更新
        for sect in sects:
            # 资源自然增长
            resources = json.loads(sect.resources_json or "{}")
            resources["spirit_stones"] = resources.get("spirit_stones", 0) + random.randint(5, 15)
            resources["herbs"] = resources.get("herbs", 0) + random.randint(2, 8)
            resources["ores"] = resources.get("ores", 0) + random.randint(2, 8)
            sect.resources_json = json.dumps(resources)

            # 稳定性恢复
            stats = json.loads(sect.stats_json or "{}")
            stats["stability"] = min(1.0, stats.get("stability", 0.5) + 0.02)
            sect.stats_json = json.dumps(stats)

        # 8. 检查宗门吞并
        for sect in sects:
            stats = json.loads(sect.stats_json or "{}")
            if stats.get("stability", 1) <= 0.1 or stats.get("military_power", 50) <= 0:
                sect.status = "annexed"
                # 触发吞并事件
                world_event = WorldEvent(
                    world_id=world_id,
                    turn=turn,
                    event_type="annexation",
                    title=f"{sect.name} 被吞并",
                    description=f"{sect.name} 因内忧外患，最终走向灭亡。",
                    severity=1.0,
                    affected_sects_json=json.dumps([sect.id]),
                )
                self.db.add(world_event)

        # 9. 保存回合记录
        summary = self._generate_turn_summary(results, events, turn)
        turn_record = TurnRecord(
            world_id=world_id,
            turn=turn,
            summary=summary,
            events_json=json.dumps(events, ensure_ascii=False),
            actions_json=json.dumps(all_actions, ensure_ascii=False, default=str),
        )
        self.db.add(turn_record)

        world.current_turn = turn
        if world.max_turns and world.current_turn >= world.max_turns:
            world.status = "finished"

        self.db.commit()

        return {
            "turn": turn,
            "summary": summary,
            "events": events,
            "results": results,
            "world_status": world.status,
        }

    def _build_world_state(self, sects: list, regions: list, diplomacy: list, turn: int) -> dict:
        """构建世界状态快照"""
        return {
            "turn": turn,
            "sects": [
                {
                    "id": s.id,
                    "name": s.name,
                    "sect_type": s.sect_type,
                    "status": s.status,
                    "resources": json.loads(s.resources_json or "{}"),
                    "stats": json.loads(s.stats_json or "{}"),
                    "controlled_regions": json.loads(s.controlled_regions_json or "[]"),
                    "leader_name": s.leader_name,
                    "model_name": s.model_name,
                }
                for s in sects
            ],
            "regions": [
                {
                    "id": r.id,
                    "name": r.name,
                    "region_type": r.region_type,
                    "owner_sect_id": r.owner_sect_id,
                    "resources": json.loads(r.resources_json or "{}"),
                    "position": json.loads(r.position_json or "{}"),
                }
                for r in regions
            ],
            "diplomacy": [
                {
                    "sect_a_id": d.sect_a_id,
                    "sect_b_id": d.sect_b_id,
                    "relation_type": d.relation_type,
                    "relation_score": d.relation_score,
                }
                for d in diplomacy
            ],
        }

    def _build_sect_state(self, sect: Sect, regions: list, world_state: dict) -> dict:
        """构建单个宗门状态"""
        return {
            "id": sect.id,
            "name": sect.name,
            "sect_type": sect.sect_type,
            "resources": json.loads(sect.resources_json or "{}"),
            "stats": json.loads(sect.stats_json or "{}"),
            "controlled_regions": json.loads(sect.controlled_regions_json or "[]"),
            "leader_name": sect.leader_name,
            "model_name": sect.model_name,
            "personality": sect.personality,
            "neighbors": self._get_neighbors(sect, regions),
        }

    def _get_neighbors(self, sect: Sect, regions: list) -> list:
        """获取相邻宗门"""
        controlled = json.loads(sect.controlled_regions_json or "[]")
        neighbor_ids = set()
        for region in regions:
            if region.id in controlled:
                adj = json.loads(region.adjacent_regions_json or "[]")
                for adj_id in adj:
                    adj_region = next((r for r in regions if r.id == adj_id), None)
                    if adj_region and adj_region.owner_sect_id and adj_region.owner_sect_id != sect.id:
                        neighbor_ids.add(adj_region.owner_sect_id)
        return list(neighbor_ids)

    def _apply_event_effect(self, sect: Sect, effect: dict):
        """应用事件效果"""
        resources = json.loads(sect.resources_json or "{}")
        stats = json.loads(sect.stats_json or "{}")

        if "resource_change" in effect:
            for res, delta in effect["resource_change"].items():
                resources[res] = resources.get(res, 0) + delta
        if "stat_change" in effect:
            for stat, delta in effect["stat_change"].items():
                stats[stat] = max(0, min(1, stats.get(stat, 0.5) + delta))

        sect.resources_json = json.dumps(resources)
        sect.stats_json = json.dumps(stats)

    def _execute_action(self, sect: Sect, action: dict, world_state: dict, regions: list, diplomacy: list, turn: int) -> dict | None:
        """执行单个行动"""
        action_type = action.get("type", "rest")
        target_id = action.get("target_sect_id")
        target = next((s for s in world_state["sects"] if s["id"] == target_id), None) if target_id else None

        if action_type == "declare_war" and target_id:
            return self._execute_war(sect, target, world_state, regions, diplomacy, turn)
        elif action_type == "diplomacy_offer" and target_id:
            return self._execute_diplomacy(sect, target, action, diplomacy, turn)
        elif action_type == "build_structure":
            return self._execute_build(sect, action, turn)
        elif action_type == "train_disciples":
            return self._execute_train(sect, action, turn)
        elif action_type == "make_pills":
            return self._execute_make_pills(sect, action, turn)
        elif action_type == "craft_artifacts":
            return self._execute_craft(sect, action, turn)
        elif action_type == "gather_intel":
            return self._execute_intel(sect, action, turn)
        elif action_type == "rest":
            return self._execute_rest(sect, turn)
        return None

    def _execute_war(self, sect: Sect, target: dict, world_state: dict, regions: list, diplomacy: list, turn: int) -> dict:
        """执行战争"""
        target_sect = self.db.query(Sect).filter(Sect.id == target["id"]).first()
        if not target_sect or target_sect.status != "active":
            return None

        # 检查是否已处于战争状态
        existing_war = any(
            d for d in diplomacy
            if ((d.sect_a_id == sect.id and d.sect_b_id == target["id"]) or
                (d.sect_a_id == target["id"] and d.sect_b_id == sect.id))
            and d.relation_type == "war"
        )
        if existing_war:
            return None

        # 结算战争
        region_id = None
        target_regions = json.loads(target_sect.controlled_regions_json or "[]")
        if target_regions:
            region_id = target_regions[0]
        region = self.db.query(Region).filter(Region.id == region_id).first() if region_id else None

        battle_result = self.battle_engine.resolve_battle(sect, target_sect, region)

        # 应用伤亡
        sect_stats = json.loads(sect.stats_json or "{}")
        target_stats = json.loads(target_sect.stats_json or "{}")
        sect_stats["military_power"] = max(0, sect_stats.get("military_power", 0) - battle_result["losses"]["attacker_loss"])
        target_stats["military_power"] = max(0, target_stats.get("military_power", 0) - battle_result["losses"]["defender_loss"])
        sect.stats_json = json.dumps(sect_stats)
        target_sect.stats_json = json.dumps(target_stats)

        # 处理奖励
        rewards = battle_result["rewards"]
        if rewards.get("spirit_stones", 0) > 0:
            sect_resources = json.loads(sect.resources_json or "{}")
            target_resources = json.loads(target_sect.resources_json or "{}")
            sect_resources["spirit_stones"] = sect_resources.get("spirit_stones", 0) + rewards["spirit_stones"]
            target_resources["spirit_stones"] = max(0, target_resources.get("spirit_stones", 0) - rewards["spirit_stones"])
            sect.resources_json = json.dumps(sect_resources)
            target_sect.resources_json = json.dumps(target_resources)

        # 占领区域
        for rid in rewards.get("regions_captured", []):
            captured_region = self.db.query(Region).filter(Region.id == rid).first()
            if captured_region:
                captured_region.owner_sect_id = sect.id
                sect_regions = json.loads(sect.controlled_regions_json or "[]")
                if rid not in sect_regions:
                    sect_regions.append(rid)
                sect.controlled_regions_json = json.dumps(sect_regions)
                target_regions_list = json.loads(target_sect.controlled_regions_json or "[]")
                if rid in target_regions_list:
                    target_regions_list.remove(rid)
                target_sect.controlled_regions_json = json.dumps(target_regions_list)

        # 更新外交关系
        rel = self._find_diplomacy_relation(diplomacy, sect.id, target["id"])
        if rel:
            rel.relation_type = "war"
            rel.relation_score = min(rel.relation_score, -0.5)

        # 获取角色并生成角色战斗事件
        attacker_chars = self._get_sect_characters(sect.id)
        defender_chars = self._get_sect_characters(target["id"])
        rng = random.Random(turn + hash(sect.id))
        char_events = self.character_engine.generate_battle_character_events(
            attacker_chars, defender_chars, battle_result, rng
        )

        # 生成战斗回放（含角色事件）
        replay = self.battle_replay_engine.generate_replay(
            {"name": sect.name, "id": sect.id},
            {"name": target_sect.name, "id": target_sect.id},
            {"name": region.name, "id": region.id} if region else None,
            battle_result,
            char_events,
        )
        battle_result["replay"] = replay
        battle_result["character_events"] = char_events
        battle_result["highlights"] = self.battle_replay_engine.generate_highlights(replay)

        # 保存战斗记录
        battle = Battle(
            world_id=sect.world_id,
            turn=turn,
            attacker_sect_id=sect.id,
            defender_sect_id=target["id"],
            winner_sect_id=battle_result.get("winner_sect_id"),
            result_type=battle_result["result_type"],
            battle_log=battle_result["log"],
            attacker_power=battle_result["attacker_power"],
            defender_power=battle_result["defender_power"],
            losses_json=json.dumps(battle_result["losses"]),
            rewards_json=json.dumps(battle_result["rewards"]),
            replay_json=json.dumps(replay, ensure_ascii=False),
        )
        self.db.add(battle)

        return {
            "action": {"type": "declare_war", "target_sect_id": target["id"]},
            "result": battle_result,
        }

    def _execute_diplomacy(self, sect: Sect, target: dict, action: dict, diplomacy: list, turn: int) -> dict:
        """执行外交"""
        target_sect = self.db.query(Sect).filter(Sect.id == target["id"]).first()
        if not target_sect:
            return None

        rel = self._find_diplomacy_relation(diplomacy, sect.id, target["id"])
        if not rel:
            return None

        offer_type = action.get("offer_type", "alliance")
        success = random.random() < 0.5 + (rel.relation_score * 0.3)

        if success:
            if offer_type == "alliance":
                rel.relation_type = "alliance"
                rel.relation_score = min(1.0, rel.relation_score + 0.3)
            elif offer_type == "trade":
                rel.relation_type = "trade"
                rel.relation_score = min(1.0, rel.relation_score + 0.2)
            elif offer_type == "non_aggression":
                rel.relation_type = "non_aggression"
                rel.relation_score = min(1.0, rel.relation_score + 0.15)

        history = json.loads(rel.history_json or "[]")
        history.append({
            "turn": turn,
            "action": offer_type,
            "success": success,
            "initiator": sect.id,
        })
        rel.history_json = json.dumps(history)

        return {
            "action": {"type": "diplomacy_offer", "target_sect_id": target["id"], "offer_type": offer_type},
            "result": {"success": success, "relation_type": rel.relation_type},
        }

    def _execute_build(self, sect: Sect, action: dict, turn: int) -> dict:
        resources = json.loads(sect.resources_json or "{}")
        stats = json.loads(sect.stats_json or "{}")
        cost = 50
        if resources.get("spirit_stones", 0) >= cost:
            resources["spirit_stones"] -= cost
            stats["stability"] = min(1.0, stats.get("stability", 0.5) + 0.05)
            sect.resources_json = json.dumps(resources)
            sect.stats_json = json.dumps(stats)
            return {"action": action, "result": {"success": True, "stability_gain": 0.05}}
        return {"action": action, "result": {"success": False, "reason": "资源不足"}}

    def _execute_train(self, sect: Sect, action: dict, turn: int) -> dict:
        resources = json.loads(sect.resources_json or "{}")
        stats = json.loads(sect.stats_json or "{}")
        cost = 30
        if resources.get("spirit_stones", 0) >= cost:
            resources["spirit_stones"] -= cost
            stats["military_power"] = stats.get("military_power", 50) + random.randint(5, 15)
            sect.resources_json = json.dumps(resources)
            sect.stats_json = json.dumps(stats)
            return {"action": action, "result": {"success": True, "military_gain": random.randint(5, 15)}}
        return {"action": action, "result": {"success": False, "reason": "资源不足"}}

    def _execute_make_pills(self, sect: Sect, action: dict, turn: int) -> dict:
        resources = json.loads(sect.resources_json or "{}")
        if resources.get("herbs", 0) >= 10:
            resources["herbs"] -= 10
            resources["spirit_stones"] = resources.get("spirit_stones", 0) + random.randint(20, 50)
            sect.resources_json = json.dumps(resources)
            return {"action": action, "result": {"success": True, "income": random.randint(20, 50)}}
        return {"action": action, "result": {"success": False, "reason": "草药不足"}}

    def _execute_craft(self, sect: Sect, action: dict, turn: int) -> dict:
        resources = json.loads(sect.resources_json or "{}")
        if resources.get("ores", 0) >= 10:
            resources["ores"] -= 10
            resources["spirit_stones"] = resources.get("spirit_stones", 0) + random.randint(15, 40)
            sect.resources_json = json.dumps(resources)
            return {"action": action, "result": {"success": True, "income": random.randint(15, 40)}}
        return {"action": action, "result": {"success": False, "reason": "矿石不足"}}

    def _execute_intel(self, sect: Sect, action: dict, turn: int) -> dict:
        return {"action": action, "result": {"success": True, "intel": "收集到附近宗门的情报"}}

    def _execute_rest(self, sect: Sect, turn: int) -> dict:
        resources = json.loads(sect.resources_json or "{}")
        stats = json.loads(sect.stats_json or "{}")
        resources["spirit_stones"] = resources.get("spirit_stones", 0) + random.randint(10, 25)
        stats["stability"] = min(1.0, stats.get("stability", 0.5) + 0.03)
        sect.resources_json = json.dumps(resources)
        sect.stats_json = json.dumps(stats)
        return {"action": {"type": "rest"}, "result": {"success": True, "recovery": "宗门休养生息"}}

    def _get_sect_characters(self, sect_id: str) -> list[dict]:
        """获取宗门角色列表"""
        chars = self.db.query(Character).filter(Character.sect_id == sect_id).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "role": c.role,
                "realm": c.realm,
                "combat_power": c.combat_power,
                "loyalty": c.loyalty,
                "ambition": c.ambition,
                "luck": c.luck,
                "status": c.status,
            }
            for c in chars
        ]

    def _find_diplomacy_relation(self, diplomacy: list, a_id: str, b_id: str):
        for rel in diplomacy:
            if (rel.sect_a_id == a_id and rel.sect_b_id == b_id) or \
               (rel.sect_a_id == b_id and rel.sect_b_id == a_id):
                return rel
        return None

    def _build_agent_messages(self, sect_state: dict, world_state: dict) -> list[dict]:
        """构建 LLM Agent 的 messages"""
        system_prompt = """你是一位修仙宗门的掌门 Agent。你必须根据宗门性格、当前资源、外交关系、地图局势做出本回合战略决策。
你必须输出合法 JSON，格式如下：
{
  "strategy_summary": "本回合战略摘要，不超过80字",
  "actions": [
    {
      "type": "declare_war|diplomacy_offer|build_structure|train_disciples|make_pills|craft_artifacts|gather_intel|rest",
      "target_sect_id": "目标宗门ID或null",
      "target_region_id": "目标区域ID或null",
      "intensity": "low|medium|high",
      "message": "行动描述"
    }
  ]
}
可选行动类型：
- declare_war: 宣战（消耗2行动点）
- diplomacy_offer: 外交提议（结盟/贸易/互不侵犯，消耗1行动点）
- build_structure: 建设设施（消耗1行动点）
- train_disciples: 训练弟子（消耗1行动点）
- make_pills: 炼丹（消耗1行动点）
- craft_artifacts: 炼器（消耗1行动点）
- gather_intel: 收集情报（消耗1行动点）
- rest: 休养生息（恢复资源，消耗0行动点）
每回合最多3个行动点。"""

        user_prompt = json.dumps({
            "self": sect_state,
            "world": {
                "sects": [s for s in world_state.get("sects", []) if s.get("id") != sect_state.get("id")],
                "regions": world_state.get("regions", []),
                "diplomacy": world_state.get("diplomacy", []),
            },
        }, ensure_ascii=False, default=str)

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _parse_llm_output(self, output: dict, sect: Sect) -> dict:
        """解析 LLM 输出为行动格式"""
        actions = []
        if isinstance(output, dict):
            raw_actions = output.get("actions", [])
            if isinstance(raw_actions, list):
                for a in raw_actions:
                    if isinstance(a, dict):
                        actions.append({
                            "type": a.get("type", "rest"),
                            "target_sect_id": a.get("target_sect_id"),
                            "target_region_id": a.get("target_region_id"),
                            "intensity": a.get("intensity", "medium"),
                            "message": a.get("message", ""),
                        })

        # 如果没有解析出行动，默认休息
        if not actions:
            actions = [{"type": "rest", "message": "休养生息"}]

        return {
            "strategy_summary": output.get("strategy_summary", "按兵不动") if isinstance(output, dict) else "按兵不动",
            "actions": actions[:3],  # 最多3个行动
        }

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
