"""
Settings API Router - API 配置中心
Provider CRUD + 测试连接 + 同步模型 + Agent 绑定
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
from app.models.agent_binding import AgentModelBinding
from app.services.llm_client import LLMClient

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ============ Schemas ============

class ProviderCreate(BaseModel):
    name: str
    provider_type: str = "openai_compatible"
    base_url: str
    api_key: str
    enabled: bool = True
    priority: int = 100
    timeout_seconds: int = 60
    max_retries: int = 2


class ProviderUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    enabled: bool | None = None
    priority: int | None = None
    timeout_seconds: int | None = None
    max_retries: int | None = None


class ModelCreate(BaseModel):
    provider_id: str
    model_name: str
    display_name: str | None = None
    context_window: int = 128000
    input_price_per_1m: float = 0
    output_price_per_1m: float = 0
    role_tags: list[str] = []


class BindingCreate(BaseModel):
    world_id: str | None = None
    sect_id: str | None = None
    agent_role: str
    provider_id: str
    model_id: str
    locked: bool = False
    fallback_chain: list[str] = []
    temperature: float = 0.7
    max_tokens: int = 2000


# ============ Helper ============

def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _provider_to_dict(p: LLMProvider) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "provider_type": p.provider_type,
        "base_url": p.base_url,
        "api_key_masked": _mask_key(p.api_key_encrypted),
        "enabled": p.enabled,
        "priority": p.priority,
        "timeout_seconds": p.timeout_seconds,
        "max_retries": p.max_retries,
        "created_at": p.created_at.isoformat() if p.created_at else "",
        "updated_at": p.updated_at.isoformat() if p.updated_at else "",
    }


def _model_to_dict(m: LLMModel) -> dict:
    return {
        "id": m.id,
        "provider_id": m.provider_id,
        "model_name": m.model_name,
        "display_name": m.display_name,
        "model_type": m.model_type,
        "context_window": m.context_window,
        "input_price_per_1m": m.input_price_per_1m,
        "output_price_per_1m": m.output_price_per_1m,
        "enabled": m.enabled,
        "role_tags": json.loads(m.role_tags_json or "[]"),
        "quality_score": m.quality_score,
        "speed_score": m.speed_score,
        "stability_score": m.stability_score,
    }


# ============ Provider CRUD ============

@router.get("/providers")
def list_providers(db: Session = Depends(get_db)):
    """列出所有 Provider"""
    providers = db.query(LLMProvider).all()
    return [_provider_to_dict(p) for p in providers]


@router.post("/providers")
def create_provider(req: ProviderCreate, db: Session = Depends(get_db)):
    """创建 Provider"""
    provider = LLMProvider(
        name=req.name,
        provider_type=req.provider_type,
        base_url=req.base_url,
        api_key_encrypted=req.api_key,
        enabled=req.enabled,
        priority=req.priority,
        timeout_seconds=req.timeout_seconds,
        max_retries=req.max_retries,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return _provider_to_dict(provider)


@router.get("/providers/{provider_id}")
def get_provider(provider_id: str, db: Session = Depends(get_db)):
    """获取 Provider 详情"""
    p = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Provider 不存在")
    return _provider_to_dict(p)


@router.put("/providers/{provider_id}")
def update_provider(provider_id: str, req: ProviderUpdate, db: Session = Depends(get_db)):
    """更新 Provider"""
    p = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Provider 不存在")

    if req.name is not None:
        p.name = req.name
    if req.base_url is not None:
        p.base_url = req.base_url
    if req.api_key is not None:
        p.api_key_encrypted = req.api_key
    if req.enabled is not None:
        p.enabled = req.enabled
    if req.priority is not None:
        p.priority = req.priority
    if req.timeout_seconds is not None:
        p.timeout_seconds = req.timeout_seconds
    if req.max_retries is not None:
        p.max_retries = req.max_retries

    db.commit()
    db.refresh(p)
    return _provider_to_dict(p)


@router.delete("/providers/{provider_id}")
def delete_provider(provider_id: str, db: Session = Depends(get_db)):
    """删除 Provider"""
    p = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Provider 不存在")
    db.delete(p)
    db.commit()
    return {"ok": True}


# ============ Test Connection ============

@router.post("/providers/{provider_id}/test")
async def test_provider_connection(provider_id: str, db: Session = Depends(get_db)):
    """测试 Provider 连接"""
    p = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Provider 不存在")

    client = LLMClient()
    try:
        result = await client.test_connection(p)
        return result
    finally:
        await client.close()


# ============ Sync Models ============

@router.post("/providers/{provider_id}/sync-models")
async def sync_models(provider_id: str, db: Session = Depends(get_db)):
    """从 Provider 拉取模型列表"""
    p = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Provider 不存在")

    client = LLMClient()
    try:
        models_data = await client.list_models(p)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"拉取失败: {e}")
    finally:
        await client.close()

    added = []
    for m in models_data:
        model_id = m.get("id", "")
        # 检查是否已存在
        existing = db.query(LLMModel).filter(
            LLMModel.provider_id == provider_id,
            LLMModel.model_name == model_id,
        ).first()
        if not existing:
            new_model = LLMModel(
                provider_id=provider_id,
                model_name=model_id,
                display_name=m.get("object", model_id),
            )
            db.add(new_model)
            added.append(model_id)

    db.commit()
    return {"ok": True, "synced_count": len(added), "models": added}


# ============ Model Management ============

@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    """列出所有模型"""
    models = db.query(LLMModel).all()
    return [_model_to_dict(m) for m in models]


@router.post("/models")
def create_model(req: ModelCreate, db: Session = Depends(get_db)):
    """手动添加模型"""
    provider = db.query(LLMProvider).filter(LLMProvider.id == req.provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider 不存在")

    model = LLMModel(
        provider_id=req.provider_id,
        model_name=req.model_name,
        display_name=req.display_name or req.model_name,
        context_window=req.context_window,
        input_price_per_1m=req.input_price_per_1m,
        output_price_per_1m=req.output_price_per_1m,
        role_tags_json=json.dumps(req.role_tags, ensure_ascii=False),
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return _model_to_dict(model)


@router.delete("/models/{model_id}")
def delete_model(model_id: str, db: Session = Depends(get_db)):
    """删除模型"""
    m = db.query(LLMModel).filter(LLMModel.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="模型不存在")
    db.delete(m)
    db.commit()
    return {"ok": True}


# ============ Agent Binding ============

@router.get("/bindings")
def list_bindings(world_id: str | None = None, db: Session = Depends(get_db)):
    """列出绑定配置"""
    query = db.query(AgentModelBinding)
    if world_id:
        query = query.filter(AgentModelBinding.world_id == world_id)
    bindings = query.all()
    return [
        {
            "id": b.id,
            "world_id": b.world_id,
            "sect_id": b.sect_id,
            "agent_role": b.agent_role,
            "provider_id": b.provider_id,
            "model_id": b.model_id,
            "locked": b.locked,
            "fallback_chain": json.loads(b.fallback_chain_json or "[]"),
            "temperature": b.temperature,
            "max_tokens": b.max_tokens,
        }
        for b in bindings
    ]


@router.post("/bindings")
def create_binding(req: BindingCreate, db: Session = Depends(get_db)):
    """创建绑定"""
    binding = AgentModelBinding(
        world_id=req.world_id,
        sect_id=req.sect_id,
        agent_role=req.agent_role,
        provider_id=req.provider_id,
        model_id=req.model_id,
        locked=req.locked,
        fallback_chain_json=json.dumps(req.fallback_chain, ensure_ascii=False),
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    db.add(binding)
    db.commit()
    db.refresh(binding)
    return {
        "id": binding.id,
        "world_id": binding.world_id,
        "sect_id": binding.sect_id,
        "agent_role": binding.agent_role,
        "provider_id": binding.provider_id,
        "model_id": binding.model_id,
        "locked": binding.locked,
    }


@router.delete("/bindings/{binding_id}")
def delete_binding(binding_id: str, db: Session = Depends(get_db)):
    """删除绑定"""
    b = db.query(AgentModelBinding).filter(AgentModelBinding.id == binding_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="绑定不存在")
    db.delete(b)
    db.commit()
    return {"ok": True}
