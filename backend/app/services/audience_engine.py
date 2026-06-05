"""
Audience Engine - 观众互动引擎
天道干预、预测、镜头追踪等玩家互动功能
"""
import json
import random
from typing import Any


class AudienceEngine:
    """观众互动引擎：处理天道干预和预测"""

    INTERVENTION_COSTS = {
        "bless_sect": 50,      # 赐福宗门
        "curse_sect": 50,      # 降灾宗门
        "spawn_secret_realm": 100,  # 投放秘境
        "spawn_genius": 80,    # 天才出世
        "boost_luck": 60,      # 提升气运
        "trigger_heaven_trial": 120,  # 触发天劫
        "predict_winner": 10,  # 预测胜者
        "focus_camera": 5,     # 追踪镜头
        "peace_edict": 150,    # 和平令
        "reveal_secrets": 70,  # 观测令
    }

    @staticmethod
    def intervene(
        action_type: str,
        target_sect_id: str | None,
        target_region_id: str | None,
        world_state: dict,
        sect_states: dict,
    ) -> dict:
        """
        执行天道干预。
        返回: {success, result, message, cost}
        """
        cost = AudienceEngine.INTERVENTION_COSTS.get(action_type, 50)
        
        if action_type == "bless_sect" and target_sect_id:
            sect = sect_states.get(target_sect_id)
            if sect:
                sect["stats"]["luck"] = min(1.0, sect["stats"].get("luck", 0.5) + 0.15)
                sect["resources"]["spirit_stones"] = sect["resources"].get("spirit_stones", 0) + 200
                return {
                    "success": True,
                    "result": {"luck_boost": 0.15, "spirit_stones": 200},
                    "message": f"天道赐福 {sect['name']}，气运提升！",
                    "cost": cost,
                }

        elif action_type == "curse_sect" and target_sect_id:
            sect = sect_states.get(target_sect_id)
            if sect:
                sect["stats"]["luck"] = max(0.0, sect["stats"].get("luck", 0.5) - 0.2)
                sect["stats"]["stability"] = max(0.1, sect["stats"].get("stability", 0.5) - 0.1)
                return {
                    "success": True,
                    "result": {"luck_drop": 0.2, "stability_drop": 0.1},
                    "message": f"天道降灾 {sect['name']}，气运衰退！",
                    "cost": cost,
                }

        elif action_type == "spawn_secret_realm" and target_region_id:
            return {
                "success": True,
                "result": {"region_id": target_region_id, "event": "secret_realm"},
                "message": "天道在某处投放了一座上古秘境！",
                "cost": cost,
            }

        elif action_type == "spawn_genius" and target_sect_id:
            sect = sect_states.get(target_sect_id)
            if sect:
                return {
                    "success": True,
                    "result": {"sect_id": target_sect_id, "event": "genius_born"},
                    "message": f"一位天才弟子拜入 {sect['name']} 门下！",
                    "cost": cost,
                }

        elif action_type == "boost_luck" and target_sect_id:
            sect = sect_states.get(target_sect_id)
            if sect:
                sect["stats"]["luck"] = min(1.0, sect["stats"].get("luck", 0.5) + 0.25)
                return {
                    "success": True,
                    "result": {"luck_boost": 0.25},
                    "message": f"{sect['name']} 气运大涨！",
                    "cost": cost,
                }

        elif action_type == "trigger_heaven_trial" and target_sect_id:
            sect = sect_states.get(target_sect_id)
            if sect:
                sect["stats"]["military_power"] = max(1, int(sect["stats"].get("military_power", 50) * 0.8))
                return {
                    "success": True,
                    "result": {"military_drop": 0.2},
                    "message": f"天劫降临 {sect['name']}，宗门实力大损！",
                    "cost": cost,
                }

        elif action_type == "peace_edict":
            # 强制所有宗门停战1回合
            for sect in sect_states.values():
                sect["peace_edict"] = True
            return {
                "success": True,
                "result": {"peace_turns": 1},
                "message": "天道颁布和平令，所有宗门停战一回合！",
                "cost": cost,
            }

        elif action_type == "reveal_secrets" and target_sect_id:
            sect = sect_states.get(target_sect_id)
            if sect:
                return {
                    "success": True,
                    "result": {"sect_id": target_sect_id, "revealed": True},
                    "message": f"天道之眼洞察 {sect['name']} 的隐藏行动！",
                    "cost": cost,
                }

        return {
            "success": False,
            "result": {},
            "message": "干预失败，参数无效。",
            "cost": 0,
        }

    @staticmethod
    def predict(
        prediction_type: str,
        target_id: str,
        predicted_result: str,
        actual_result: str,
    ) -> dict:
        """
        结算预测。
        返回: {success, points_earned, message}
        """
        correct = predicted_result == actual_result
        points = 50 if correct else -10
        
        messages = {
            ("war_winner", True): "预测正确！你洞察了战局走向！",
            ("war_winner", False): "预测失误，战局变幻莫测...",
            ("season_champion", True): "神机妙算！你预见了赛季冠军！",
            ("season_champion", False): "预测落空，局势风云突变...",
            ("first_annexed", True): "料事如神！你猜中了最先灭门的宗门！",
            ("first_annexed", False): "预测错误，该宗门竟顽强存活...",
            ("betrayal", True): "慧眼如炬！你预见了这场背叛！",
            ("betrayal", False): "预测失败，他们竟维持了盟约...",
        }
        
        return {
            "success": correct,
            "points_earned": points,
            "message": messages.get((prediction_type, correct), "预测已结算。"),
        }
