"""Model Leaderboard API Router - 模型斗蛐蛐排行榜"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.model_leaderboard_engine import ModelLeaderboardEngine

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("")
def get_global_leaderboard(min_games: int = 1, db: Session = Depends(get_db)):
    """获取全局模型斗蛐蛐排行榜"""
    engine = ModelLeaderboardEngine(db)
    return {
        "leaderboard": engine.get_leaderboard(min_games=min_games),
        "min_games": min_games,
    }


@router.get("/models/{model_id}")
def get_model_detail(model_id: str, db: Session = Depends(get_db)):
    """获取模型详细表现"""
    engine = ModelLeaderboardEngine(db)
    detail = engine.get_model_detail(model_id)
    if not detail["stats"]["total_games"]:
        raise HTTPException(status_code=404, detail="模型暂无对战记录")
    return detail


@router.get("/head-to-head")
def get_head_to_head(model_a_id: str, model_b_id: str, db: Session = Depends(get_db)):
    """获取两个模型的对战记录"""
    engine = ModelLeaderboardEngine(db)
    return engine.get_head_to_head(model_a_id, model_b_id)


@router.get("/stats/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    """获取斗蛐蛐统计摘要"""
    engine = ModelLeaderboardEngine(db)
    leaderboard = engine.get_leaderboard(min_games=1)

    total_games = sum(e["total_games"] for e in leaderboard)
    total_models = len(leaderboard)
    avg_win_rate = sum(e["win_rate"] for e in leaderboard) / max(total_models, 1)

    top_warrior = max(leaderboard, key=lambda x: x["war_score"]) if leaderboard else None
    top_diplomat = max(leaderboard, key=lambda x: x["diplomacy_score"]) if leaderboard else None
    top_economist = max(leaderboard, key=lambda x: x["economy_score"]) if leaderboard else None

    return {
        "total_models": total_models,
        "total_games": total_games,
        "avg_win_rate": round(avg_win_rate, 3),
        "top_warrior": top_warrior,
        "top_diplomat": top_diplomat,
        "top_economist": top_economist,
    }
