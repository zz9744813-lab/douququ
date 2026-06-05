"""
Event Engine - 事件引擎
负责生成世界事件、宗门事件、外交事件
"""
import random
from typing import Any


class EventEngine:
    """事件引擎：生成和管理游戏事件"""

    WORLD_EVENTS = [
        {"type": "secret_realm", "title": "秘境开启", "desc": "传闻有上古秘境开启，内含高阶功法与法宝。", "severity": 0.6},
        {"type": "spirit_tide", "title": "灵气潮汐", "desc": "天地灵气突然暴涨，所有宗门修炼速度翻倍。", "severity": 0.4},
        {"type": "demon_outbreak", "title": "魔灾爆发", "desc": "外域魔物入侵，所有宗门面临威胁。", "severity": 0.8},
        {"type": "genius_born", "title": "天才出世", "desc": "天降异象，预示一位绝世天才即将现世。", "severity": 0.5},
        {"type": "ancient_ruins", "title": "上古遗迹", "desc": "某处发现上古遗迹，可能藏有失传功法。", "severity": 0.7},
        {"type": "resource_depletion", "title": "资源枯竭", "desc": "某片区域的灵脉出现枯竭迹象。", "severity": 0.5},
    ]

    SECT_EVENTS = [
        {"type": "breakthrough", "title": "弟子突破", "desc_template": "{sect_name} 一位弟子突破瓶颈，实力大增。"},
        {"type": "elder_betrayal", "title": "长老叛逃", "desc_template": "{sect_name} 一位长老携带宗门秘法叛逃。"},
        {"type": "leader_retreat", "title": "掌门闭关", "desc_template": "{sect_name} 掌门宣布闭关修炼，宗门事务暂由长老代理。"},
        {"type": "inner_strife", "title": "内门斗争", "desc_template": "{sect_name} 内部出现派系斗争，稳定度下降。"},
        {"type": "artifact_created", "title": "法器出世", "desc_template": "{sect_name} 成功炼制出一件强大法器！"},
        {"type": "array_damaged", "title": "大阵破损", "desc_template": "{sect_name} 的护山大阵出现破损，需要修复。"},
        {"type": "reputation_surge", "title": "声望暴涨", "desc_template": "{sect_name} 的名声在修仙界广为流传。"},
    ]

    @staticmethod
    def generate_world_events(turn: int, world_seed: int) -> list[dict]:
        """生成世界事件"""
        random.seed(world_seed + turn)
        events = []
        if random.random() < 0.3:
            event = random.choice(EventEngine.WORLD_EVENTS)
            events.append({
                "type": event["type"],
                "title": event["title"],
                "description": event["desc"],
                "severity": event["severity"],
                "affected_regions": [],
                "affected_sects": [],
            })
        random.seed()
        return events

    @staticmethod
    def generate_sect_events(sect: dict, turn: int, world_seed: int) -> list[dict]:
        """为单个宗门生成事件"""
        random.seed(world_seed + turn + hash(sect.get("id", "")) % 10000)
        events = []
        stability = sect.get("stats", {}).get("stability", 0.5)
        event_chance = 0.25 - stability * 0.2  # 稳定度越低事件越多

        if random.random() < event_chance:
            event = random.choice(EventEngine.SECT_EVENTS)
            desc = event["desc_template"].format(sect_name=sect.get("name", "某宗门"))
            events.append({
                "type": event["type"],
                "title": event["title"],
                "description": desc,
                "severity": random.uniform(0.3, 0.7),
                "affected_sects": [sect["id"]],
            })
        random.seed()
        return events

    @staticmethod
    def generate_diplomacy_events(world_state: dict, turn: int) -> list[dict]:
        """生成外交事件"""
        events = []
        # 检查是否有背叛风险
        for sect in world_state.get("sects", []):
            personality = sect.get("personality", {})
            honor = personality.get("honor", 0.5)
            if random.random() < (1 - honor) * 0.15:
                # 低信誉宗门可能背叛
                allies = [
                    r for r in world_state.get("diplomacy", [])
                    if r.get("relation_type") == "alliance"
                    and (r.get("sect_a_id") == sect["id"] or r.get("sect_b_id") == sect["id"])
                ]
                if allies:
                    events.append({
                        "type": "betrayal_risk",
                        "title": "暗流涌动",
                        "description": f"暗中有势力试图破坏 {sect.get('name', '')} 的联盟关系。",
                        "severity": 0.6,
                        "tags": ["背叛"],
                    })
        return events