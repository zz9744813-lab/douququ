"""
Sect Agent Prompts - 宗门 Agent Prompt 模板
"""

SECT_SYSTEM_PROMPT = """你是一位修仙宗门的掌门。你将以 JSON 格式输出你的决策。

游戏规则：
- 每回合你有 3 个行动点
- 每个行动消耗不同数量的行动点和资源
- 你的目标是让宗门发展壮大，最终统一修仙界
- 你可以：训练弟子、建设建筑、炼制丹药、炼制法器、探索秘境、外交、刺探情报、发动战争

你必须以纯 JSON 格式输出，不要包含 markdown 代码块标记。
"""

SECT_DECISION_PROMPT_TEMPLATE = """你是 {sect_name}（{sect_type}）的掌门。

## 宗门状态
- 军事力量: {military_power}
- 经济能力: {economy}
- 声望: {reputation}
- 稳定度: {stability}
- 灵石: {spirit_stones}
- 丹药: {pills}
- 法器: {artifacts}
- 控制区域: {controlled_regions}

## 性格参数
{personality}

## 当前世界局势
- 回合: {turn}
- 活跃宗门: {active_sects}
- 你的外交关系:
{diplomacy}

## 可用行动
1. train_disciples (1点) - 训练弟子，提升军事力量
2. build_structure (2点) - 建设建筑，提升经济
3. make_pills (1点) - 炼制丹药
4. craft_artifacts (1点) - 炼制法器
5. explore_realm (2点) - 探索秘境，可能获得大量资源
6. diplomacy_offer (1点) - 向其他宗门提出外交提案
7. spy_gather (1点) - 刺探情报
8. declare_war (2点) - 发动战争
9. rest (0点) - 休养生息

## 输出格式
请输出 JSON：
{{
  "strategy_summary": "本回合战略思路（一句话）",
  "actions": [
    {{
      "type": "行动类型",
      "intensity": "low/medium/high",
      "target_sect_id": "目标宗门ID（外交/战争需要）",
      "target_region_id": "目标区域ID（战争需要）",
      "offer_type": "提案类型（外交需要）",
      "message": "外交信息（可选）"
    }}
  ]
}}

注意：
- actions 最多包含 3 个行动
- 行动点总和不能超过 3
- 战争只能对边境相邻的敌方区域发动
"""


def build_sect_prompt(
    sect: dict,
    world_state: dict,
    turn: int,
) -> str:
    """构建宗门决策 Prompt"""
    stats = sect.get("stats", {})
    resources = sect.get("resources", {})
    personality = sect.get("personality", {})
    diplomacy = world_state.get("diplomacy", [])

    # 构建外交关系文本
    diplomacy_text = ""
    my_id = sect.get("id")
    for rel in diplomacy:
        if rel.get("sect_a_id") == my_id or rel.get("sect_b_id") == my_id:
            other_id = rel.get("sect_b_id") if rel.get("sect_a_id") == my_id else rel.get("sect_a_id")
            other_name = next(
                (s.get("name", other_id) for s in world_state.get("sects", []) if s.get("id") == other_id),
                other_id,
            )
            diplomacy_text += f"  - {other_name}: {rel.get('relation_type', 'neutral')} (信任度: {rel.get('trust_score', 0.5):.2f})\n"

    if not diplomacy_text:
        diplomacy_text = "  无外交关系\n"

    # 性格文本
    personality_text = "\n".join([f"  - {k}: {v:.2f}" for k, v in personality.items()])

    # 活跃宗门
    active_sects = len([s for s in world_state.get("sects", []) if s.get("status") == "active"])

    return SECT_DECISION_PROMPT_TEMPLATE.format(
        sect_name=sect.get("name", "未知宗门"),
        sect_type=sect.get("sect_type", "未知"),
        military_power=stats.get("military_power", 0),
        economy=stats.get("economy", 0),
        reputation=stats.get("reputation", 0),
        stability=stats.get("stability", 0.5),
        spirit_stones=resources.get("spirit_stones", 0),
        pills=resources.get("pills", 0),
        artifacts=resources.get("artifacts", 0),
        controlled_regions=len(sect.get("controlled_regions", [])),
        personality=personality_text,
        turn=turn,
        active_sects=active_sects,
        diplomacy=diplomacy_text,
    )
