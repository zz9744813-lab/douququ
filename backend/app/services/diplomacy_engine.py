"""
Diplomacy Engine - 外交引擎
负责外交谈判成功率计算、关系变化、联盟/背叛/条约管理
"""
import random
import math
from typing import Any


class DiplomacyEngine:
    """外交引擎：处理宗门间外交关系"""

    RELATION_TYPES = [
        "neutral", "friendly", "trade", "non_aggression",
        "alliance", "vassal", "hostile", "war", "mortal_enemy",
    ]

    @staticmethod
    def calculate_diplomacy_success(
        offer_type: str,
        from_sect: dict,
        to_sect: dict,
        current_relation: dict,
        world_state: dict,
    ) -> float:
        """
        计算外交提案成功率，返回 0-1 之间的概率。
        """
        base = 0.3
        relation_score = current_relation.get("relation_score", 0)
        trust_score = current_relation.get("trust_score", 0.5)

        # 关系加成
        relation_bonus = relation_score * 0.3

        # 共同敌人加成
        from_enemies = set(from_sect.get("enemy_sects", []))
        to_enemies = set(to_sect.get("enemy_sects", []))
        common_enemies = len(from_enemies & to_enemies)
        enemy_bonus = min(common_enemies * 0.15, 0.3)

        # 实力差距 - 对强者更有利
        from_power = from_sect.get("stats", {}).get("military_power", 50)
        to_power = to_sect.get("stats", {}).get("military_power", 50)
        power_ratio = from_power / max(to_power, 1)
        power_bonus = min((power_ratio - 1) * 0.1, 0.2)

        # 信誉惩罚
        from_trust = from_sect.get("stats", {}).get("trustworthiness", 0.5)
        trust_penalty = (1 - from_trust) * 0.2

        # 性格修正
        to_personality = to_sect.get("personality", {})
        to_diplomacy = to_personality.get("diplomacy", 0.5)
        to_paranoia = to_personality.get("paranoia", 0.5)
        personality_bonus = to_diplomacy * 0.15 - to_paranoia * 0.1

        # 提案类型修正
        offer_modifiers = {
            "trade": 0.15,
            "non_aggression_pact": 0.05,
            "alliance": -0.1,
            "vassal_offer": -0.2,
            "ceasefire": 0.1,
            "threat": -0.15,
        }
        offer_mod = offer_modifiers.get(offer_type, 0)

        success_rate = base + relation_bonus + enemy_bonus + power_bonus - trust_penalty + personality_bonus + offer_mod
        return max(0.05, min(0.95, success_rate))

    @staticmethod
    def resolve_diplomacy(
        offer_type: str,
        from_sect: dict,
        to_sect: dict,
        current_relation: dict,
        world_state: dict,
    ) -> dict:
        """
        结算外交行动，返回结果。
        """
        success_rate = DiplomacyEngine.calculate_diplomacy_success(
            offer_type, from_sect, to_sect, current_relation, world_state
        )
        roll = random.random()
        success = roll < success_rate

        relation_changes = {
            "trade": (0.1, 0.05),
            "non_aggression_pact": (0.15, 0.05),
            "alliance": (0.3, 0.1),
            "vassal_offer": (0.0, -0.1),
            "ceasefire": (0.2, 0.0),
            "threat": (-0.2, -0.1),
        }
        change_success, change_fail = relation_changes.get(offer_type, (0.05, 0.0))

        new_relation_type = current_relation.get("relation_type", "neutral")
        if success:
            type_map = {
                "trade": "trade",
                "non_aggression_pact": "non_aggression",
                "alliance": "alliance",
                "vassal_offer": "vassal",
                "ceasefire": "neutral",
                "threat": "hostile",
            }
            new_relation_type = type_map.get(offer_type, current_relation.get("relation_type", "neutral"))

        return {
            "success": success,
            "success_rate": round(success_rate, 2),
            "new_relation_type": new_relation_type,
            "relation_change": change_success if success else change_fail,
            "log": DiplomacyEngine._generate_diplomacy_log(
                offer_type, success, from_sect.get("name", ""), to_sect.get("name", "")
            ),
        }

    @staticmethod
    def _generate_diplomacy_log(offer_type: str, success: bool, from_name: str, to_name: str) -> str:
        type_names = {
            "trade": "贸易协议",
            "non_aggression_pact": "互不侵犯条约",
            "alliance": "结盟",
            "vassal_offer": "附庸关系",
            "ceasefire": "停战协议",
            "threat": "威胁",
        }
        type_name = type_names.get(offer_type, "外交提案")
        if success:
            return f"【外交成功】{from_name} 向 {to_name} 提出的{type_name}被接受！"
        else:
            return f"【外交失败】{from_name} 向 {to_name} 提出的{type_name}被拒绝。"

    @staticmethod
    def check_betrayal_risk(sect: dict, ally_relations: list[dict]) -> list[dict]:
        """检查背叛风险。返回可能背叛的宗门列表。"""
        risks = []
        personality = sect.get("personality", {})
        honor = personality.get("honor", 0.5)
        ambition = personality.get("ambition", 0.5)
        greed = personality.get("greed", 0.5)

        for rel in ally_relations:
            if rel.get("relation_type") == "alliance":
                # 低信誉 + 高野心 + 高贪婪 = 高背叛风险
                risk = (1 - honor) * 0.5 + ambition * 0.3 + greed * 0.2
                if risk > 0.6:
                    risks.append({"target_id": rel.get("sect_b_id") or rel.get("sect_a_id"), "risk": round(risk, 2)})
        return risks