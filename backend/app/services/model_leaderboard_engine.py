"""
Model Leaderboard Engine - 模型斗蛐蛐排行榜引擎
跨世界统计模型表现，生成斗蛐蛐排行榜
"""
import json
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.model_performance import ModelPerformanceStats
from app.models.llm_model import LLMModel
from app.models.llm_provider import LLMProvider
from app.models.sect import Sect
from app.models.world import World


class ModelLeaderboardEngine:
    """模型斗蛐蛐排行榜引擎"""

    RATING_WEIGHTS = {
        "win_rate": 0.30,
        "survival": 0.20,
        "war": 0.15,
        "diplomacy": 0.15,
        "economy": 0.10,
        "cost_efficiency": 0.05,
        "reliability": 0.05,
    }

    def __init__(self, db: Session):
        self.db = db

    def get_model_stats(self, model_id: str) -> dict:
        """获取单个模型的统计数据"""
        stats = self.db.query(ModelPerformanceStats).filter(ModelPerformanceStats.model_id == model_id).all()
        if not stats:
            return self._empty_stats(model_id)

        total_calls = sum(s.total_calls for s in stats)
        success_calls = sum(s.success_calls for s in stats)
        wins = sum(s.win_count for s in stats)
        losses = sum(s.lose_count for s in stats)
        total_games = wins + losses

        avg_latency = sum(s.avg_latency_ms * s.total_calls for s in stats) / max(total_calls, 1)
        total_cost = sum(s.total_cost for s in stats)

        return {
            "model_id": model_id,
            "total_games": total_games,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / max(total_games, 1), 3),
            "total_calls": total_calls,
            "success_rate": round(success_calls / max(total_calls, 1), 3),
            "avg_latency_ms": round(avg_latency, 1),
            "total_cost": round(total_cost, 4),
            "diplomacy_score": round(sum(s.diplomacy_score for s in stats) / max(len(stats), 1), 1),
            "war_score": round(sum(s.war_score for s in stats) / max(len(stats), 1), 1),
            "economy_score": round(sum(s.economy_score for s in stats) / max(len(stats), 1), 1),
            "survival_score": round(sum(s.survival_score for s in stats) / max(len(stats), 1), 1),
        }

    def get_leaderboard(self, min_games: int = 1) -> list[dict]:
        """获取模型斗蛐蛐排行榜"""
        # 获取所有有记录的 model_id
        model_ids = self.db.query(ModelPerformanceStats.model_id).distinct().all()
        model_ids = [m[0] for m in model_ids]

        entries = []
        for model_id in model_ids:
            stats = self.get_model_stats(model_id)
            if stats["total_games"] < min_games:
                continue

            # 获取模型信息
            model = self.db.query(LLMModel).filter(LLMModel.id == model_id).first()
            provider = None
            if model:
                provider = self.db.query(LLMProvider).filter(LLMProvider.id == model.provider_id).first()

            # 计算综合评分
            rating = self._calculate_rating(stats)

            entries.append({
                "model_id": model_id,
                "model_name": model.display_name if model else model_id,
                "provider_name": provider.name if provider else "未知",
                "total_games": stats["total_games"],
                "wins": stats["wins"],
                "losses": stats["losses"],
                "win_rate": stats["win_rate"],
                "survival_score": stats["survival_score"],
                "war_score": stats["war_score"],
                "diplomacy_score": stats["diplomacy_score"],
                "economy_score": stats["economy_score"],
                "avg_latency_ms": stats["avg_latency_ms"],
                "total_cost": stats["total_cost"],
                "reliability": stats["success_rate"],
                "rating": round(rating, 1),
            })

        # 按评分排序
        entries.sort(key=lambda x: x["rating"], reverse=True)
        for i, e in enumerate(entries, 1):
            e["rank"] = i

        return entries

    def get_model_detail(self, model_id: str) -> dict:
        """获取模型详细表现"""
        stats = self.get_model_stats(model_id)
        model = self.db.query(LLMModel).filter(LLMModel.id == model_id).first()
        provider = self.db.query(LLMProvider).filter(LLMProvider.id == model.provider_id).first() if model else None

        # 获取该模型参与的所有世界
        world_stats = self.db.query(ModelPerformanceStats).filter(ModelPerformanceStats.model_id == model_id).all()
        world_performances = []
        for ws in world_stats:
            world = self.db.query(World).filter(World.id == ws.world_id).first()
            world_performances.append({
                "world_id": ws.world_id,
                "world_name": world.name if world else "未知",
                "turns": world.current_turn if world else 0,
                "win_count": ws.win_count,
                "lose_count": ws.lose_count,
                "total_calls": ws.total_calls,
                "avg_latency_ms": ws.avg_latency_ms,
                "total_cost": ws.total_cost,
            })

        return {
            "model_id": model_id,
            "model_name": model.display_name if model else model_id,
            "provider_name": provider.name if provider else "未知",
            "stats": stats,
            "world_performances": world_performances,
        }

    def get_head_to_head(self, model_a_id: str, model_b_id: str) -> dict:
        """获取两个模型的对战记录"""
        # 查找两个模型在同一世界中的对战
        a_worlds = self.db.query(ModelPerformanceStats.world_id).filter(ModelPerformanceStats.model_id == model_a_id).all()
        b_worlds = self.db.query(ModelPerformanceStats.world_id).filter(ModelPerformanceStats.model_id == model_b_id).all()
        a_worlds = set(w[0] for w in a_worlds if w[0])
        b_worlds = set(w[0] for w in b_worlds if w[0])
        common_worlds = a_worlds & b_worlds

        matches = []
        for world_id in common_worlds:
            world = self.db.query(World).filter(World.id == world_id).first()
            if not world or world.status != "finished":
                continue

            # 获取该世界中两个模型的宗门
            sects = self.db.query(Sect).filter(Sect.world_id == world_id).all()
            a_sect = [s for s in sects if s.model_name == model_a_id]
            b_sect = [s for s in sects if s.model_name == model_b_id]

            if a_sect and b_sect:
                a_final = a_sect[0]
                b_final = b_sect[0]
                a_stats = self.db.query(ModelPerformanceStats).filter(
                    ModelPerformanceStats.model_id == model_a_id,
                    ModelPerformanceStats.world_id == world_id,
                ).first()
                b_stats = self.db.query(ModelPerformanceStats).filter(
                    ModelPerformanceStats.model_id == model_b_id,
                    ModelPerformanceStats.world_id == world_id,
                ).first()

                matches.append({
                    "world_id": world_id,
                    "world_name": world.name,
                    "turns": world.current_turn,
                    "model_a": {"sect_name": a_final.name, "status": a_final.status, "wins": a_stats.win_count if a_stats else 0},
                    "model_b": {"sect_name": b_final.name, "status": b_final.status, "wins": b_stats.win_count if b_stats else 0},
                })

        return {
            "model_a_id": model_a_id,
            "model_b_id": model_b_id,
            "total_matches": len(matches),
            "matches": matches,
        }

    def _calculate_rating(self, stats: dict) -> float:
        """计算模型综合评分"""
        rating = 0
        rating += stats["win_rate"] * 100 * self.RATING_WEIGHTS["win_rate"]
        rating += stats["survival_score"] * self.RATING_WEIGHTS["survival"]
        rating += stats["war_score"] * self.RATING_WEIGHTS["war"]
        rating += stats["diplomacy_score"] * self.RATING_WEIGHTS["diplomacy"]
        rating += stats["economy_score"] * self.RATING_WEIGHTS["economy"]
        # 成本效率：成本越低分越高
        cost_efficiency = max(0, 100 - stats["total_cost"] * 100)
        rating += cost_efficiency * self.RATING_WEIGHTS["cost_efficiency"]
        rating += stats["success_rate"] * 100 * self.RATING_WEIGHTS["reliability"]
        return rating

    def _empty_stats(self, model_id: str) -> dict:
        return {
            "model_id": model_id,
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0,
            "total_calls": 0,
            "success_rate": 0,
            "avg_latency_ms": 0,
            "total_cost": 0,
            "diplomacy_score": 0,
            "war_score": 0,
            "economy_score": 0,
            "survival_score": 0,
        }
