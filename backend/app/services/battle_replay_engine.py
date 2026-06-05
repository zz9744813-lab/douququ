"""
Battle Replay Engine - 战斗回放引擎
将战争拆解为多个阶段事件，支持前端回放。
"""
import random
from typing import Any


class BattleReplayEngine:
    """战斗回放引擎：生成结构化的战斗阶段事件"""

    @staticmethod
    def generate_replay(
        attacker: dict,
        defender: dict,
        region: dict | None,
        battle_result: dict,
    ) -> list[dict]:
        """
        将战斗结果拆解为多阶段事件。
        返回: [{phase, title, description, effects, duration}]
        """
        replay = []
        atk_name = attacker.get("name", "未知宗门")
        def_name = defender.get("name", "未知宗门")
        region_name = region.get("name", "某地") if region else "边境"
        result_type = battle_result.get("result_type", "stalemate")
        winner = battle_result.get("winner_sect_id")
        atk_power = battle_result.get("attacker_power", 0)
        def_power = battle_result.get("defender_power", 0)
        losses = battle_result.get("losses", {})

        # Phase 1: 宣战
        replay.append({
            "phase": "declaration",
            "title": "宣战",
            "description": f"{atk_name} 向 {def_name} 宣战！目标：{region_name}",
            "effects": {},
            "duration": 1.0,
        })

        # Phase 2: 兵力对比
        replay.append({
            "phase": "comparison",
            "title": "兵力对比",
            "description": f"{atk_name} 战力 {atk_power:.0f} vs {def_name} 战力 {def_power:.0f}",
            "effects": {
                "attacker_power": atk_power,
                "defender_power": def_power,
            },
            "duration": 1.5,
        })

        # Phase 3: 战斗过程
        if result_type == "decisive_victory":
            replay.append({
                "phase": "battle",
                "title": "雷霆一击",
                "description": f"{atk_name} 以压倒性优势击溃 {def_name} 防线！{def_name} 溃不成军！",
                "effects": {
                    "attacker_loss": losses.get("attacker_loss", 0),
                    "defender_loss": losses.get("defender_loss", 0),
                },
                "duration": 2.0,
            })
        elif result_type == "victory":
            replay.append({
                "phase": "battle",
                "title": "激烈交锋",
                "description": f"双方激战数个时辰，{atk_name} 凭借优势兵力取得胜利。",
                "effects": {
                    "attacker_loss": losses.get("attacker_loss", 0),
                    "defender_loss": losses.get("defender_loss", 0),
                },
                "duration": 2.0,
            })
        elif result_type == "stalemate":
            replay.append({
                "phase": "battle",
                "title": "僵持不下",
                "description": f"双方势均力敌，激战良久难分胜负，最终各自收兵。",
                "effects": {
                    "attacker_loss": losses.get("attacker_loss", 0),
                    "defender_loss": losses.get("defender_loss", 0),
                },
                "duration": 2.0,
            })
        elif result_type == "defeat":
            replay.append({
                "phase": "battle",
                "title": "进攻受挫",
                "description": f"{atk_name} 进攻 {def_name} 受挫，{def_name} 防守严密，反击凌厉！",
                "effects": {
                    "attacker_loss": losses.get("attacker_loss", 0),
                    "defender_loss": losses.get("defender_loss", 0),
                },
                "duration": 2.0,
            })
        else:  # crushing_defeat
            replay.append({
                "phase": "battle",
                "title": "惨败而归",
                "description": f"{atk_name} 被 {def_name} 打得溃不成军，士气大损！",
                "effects": {
                    "attacker_loss": losses.get("attacker_loss", 0),
                    "defender_loss": losses.get("defender_loss", 0),
                },
                "duration": 2.0,
            })

        # Phase 4: 结果
        rewards = battle_result.get("rewards", {})
        if result_type in ("decisive_victory", "victory"):
            captured = rewards.get("regions_captured", [])
            captured_text = f"，占领 {region_name}" if captured else ""
            replay.append({
                "phase": "result",
                "title": "胜利",
                "description": f"{atk_name} 获胜！掠夺资源{captured_text}",
                "effects": {
                    "winner": winner,
                    "spirit_stones_looted": rewards.get("spirit_stones", 0),
                    "regions_captured": len(captured),
                },
                "duration": 1.5,
            })
        elif result_type == "stalemate":
            replay.append({
                "phase": "result",
                "title": "僵持",
                "description": "双方各自收兵，约定来日再战。",
                "effects": {},
                "duration": 1.0,
            })
        else:
            replay.append({
                "phase": "result",
                "title": "战败",
                "description": f"{atk_name} 战败，损兵折将。",
                "effects": {
                    "winner": winner,
                },
                "duration": 1.5,
            })

        return replay
