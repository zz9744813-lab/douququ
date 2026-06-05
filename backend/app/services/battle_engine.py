"""
Battle Engine - 战斗引擎
负责战争胜负计算、伤亡计算、区域占领
"""
import random
import math
from typing import Any


class BattleEngine:
    """战斗引擎：计算战争结果"""

    @staticmethod
    def resolve_battle(
        attacker: dict,
        defender: dict,
        region: dict | None = None,
        attacker_intel: float = 0.0,
    ) -> dict:
        """
        结算一场战争。
        返回: {result_type, winner_id, attacker_power, defender_power, losses, rewards, log}
        """
        # 基础战力
        atk_military = attacker.get("stats", {}).get("military_power", 50)
        def_military = defender.get("stats", {}).get("military_power", 50)

        # 士气系数
        atk_stability = attacker.get("stats", {}).get("stability", 0.5)
        def_stability = defender.get("stats", {}).get("stability", 0.5)
        atk_morale = 0.7 + atk_stability * 0.6
        def_morale = 0.7 + def_stability * 0.6

        # 法器加成
        atk_artifacts = attacker.get("resources", {}).get("artifacts", 0)
        def_artifacts = defender.get("resources", {}).get("artifacts", 0)
        atk_artifact_bonus = 1.0 + min(atk_artifacts * 0.02, 0.5)
        def_artifact_bonus = 1.0 + min(def_artifacts * 0.02, 0.5)

        # 防御方加成
        def_formation = defender.get("stats", {}).get("formation", 10)
        defense_bonus = 1.0 + def_formation * 0.03
        if region:
            defense_bonus += region.get("defense_level", 1) * 0.1

        # 情报加成
        intel_bonus = 1.0 + attacker_intel * 0.02

        # 随机波动
        random_factor = random.uniform(0.85, 1.15)

        # 计算最终战力
        attacker_power = atk_military * atk_morale * atk_artifact_bonus * intel_bonus * random_factor
        defender_power = def_military * def_morale * def_artifact_bonus * defense_bonus * random.uniform(0.85, 1.15)

        # 判断结果
        ratio = attacker_power / max(defender_power, 1)
        if ratio > 1.2:
            result_type = "decisive_victory"
            winner_id = attacker["id"]
        elif ratio > 1.0:
            result_type = "victory"
            winner_id = attacker["id"]
        elif ratio > 0.8:
            result_type = "stalemate"
            winner_id = None
        elif ratio > 0.5:
            result_type = "defeat"
            winner_id = defender["id"]
        else:
            result_type = "crushing_defeat"
            winner_id = defender["id"]

        # 伤亡计算
        losses = BattleEngine._calculate_losses(result_type, atk_military, def_military)

        # 奖励计算
        rewards = BattleEngine._calculate_rewards(result_type, defender, region)

        # 生成战报
        battle_log = BattleEngine._generate_log(
            result_type, attacker, defender, attacker_power, defender_power, losses, rewards
        )

        return {
            "result_type": result_type,
            "winner_sect_id": winner_id,
            "attacker_power": round(attacker_power, 1),
            "defender_power": round(defender_power, 1),
            "losses": losses,
            "rewards": rewards,
            "battle_log": battle_log,
        }

    @staticmethod
    def _calculate_losses(result_type: str, atk_military: float, def_military: float) -> dict:
        """计算双方伤亡"""
        loss_rates = {
            "decisive_victory": (0.05, 0.35),
            "victory": (0.1, 0.25),
            "stalemate": (0.15, 0.15),
            "defeat": (0.25, 0.1),
            "crushing_defeat": (0.35, 0.05),
        }
        atk_rate, def_rate = loss_rates.get(result_type, (0.15, 0.15))
        return {
            "attacker_loss": max(1, int(atk_military * atk_rate * random.uniform(0.8, 1.2))),
            "defender_loss": max(1, int(def_military * def_rate * random.uniform(0.8, 1.2))),
        }

    @staticmethod
    def _calculate_rewards(result_type: str, defender: dict, region: dict | None) -> dict:
        """计算战胜奖励"""
        rewards = {"spirit_stones": 0, "regions_captured": [], "pills": 0, "artifacts": 0}
        if result_type in ("decisive_victory", "victory"):
            # 掠夺资源
            def_res = defender.get("resources", {})
            rewards["spirit_stones"] = int(def_res.get("spirit_stones", 0) * 0.3)
            rewards["pills"] = int(def_res.get("pills", 0) * 0.3)
            rewards["artifacts"] = int(def_res.get("artifacts", 0) * 0.2)
            if result_type == "decisive_victory" and region:
                rewards["regions_captured"] = [region["id"]]
        elif result_type == "defeat":
            # 攻击方失败，防守方获得少量战利品
            pass
        return rewards

    @staticmethod
    def _generate_log(
        result_type: str,
        attacker: dict,
        defender: dict,
        atk_power: float,
        def_power: float,
        losses: dict,
        rewards: dict,
    ) -> str:
        """生成人类可读战报"""
        atk_name = attacker.get("name", "未知宗门")
        def_name = defender.get("name", "未知宗门")
        log_map = {
            "decisive_victory": f"【大胜】{atk_name} 以雷霆之势击溃 {def_name}！战力 {atk_power:.0f} vs {def_power:.0f}。{atk_name} 损失 {losses['attacker_loss']}，{def_name} 损失 {losses['defender_loss']}。",
            "victory": f"【小胜】{atk_name} 在与 {def_name} 的战斗中取得优势。战力 {atk_power:.0f} vs {def_power:.0f}。双方各损失 {losses['attacker_loss']}/{losses['defender_loss']}。",
            "stalemate": f"【僵持】{atk_name} 与 {def_name} 势均力敌，陷入僵持。战力 {atk_power:.0f} vs {def_power:.0f}。",
            "defeat": f"【战败】{atk_name} 进攻 {def_name} 受挫！战力 {atk_power:.0f} vs {def_power:.0f}。{atk_name} 损失惨重 ({losses['attacker_loss']})。",
            "crushing_defeat": f"【惨败】{atk_name} 被 {def_name} 打得溃不成军！战力 {atk_power:.0f} vs {def_power:.0f}。{atk_name} 军心涣散！",
        }
        return log_map.get(result_type, "战斗结束。")