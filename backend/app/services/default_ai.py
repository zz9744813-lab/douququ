"""
Default AI - 默认AI行动生成器
当不使用 LLM 时，使用规则驱动的 AI 生成宗门行动。
用于 MVP 测试和低成本运行。
"""
import random
from typing import Any


class DefaultAI:
    """默认规则 AI：根据宗门状态和性格生成行动"""

    ACTION_COSTS = {
        "train_disciples": 1, "build_structure": 2, "make_pills": 1,
        "craft_artifacts": 1, "explore_realm": 2, "diplomacy_offer": 1,
        "spy_gather": 1, "declare_war": 2, "subvert_elder": 2,
        "propaganda": 1, "rest": 0,
    }

    ACTION_TYPES = [
        "train_disciples", "build_structure", "make_pills",
        "craft_artifacts", "explore_realm",
        "spy_gather", "propaganda", "rest",
    ]

    AGGRESSIVE_ACTIONS = ["train_disciples", "explore_realm", "declare_war"]
    ECONOMIC_ACTIONS = ["build_structure", "make_pills", "craft_artifacts"]
    DIPLOMATIC_ACTIONS = ["diplomacy_offer", "propaganda", "spy_gather"]
    DEFENSIVE_ACTIONS = ["build_structure", "train_disciples", "rest"]

    @staticmethod
    def generate_actions(
        sect: dict,
        world_state: dict,
        max_actions: int = 3,
    ) -> dict:
        """
        根据宗门状态生成本回合行动。
        返回: {strategy_summary, actions: [...]}
        """
        personality = sect.get("personality", {})
        stats = sect.get("stats", {})
        resources = sect.get("resources", {})
        stats_v = {
            "military_power": stats.get("military_power", 50),
            "economy": stats.get("economy", 50),
            "reputation": stats.get("reputation", 50),
            "stability": stats.get("stability", 0.5),
            "intelligence": stats.get("intelligence", 30),
        }

        # 确定战略倾向
        strategy = DefaultAI._determine_strategy(personality, stats_v, resources)

        # 生成行动
        actions = []
        used_points = 0
        action_pool = DefaultAI._get_action_pool(strategy, personality, stats_v, resources)

        for _ in range(max_actions):
            if not action_pool:
                break
            action = random.choice(action_pool)
            action_type = action["type"]
            cost = DefaultAI.ACTION_COSTS.get(action_type, 1)
            if used_points + cost > max_actions:
                continue  # 行动点不够，跳过

            # 构建具体行动
            built_action = {"type": action_type, "intensity": DefaultAI._pick_intensity(personality)}

            if action_type == "diplomacy_offer":
                # 选择一个目标宗门
                targets = DefaultAI._find_diplomacy_targets(sect, world_state, personality)
                if targets:
                    target = random.choice(targets)
                    built_action["target_sect_id"] = target["id"]
                    built_action["offer_type"] = DefaultAI._pick_offer_type(personality, target)
                    built_action["message"] = f"愿与贵宗共商大计。"
                else:
                    built_action = {"type": "train_disciples", "intensity": "medium"}

            elif action_type == "declare_war":
                targets = DefaultAI._find_war_targets(sect, world_state, personality)
                if targets:
                    target = random.choice(targets)
                    built_action["target_sect_id"] = target["id"]
                    # 选择相邻区域
                    target_regions = [
                        r for r in world_state.get("regions", [])
                        if r.get("owner_sect_id") == target["id"]
                    ]
                    if target_regions:
                        built_action["target_region_id"] = random.choice(target_regions)["id"]
                else:
                    built_action = {"type": "train_disciples", "intensity": "high"}

            elif action_type == "explore_realm":
                # 选择探索区域
                unowned = [
                    r for r in world_state.get("regions", [])
                    if not r.get("owner_sect_id")
                ]
                if unowned:
                    built_action["target_region_id"] = random.choice(unowned)["id"]

            actions.append(built_action)
            used_points += cost

        strategy_summary = DefaultAI._generate_summary(strategy, actions, sect.get("name", ""))

        return {
            "strategy_summary": strategy_summary,
            "actions": actions,
        }

    @staticmethod
    def _determine_strategy(personality: dict, stats: dict, resources: dict) -> str:
        """确定战略倾向"""
        aggression = personality.get("aggression", 0.5)
        ambition = personality.get("ambition", 0.5)
        patience = personality.get("patience", 0.5)
        greed = personality.get("greed", 0.5)

        military = stats.get("military_power", 50)
        economy = stats.get("economy", 50)
        spirit_stones = resources.get("spirit_stones", 100)

        if aggression > 0.7 and military > 60:
            return "aggressive"
        elif ambition > 0.7 and economy > 50:
            return "expansion"
        elif greed > 0.7:
            return "greedy"
        elif patience > 0.7:
            return "defensive"
        elif spirit_stones < 100:
            return "recovery"
        else:
            return "balanced"

    @staticmethod
    def _get_action_pool(strategy: str, personality: dict, stats: dict, resources: dict) -> list[dict]:
        """根据策略获取行动池"""
        pools = {
            "aggressive": [
                {"type": "train_disciples", "weight": 3},
                {"type": "declare_war", "weight": 2},
                {"type": "explore_realm", "weight": 2},
                {"type": "craft_artifacts", "weight": 1},
                {"type": "spy_gather", "weight": 1},
            ],
            "expansion": [
                {"type": "build_structure", "weight": 2},
                {"type": "explore_realm", "weight": 2},
                {"type": "train_disciples", "weight": 2},
                {"type": "diplomacy_offer", "weight": 1},
                {"type": "propaganda", "weight": 1},
            ],
            "greedy": [
                {"type": "explore_realm", "weight": 3},
                {"type": "make_pills", "weight": 2},
                {"type": "craft_artifacts", "weight": 2},
                {"type": "spy_gather", "weight": 1},
            ],
            "defensive": [
                {"type": "build_structure", "weight": 3},
                {"type": "train_disciples", "weight": 2},
                {"type": "make_pills", "weight": 1},
                {"type": "propaganda", "weight": 1},
            ],
            "recovery": [
                {"type": "rest", "weight": 3},
                {"type": "build_structure", "weight": 2},
                {"type": "make_pills", "weight": 1},
            ],
            "balanced": [
                {"type": "train_disciples", "weight": 2},
                {"type": "build_structure", "weight": 2},
                {"type": "explore_realm", "weight": 1},
                {"type": "diplomacy_offer", "weight": 1},
                {"type": "make_pills", "weight": 1},
            ],
        }
        pool = pools.get(strategy, pools["balanced"])
        # 加权展开
        expanded = []
        for item in pool:
            for _ in range(item["weight"]):
                expanded.append({"type": item["type"]})
        return expanded

    @staticmethod
    def _pick_intensity(personality: dict) -> str:
        risk = personality.get("risk_tolerance", 0.5)
        if risk > 0.7:
            return random.choice(["high", "high", "medium"])
        elif risk < 0.3:
            return random.choice(["low", "low", "medium"])
        return "medium"

    @staticmethod
    def _find_diplomacy_targets(sect: dict, world_state: dict, personality: dict) -> list[dict]:
        """寻找外交目标"""
        targets = []
        my_id = sect.get("id")
        for other in world_state.get("sects", []):
            if other.get("id") == my_id or other.get("status") != "active":
                continue
            # 检查当前关系
            relation = next(
                (r for r in world_state.get("diplomacy", [])
                 if (r.get("sect_a_id") == my_id and r.get("sect_b_id") == other["id"])
                 or (r.get("sect_a_id") == other["id"] and r.get("sect_b_id") == my_id)),
                None,
            )
            if relation and relation.get("relation_type") in ("war", "mortal_enemy"):
                continue
            targets.append(other)
        return targets

    @staticmethod
    def _find_war_targets(sect: dict, world_state: dict, personality: dict) -> list[dict]:
        """寻找战争目标"""
        targets = []
        my_id = sect.get("id")
        my_power = sect.get("stats", {}).get("military_power", 50)
        for other in world_state.get("sects", []):
            if other.get("id") == my_id or other.get("status") != "active":
                continue
            other_power = other.get("stats", {}).get("military_power", 50)
            # 倾向于攻击比自己弱的
            if other_power < my_power * 1.1:
                targets.append(other)
        return targets

    @staticmethod
    def _pick_offer_type(personality: dict, target: dict) -> str:
        diplomacy = personality.get("diplomacy", 0.5)
        honor = personality.get("honor", 0.5)
        if diplomacy > 0.6:
            return random.choice(["trade", "non_aggression_pact", "alliance"])
        elif honor > 0.6:
            return "non_aggression_pact"
        return "trade"

    @staticmethod
    def _generate_summary(strategy: str, actions: list[dict], name: str) -> str:
        summaries = {
            "aggressive": f"{name} 本回合采取激进策略，积极备战。",
            "expansion": f"{name} 本回合致力于扩张势力。",
            "greedy": f"{name} 本回合重点搜刮资源。",
            "defensive": f"{name} 本回合固守求稳，积蓄力量。",
            "recovery": f"{name} 本回合休养生息，恢复元气。",
            "balanced": f"{name} 本回合均衡发展。",
        }
        return summaries.get(strategy, f"{name} 本回合按计划行动。")