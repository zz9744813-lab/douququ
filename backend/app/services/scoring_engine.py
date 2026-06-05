"""
Scoring Engine - 评分引擎
模型斗蛐蛐评分体系：生存、扩张、经济、战争、外交、策略、成本、戏剧性
"""
import json
import math
from typing import Any


class ScoringEngine:
    """评分引擎：计算宗门/模型在各维度的表现"""

    # 评分权重
    WEIGHTS = {
        "survival": 0.20,
        "expansion": 0.15,
        "economy": 0.10,
        "war": 0.15,
        "diplomacy": 0.15,
        "strategy": 0.15,
        "cost_efficiency": 0.05,
        "drama": 0.05,
    }

    @staticmethod
    def calculate_sect_score(
        sect: dict,
        turn: int,
        max_turns: int,
        battles: list[dict],
        diplomacy_history: list[dict],
        decisions: list[dict],
    ) -> dict:
        """
        计算单个宗门的综合评分。
        返回: {total, survival, expansion, economy, war, diplomacy, strategy, cost_efficiency, drama}
        """
        scores = {}

        # 1. 生存分 (0-100)
        if sect.get("status") == "active":
            survival_score = 100 * (turn / max(max_turns, 1))
        elif sect.get("status") == "annexed":
            survival_score = 30
        else:
            survival_score = 0
        scores["survival"] = survival_score

        # 2. 扩张分 (0-100)
        region_count = len(sect.get("controlled_regions", []))
        expansion_score = min(100, region_count * 15)
        scores["expansion"] = expansion_score

        # 3. 经济分 (0-100)
        resources = sect.get("resources", {})
        total_resources = sum(resources.values())
        economy_score = min(100, total_resources / 50)
        scores["economy"] = economy_score

        # 4. 战争分 (0-100)
        sect_battles = [b for b in battles if b.get("attacker_sect_id") == sect["id"] or b.get("defender_sect_id") == sect["id"]]
        wins = sum(1 for b in sect_battles if b.get("winner_sect_id") == sect["id"])
        total = len(sect_battles)
        win_rate = wins / max(total, 1)
        war_score = win_rate * 80 + min(20, total * 2)
        scores["war"] = war_score

        # 5. 外交分 (0-100)
        dip_success = sum(1 for d in diplomacy_history if d.get("success"))
        dip_total = len(diplomacy_history)
        dip_rate = dip_success / max(dip_total, 1)
        # 联盟数量加分
        alliances = sum(1 for d in diplomacy_history if d.get("relation_type") == "alliance")
        diplomacy_score = dip_rate * 60 + min(40, alliances * 10)
        scores["diplomacy"] = diplomacy_score

        # 6. 策略分 (0-100)
        valid_decisions = sum(1 for d in decisions if d.get("status") == "completed")
        total_decisions = len(decisions)
        valid_rate = valid_decisions / max(total_decisions, 1)
        strategy_score = valid_rate * 100
        scores["strategy"] = strategy_score

        # 7. 成本效率分 (0-100)
        total_cost = sum(d.get("estimated_cost", 0) for d in decisions)
        if total_cost > 0:
            cost_efficiency = max(0, 100 - total_cost / 10)
        else:
            cost_efficiency = 50  # 默认分
        scores["cost_efficiency"] = cost_efficiency

        # 8. 戏剧性分 (0-100)
        drama_events = sum(1 for b in battles if b.get("result_type") in ("decisive_victory", "crushing_defeat"))
        drama_score = min(100, drama_events * 20)
        scores["drama"] = drama_score

        # 计算总分
        total = sum(scores[k] * ScoringEngine.WEIGHTS[k] for k in ScoringEngine.WEIGHTS)
        scores["total"] = round(total, 2)

        return scores

    @staticmethod
    def generate_leaderboard(sect_scores: list[dict]) -> list[dict]:
        """生成排行榜"""
        # 按总分排序
        sorted_scores = sorted(sect_scores, key=lambda x: x["total"], reverse=True)
        
        leaderboard = []
        for rank, score in enumerate(sorted_scores, 1):
            leaderboard.append({
                "rank": rank,
                "sect_id": score.get("sect_id"),
                "sect_name": score.get("sect_name"),
                "model_name": score.get("model_name", "默认AI"),
                "total_score": score["total"],
                "survival": round(score.get("survival", 0), 1),
                "expansion": round(score.get("expansion", 0), 1),
                "economy": round(score.get("economy", 0), 1),
                "war": round(score.get("war", 0), 1),
                "diplomacy": round(score.get("diplomacy", 0), 1),
                "strategy": round(score.get("strategy", 0), 1),
                "cost_efficiency": round(score.get("cost_efficiency", 0), 1),
                "drama": round(score.get("drama", 0), 1),
                "status": score.get("status", "active"),
            })
        
        return leaderboard

    @staticmethod
    def generate_season_report(world_id: str, turns: int, leaderboard: list[dict]) -> dict:
        """生成赛季总结报告"""
        champion = leaderboard[0] if leaderboard else None
        
        # 各种榜单
        war_lords = sorted(leaderboard, key=lambda x: x["war"], reverse=True)[:3]
        diplomats = sorted(leaderboard, key=lambda x: x["diplomacy"], reverse=True)[:3]
        economists = sorted(leaderboard, key=lambda x: x["economy"], reverse=True)[:3]
        survivors = sorted(leaderboard, key=lambda x: x["survival"], reverse=True)[:3]
        
        return {
            "world_id": world_id,
            "total_turns": turns,
            "champion": champion,
            "top_warriors": war_lords,
            "top_diplomats": diplomats,
            "top_economists": economists,
            "top_survivors": survivors,
            "full_leaderboard": leaderboard,
            "summary": ScoringEngine._generate_report_summary(champion, turns),
        }

    @staticmethod
    def _generate_report_summary(champion: dict | None, turns: int) -> str:
        if not champion:
            return "本赛季没有产生冠军。"
        return (
            f"本赛季历经 {turns} 回合，"
            f"{champion['sect_name']}（{champion['model_name']}）"
            f"以 {champion['total_score']} 分的成绩夺得冠军！"
        )
