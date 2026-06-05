"""
Rule Engine - 规则引擎
负责所有行动的合法性校验和资源结算。
LLM 不能直接修改世界状态，所有行动必须通过规则引擎。
"""
import json
import random
import math
from typing import Any


class RuleEngine:
    """核心规则引擎：校验、结算、资源计算"""

    # 行动类型及消耗
    ACTION_COSTS = {
        "train_disciples": 1,
        "build_structure": 2,
        "make_pills": 1,
        "craft_artifacts": 1,
        "explore_realm": 2,
        "diplomacy_offer": 1,
        "spy_gather": 1,
        "declare_war": 2,
        "subvert_elder": 2,
        "propaganda": 1,
        "rest": 0,
    }

    # 各行动的资源基础消耗
    ACTION_RESOURCE_COST = {
        "train_disciples": {"spirit_stones": 50},
        "build_structure": {"spirit_stones": 200},
        "make_pills": {"spirit_stones": 80, "spirit_herbs": 30},
        "craft_artifacts": {"spirit_stones": 100, "materials": 40},
        "explore_realm": {"spirit_stones": 60},
        "diplomacy_offer": {"spirit_stones": 30},
        "spy_gather": {"spirit_stones": 40},
        "declare_war": {"spirit_stones": 200},
        "subvert_elder": {"spirit_stones": 150},
        "propaganda": {"spirit_stones": 40},
        "rest": {},
    }

    @staticmethod
    def validate_action(action: dict, sect_state: dict, world_state: dict) -> tuple[bool, str]:
        """校验单个行动是否合法。返回 (合法, 原因)"""
        action_type = action.get("type", "")

        if action_type not in RuleEngine.ACTION_COSTS:
            return False, f"未知行动类型: {action_type}"

        # 检查资源是否足够
        resources = sect_state.get("resources", {})
        cost = RuleEngine.ACTION_RESOURCE_COST.get(action_type, {})
        for res_key, amount in cost.items():
            if resources.get(res_key, 0) < amount:
                return False, f"资源不足: {res_key} 需要 {amount}，当前 {resources.get(res_key, 0)}"

        # 检查行动点
        action_points = sect_state.get("action_points", 0)
        needed = RuleEngine.ACTION_COSTS.get(action_type, 1)
        if action_points < needed:
            return False, f"行动点不足: 需要 {needed}，当前 {action_points}"

        # 战争行动特殊校验
        if action_type == "declare_war":
            target_id = action.get("target_sect_id", "")
            if not target_id:
                return False, "战争需要指定目标宗门"
            if target_id == sect_state.get("id"):
                return False, "不能对自己发动战争"
            # 检查是否在停战期
            for treaty in sect_state.get("active_treaties", []):
                if treaty.get("target") == target_id and treaty.get("type") == "ceasefire":
                    return False, f"与目标宗门处于停战期，剩余 {treaty.get('remaining_turns', 0)} 回合"

        # 外交行动校验
        if action_type == "diplomacy_offer":
            target_id = action.get("target_sect_id", "")
            if not target_id:
                return False, "外交需要指定目标宗门"
            if target_id == sect_state.get("id"):
                return False, "不能对自己进行外交"

        return True, "合法"

    @staticmethod
    def resolve_action(action: dict, sect_state: dict, world_state: dict) -> dict:
        """结算单个行动，返回行动结果。资源消耗由 ACTION_RESOURCE_COST 统一扣除，这里只处理收益。"""
        action_type = action.get("type", "")
        intensity = action.get("intensity", "medium")
        result = {"action_type": action_type, "success": True, "effects": {}, "log": ""}

        intensity_mult = {"low": 0.5, "medium": 1.0, "high": 1.5}.get(intensity, 1.0)

        if action_type == "train_disciples":
            gain = int(10 * intensity_mult * random.uniform(0.8, 1.2))
            result["effects"] = {"military_power": gain}
            result["log"] = f"训练弟子，军事力量 +{gain}"

        elif action_type == "build_structure":
            gain = int(8 * intensity_mult * random.uniform(0.8, 1.2))
            result["effects"] = {"economy": gain}
            result["log"] = f"建设建筑，经济能力 +{gain}"

        elif action_type == "make_pills":
            gain = int(6 * intensity_mult * random.uniform(0.8, 1.2))
            result["effects"] = {"pills": gain}
            result["log"] = f"炼制丹药，获得 {gain} 枚丹药"

        elif action_type == "craft_artifacts":
            gain = int(5 * intensity_mult * random.uniform(0.8, 1.2))
            result["effects"] = {"artifacts": gain}
            result["log"] = f"炼制法器，获得 {gain} 件法器"

        elif action_type == "explore_realm":
            luck = random.uniform(0.5, 1.5)
            if luck > 1.2:
                gain = int(15 * intensity_mult)
                result["effects"] = {"spirit_stones": gain * 10, "techniques": random.randint(1, 3)}
                result["log"] = f"秘境探索大获成功！获得 {gain*10} 灵石和功法"
                result["tags"] = ["奇遇"]
            elif luck < 0.4:
                loss = int(5 * intensity_mult)
                result["effects"] = {"military_power": -loss}
                result["log"] = f"秘境探索遭遇危险，损失 {loss} 战力"
                result["success"] = False
            else:
                gain = int(8 * intensity_mult)
                result["effects"] = {"spirit_stones": gain * 5}
                result["log"] = f"秘境探索有所收获，获得 {gain*5} 灵石"

        elif action_type == "spy_gather":
            result["effects"] = {"intelligence": 5}
            result["log"] = "情报刺探成功，获得敌方动向信息"

        elif action_type == "propaganda":
            result["effects"] = {"reputation": 3}
            result["log"] = "宣传造势，声望提升"

        elif action_type == "rest":
            result["effects"] = {"spirit_stones": 20}
            result["log"] = "休养生息，恢复少量灵石"

        return result

    @staticmethod
    def deduct_cost(sect_state: dict, action_type: str) -> dict:
        """统一扣除行动成本。返回扣除的资源列表。"""
        resources = sect_state.get("resources", {})
        cost = RuleEngine.ACTION_RESOURCE_COST.get(action_type, {})
        deducted = {}
        for res_key, amount in cost.items():
            old = resources.get(res_key, 0)
            resources[res_key] = max(0, old - amount)
            deducted[res_key] = amount
        return deducted

    @staticmethod
    def apply_effects(sect_resources: dict, sect_stats: dict, effects: dict):
        """将行动效果应用到宗门状态"""
        stat_map = {
            "military_power": "military_power",
            "economy": "economy",
            "reputation": "reputation",
            "intelligence": "intelligence",
            "spiritual_power": "spiritual_power",
        }
        for key, value in effects.items():
            if key == "spirit_stones":
                sect_resources["spirit_stones"] = max(0, sect_resources.get("spirit_stones", 0) + value)
            elif key == "pills":
                sect_resources["pills"] = max(0, sect_resources.get("pills", 0) + value)
            elif key == "artifacts":
                sect_resources["artifacts"] = max(0, sect_resources.get("artifacts", 0) + value)
            elif key == "techniques":
                sect_resources["techniques"] = max(0, sect_resources.get("techniques", 0) + value)
            elif key in stat_map:
                sect_stats[stat_map[key]] = max(0, sect_stats.get(stat_map[key], 0) + value)

    @staticmethod
    def calculate_resource_production(sect: dict, regions: list[dict]) -> dict:
        """计算宗门每回合资源产出"""
        production = {
            "spirit_stones": 50,
            "spirit_herbs": 10,
            "materials": 10,
        }
        for region in regions:
            rl = region.get("resource_level", 1)
            rt = region.get("region_type", "wilderness")
            if rt == "spirit_mine":
                production["spirit_stones"] += 30 * rl
            elif rt == "spirit_vein":
                production["spirit_stones"] += 20 * rl
                production["spirit_herbs"] += 10 * rl
            elif rt == "mortal_city":
                production["spirit_stones"] += 15 * rl
                production["materials"] += 10 * rl
            elif rt == "sect_peak":
                production["spirit_stones"] += 25 * rl

        # 经济加成
        economy = sect.get("stats", {}).get("economy", 10)
        production["spirit_stones"] = int(production["spirit_stones"] * (1 + economy * 0.01))
        return production