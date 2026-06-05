"""
Event Engine - 事件引擎
负责生成世界事件、宗门事件、外交事件，并计算事件对世界状态的实际影响。
"""
import random
from typing import Any


class EventEngine:
    """事件引擎：生成和管理游戏事件，事件有实际数值效果"""

    WORLD_EVENTS = [
        {
            "type": "secret_realm", "title": "秘境开启",
            "desc": "传闻有上古秘境开启，内含高阶功法与法宝。",
            "severity": 0.6,
            "effects": {"all_sects": {"spirit_stones": 200, "techniques": 1}},
        },
        {
            "type": "spirit_tide", "title": "灵气潮汐",
            "desc": "天地灵气突然暴涨，所有宗门修炼速度翻倍。",
            "severity": 0.4,
            "effects": {"all_sects": {"military_power": 15, "spiritual_power": 10}},
        },
        {
            "type": "demon_outbreak", "title": "魔灾爆发",
            "desc": "外域魔物入侵，所有宗门面临威胁。",
            "severity": 0.8,
            "effects": {"all_sects": {"military_power": -20, "stability": -0.1}},
        },
        {
            "type": "genius_born", "title": "天才出世",
            "desc": "天降异象，预示一位绝世天才即将现世。",
            "severity": 0.5,
            "effects": {"random_sect": {"military_power": 30, "reputation": 10}},
        },
        {
            "type": "ancient_ruins", "title": "上古遗迹",
            "desc": "某处发现上古遗迹，可能藏有失传功法。",
            "severity": 0.7,
            "effects": {"random_sect": {"artifacts": 5, "techniques": 2, "spirit_stones": 300}},
        },
        {
            "type": "resource_depletion", "title": "资源枯竭",
            "desc": "某片区域的灵脉出现枯竭迹象。",
            "severity": 0.5,
            "effects": {"all_sects": {"spirit_stones": -100}},
        },
        {
            "type": "celestial_blessing", "title": "天道赐福",
            "desc": "天道降下祥瑞，某宗门气运大增。",
            "severity": 0.3,
            "effects": {"random_sect": {"luck": 0.2, "spirit_stones": 500}},
        },
        {
            "type": "plague", "title": "瘟疫蔓延",
            "desc": "一种诡异瘟疫在修仙界蔓延，影响修炼。",
            "severity": 0.6,
            "effects": {"all_sects": {"military_power": -10, "stability": -0.05}},
        },
    ]

    SECT_EVENTS = [
        {
            "type": "breakthrough", "title": "弟子突破",
            "desc_template": "{sect_name} 一位弟子突破瓶颈，实力大增。",
            "effects": {"military_power": 15, "reputation": 5},
        },
        {
            "type": "elder_betrayal", "title": "长老叛逃",
            "desc_template": "{sect_name} 一位长老携带宗门秘法叛逃。",
            "effects": {"military_power": -10, "stability": -0.15, "techniques": -1},
        },
        {
            "type": "leader_retreat", "title": "掌门闭关",
            "desc_template": "{sect_name} 掌门宣布闭关修炼，宗门事务暂由长老代理。",
            "effects": {"stability": -0.05, "spiritual_power": 10},
        },
        {
            "type": "inner_strife", "title": "内门斗争",
            "desc_template": "{sect_name} 内部出现派系斗争，稳定度下降。",
            "effects": {"stability": -0.2, "military_power": -5},
        },
        {
            "type": "artifact_created", "title": "法器出世",
            "desc_template": "{sect_name} 成功炼制出一件强大法器！",
            "effects": {"artifacts": 2, "military_power": 8},
        },
        {
            "type": "array_damaged", "title": "大阵破损",
            "desc_template": "{sect_name} 的护山大阵出现破损，需要修复。",
            "effects": {"stability": -0.1, "spirit_stones": -100},
        },
        {
            "type": "reputation_surge", "title": "声望暴涨",
            "desc_template": "{sect_name} 的名声在修仙界广为流传。",
            "effects": {"reputation": 15, "spirit_stones": 50},
        },
        {
            "type": "treasure_found", "title": "发现宝藏",
            "desc_template": "{sect_name} 弟子外出历练时发现一处宝藏。",
            "effects": {"spirit_stones": 200, "artifacts": 1},
        },
        {
            "type": "disciple_lost", "title": "弟子失踪",
            "desc_template": "{sect_name} 数名弟子在外出历练时失踪。",
            "effects": {"military_power": -8, "stability": -0.08},
        },
    ]

    @staticmethod
    def generate_world_events(turn: int, world_seed: int, sects: list[dict] | None = None) -> list[dict]:
        """生成世界事件，带实际效果"""
        random.seed(world_seed + turn)
        events = []
        if random.random() < 0.35:
            event_template = random.choice(EventEngine.WORLD_EVENTS)
            event = {
                "type": event_template["type"],
                "title": event_template["title"],
                "description": event_template["desc"],
                "severity": event_template["severity"],
                "effects": event_template.get("effects", {}),
                "affected_regions": [],
                "affected_sects": [],
            }
            # 确定影响对象
            effects = event["effects"]
            if "all_sects" in effects:
                event["affected_sects"] = [s["id"] for s in (sects or [])]
            elif "random_sect" in effects and sects:
                event["affected_sects"] = [random.choice(sects)["id"]]
            events.append(event)
        random.seed()
        return events

    @staticmethod
    def generate_sect_events(sect: dict, turn: int, world_seed: int) -> list[dict]:
        """为单个宗门生成事件，带实际效果"""
        random.seed(world_seed + turn + hash(sect.get("id", "")) % 10000)
        events = []
        stability = sect.get("stats", {}).get("stability", 0.5)
        # 稳定度越低事件越多，但突破类好事也更多
        event_chance = 0.3 - stability * 0.15

        if random.random() < event_chance:
            event_template = random.choice(EventEngine.SECT_EVENTS)
            desc = event_template["desc_template"].format(sect_name=sect.get("name", "某宗门"))
            events.append({
                "type": event_template["type"],
                "title": event_template["title"],
                "description": desc,
                "severity": random.uniform(0.3, 0.7),
                "effects": event_template.get("effects", {}),
                "affected_sects": [sect["id"]],
            })
        random.seed()
        return events

    @staticmethod
    def apply_event_effects(event: dict, sect_states: dict):
        """将事件效果应用到宗门状态"""
        effects = event.get("effects", {})
        affected = event.get("affected_sects", [])

        for sect_id in affected:
            if sect_id not in sect_states:
                continue
            sect = sect_states[sect_id]
            resources = sect.get("resources", {})
            stats = sect.get("stats", {})

            # 确定使用哪个效果集
            event_effects = effects.get("all_sects") or effects.get("random_sect") or effects

            for key, value in event_effects.items():
                if key == "spirit_stones":
                    resources["spirit_stones"] = max(0, resources.get("spirit_stones", 0) + value)
                elif key == "pills":
                    resources["pills"] = max(0, resources.get("pills", 0) + value)
                elif key == "artifacts":
                    resources["artifacts"] = max(0, resources.get("artifacts", 0) + value)
                elif key == "techniques":
                    resources["techniques"] = max(0, resources.get("techniques", 0) + value)
                elif key == "military_power":
                    stats["military_power"] = max(0, stats.get("military_power", 0) + value)
                elif key == "spiritual_power":
                    stats["spiritual_power"] = max(0, stats.get("spiritual_power", 0) + value)
                elif key == "reputation":
                    stats["reputation"] = max(0, stats.get("reputation", 0) + value)
                elif key == "stability":
                    stats["stability"] = max(0.0, min(1.0, stats.get("stability", 0.5) + value))
                elif key == "luck":
                    stats["luck"] = max(0.0, min(1.0, stats.get("luck", 0.5) + value))
                elif key == "economy":
                    stats["economy"] = max(0, stats.get("economy", 0) + value)

    @staticmethod
    def generate_diplomacy_events(world_state: dict, turn: int) -> list[dict]:
        """生成外交事件"""
        events = []
        for sect in world_state.get("sects", []):
            personality = sect.get("personality", {})
            honor = personality.get("honor", 0.5)
            if random.random() < (1 - honor) * 0.15:
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
                        "effects": {"stability": -0.05},
                        "affected_sects": [sect["id"]],
                        "tags": ["背叛"],
                    })
        return events
