"""
Character Engine - 角色引擎
负责角色生成、角色事件、角色与战斗/外交的结合
"""
import json
import random
from typing import Any


# 角色名字生成器
SURNAMES = [
    "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
    "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
    "欧阳", "慕容", "上官", "司徒", "南宫", "独孤", "西门", "东方", "诸葛", "司马",
]
NAMES = [
    "云飞", "剑心", "无痕", "天行", "逍遥", "紫霞", "青冥", "玄霜", "烈火", "寒冰",
    "明月", "星辰", "长风", "沧海", "苍穹", "无极", "太虚", "混元", "乾坤", "阴阳",
    "玉清", "上清", "太清", "灵宝", "道德", "元始", "通天", "接引", "准提", "女娲",
    "红绫", "素衣", "青衫", "白袍", "黑羽", "金瞳", "银发", "碧落", "黄泉", "轮回",
]

REALMS = ["炼气", "筑基", "金丹", "元婴", "化神", "炼虚", "合体", "大乘", "渡劫"]

TRAITS_POOL = [
    "天资聪颖", "心狠手辣", "忠肝义胆", "阴险狡诈", "光明磊落",
    "野心勃勃", "淡泊名利", "嗜血成性", "慈悲为怀", "刚愎自用",
    "足智多谋", "鲁莽冲动", "沉稳老练", "年少轻狂", "深不可测",
    "剑道天才", "炼丹宗师", "阵法大师", "炼器圣手", "御兽奇才",
]


def generate_name(seed: int | None = None) -> str:
    """生成修仙风格名字"""
    rng = random.Random(seed)
    surname = rng.choice(SURNAMES)
    name = rng.choice(NAMES)
    return surname + name


class CharacterEngine:
    """角色引擎"""

    @staticmethod
    def generate_sect_characters(sect_id: str, world_id: str, sect_type: str, seed: int) -> list[dict]:
        """为一个宗门生成初始角色阵容"""
        rng = random.Random(seed)
        characters = []

        # 1 名掌门
        leader = CharacterEngine._create_character(
            world_id, sect_id, "leader", sect_type, rng, realm_boost=3
        )
        characters.append(leader)

        # 2-4 名长老
        elder_count = rng.randint(2, 4)
        for _ in range(elder_count):
            elder = CharacterEngine._create_character(
                world_id, sect_id, "elder", sect_type, rng, realm_boost=2
            )
            characters.append(elder)

        # 1 名圣子/圣女
        heir = CharacterEngine._create_character(
            world_id, sect_id, "heir", sect_type, rng, realm_boost=1
        )
        characters.append(heir)

        # 3-8 名核心弟子
        disciple_count = rng.randint(3, 8)
        for _ in range(disciple_count):
            disciple = CharacterEngine._create_character(
                world_id, sect_id, "disciple", sect_type, rng, realm_boost=0
            )
            characters.append(disciple)

        # 0-2 名暗子/客卿
        if rng.random() < 0.3:
            spy = CharacterEngine._create_character(
                world_id, sect_id, "spy", sect_type, rng, realm_boost=1
            )
            characters.append(spy)

        return characters

    @staticmethod
    def _create_character(
        world_id: str,
        sect_id: str,
        role: str,
        sect_type: str,
        rng: random.Random,
        realm_boost: int = 0,
    ) -> dict:
        """创建单个角色"""
        name = generate_name(rng.randint(0, 999999))

        # 根据角色类型确定境界
        base_realm_idx = {
            "leader": 3, "elder": 2, "heir": 1, "disciple": 0,
            "spy": 1, "prisoner": 0, "traitor": 1, "wanderer": 1,
        }.get(role, 0)

        realm_idx = min(8, base_realm_idx + realm_boost + rng.randint(0, 2))
        realm = REALMS[realm_idx]
        cultivation = rng.randint(1, 9)

        # 天赋 30-100
        talent = rng.randint(30, 100)

        # 战力基于境界和天赋
        base_power = (realm_idx + 1) * 20 + cultivation * 5
        combat_power = int(base_power * (0.5 + talent / 100))

        # 忠诚和野心
        loyalty = rng.uniform(0.3, 0.9)
        ambition = rng.uniform(0.2, 0.8)

        # 气运
        luck = rng.uniform(0.1, 0.9)

        # 性格标签 1-3 个
        trait_count = rng.randint(1, 3)
        traits = rng.sample(TRAITS_POOL, min(trait_count, len(TRAITS_POOL)))

        return {
            "world_id": world_id,
            "sect_id": sect_id,
            "name": name,
            "role": role,
            "realm": realm,
            "cultivation": cultivation,
            "talent": talent,
            "loyalty": loyalty,
            "ambition": ambition,
            "combat_power": combat_power,
            "luck": luck,
            "status": "active",
            "traits_json": json.dumps(traits, ensure_ascii=False),
            "relationships_json": json.dumps({}, ensure_ascii=False),
            "inventory_json": json.dumps([], ensure_ascii=False),
            "story_flags_json": json.dumps([], ensure_ascii=False),
        }

    @staticmethod
    def generate_battle_character_events(
        attacker_chars: list[dict],
        defender_chars: list[dict],
        battle_result: dict,
        rng: random.Random,
    ) -> list[dict]:
        """
        为战斗生成角色相关事件。
        返回: [{event_type, title, description, character_name, effect}]
        """
        events = []
        result_type = battle_result.get("result_type", "stalemate")

        # 掌门对决
        atk_leader = next((c for c in attacker_chars if c.get("role") == "leader"), None)
        def_leader = next((c for c in defender_chars if c.get("role") == "leader"), None)

        if atk_leader and def_leader and rng.random() < 0.5:
            events.append({
                "event_type": "leader_duel",
                "title": "掌门对决",
                "description": f"{atk_leader['name']} 与 {def_leader['name']} 于战场中央交手，灵气激荡！",
                "character_name": atk_leader["name"],
                "phase": "climax",
            })

        # 长老大战
        atk_elders = [c for c in attacker_chars if c.get("role") == "elder"]
        def_elders = [c for c in defender_chars if c.get("role") == "elder"]
        if atk_elders and def_elders and rng.random() < 0.4:
            events.append({
                "event_type": "elder_battle",
                "title": "长老斗法",
                "description": f"双方长老展开激烈斗法，{atk_elders[0]['name']} 与 {def_elders[0]['name']} 各施绝技。",
                "character_name": atk_elders[0]["name"],
                "phase": "main_battle",
            })

        # 圣子临阵突破
        atk_heir = next((c for c in attacker_chars if c.get("role") == "heir"), None)
        def_heir = next((c for c in defender_chars if c.get("role") == "heir"), None)
        heir = atk_heir if atk_heir and rng.random() < 0.5 else def_heir
        if heir and rng.random() < 0.15:
            events.append({
                "event_type": "heir_breakthrough",
                "title": "临阵突破",
                "description": f"{heir['name']} 在生死关头顿悟，境界突破！战力暴涨！",
                "character_name": heir["name"],
                "phase": "climax",
            })

        # 叛徒开门（防守方有叛徒时）
        def_traitors = [c for c in defender_chars if c.get("role") == "traitor" or c.get("loyalty", 1) < 0.2]
        if def_traitors and result_type in ("decisive_victory", "victory") and rng.random() < 0.2:
            traitor = def_traitors[0]
            events.append({
                "event_type": "betrayal",
                "title": "临阵倒戈",
                "description": f"{traitor['name']} 暗中破坏护山大阵，防线崩溃！",
                "character_name": traitor["name"],
                "phase": "climax",
            })

        # 掌门负伤
        if result_type in ("defeat", "crushing_defeat") and atk_leader and rng.random() < 0.3:
            events.append({
                "event_type": "leader_wounded",
                "title": "掌门负伤",
                "description": f"{atk_leader['name']} 在战斗中负伤，宗门士气大损。",
                "character_name": atk_leader["name"],
                "phase": "result",
            })

        # 俘虏
        if result_type == "decisive_victory" and def_leader and rng.random() < 0.25:
            events.append({
                "event_type": "leader_captured",
                "title": "掌门被俘",
                "description": f"{def_leader['name']} 力战不敌，被生擒！",
                "character_name": def_leader["name"],
                "phase": "result",
            })

        return events

    @staticmethod
    def generate_character_events(characters: list[dict], turn: int, rng: random.Random) -> list[dict]:
        """生成角色日常事件（突破、叛逃、死亡等）"""
        events = []
        for char in characters:
            if char.get("status") != "active":
                continue

            # 突破事件
            if rng.random() < 0.02 * char.get("talent", 50) / 100:
                realm_idx = REALMS.index(char.get("realm", "炼气"))
                if realm_idx < 8 and rng.random() < char.get("luck", 0.5):
                    char["realm"] = REALMS[realm_idx + 1]
                    char["combat_power"] = int(char["combat_power"] * 1.3)
                    events.append({
                        "event_type": "breakthrough",
                        "title": "境界突破",
                        "description": f"{char['name']} 突破至 {char['realm']} 境界！",
                        "character_name": char["name"],
                        "sect_id": char.get("sect_id"),
                    })

            # 叛逃事件（野心高 + 忠诚低）
            if char.get("ambition", 0) > 0.7 and char.get("loyalty", 0.5) < 0.3 and rng.random() < 0.05:
                char["status"] = "betrayed"
                events.append({
                    "event_type": "betrayal",
                    "title": "弟子叛逃",
                    "description": f"{char['name']} 叛出师门，带走部分功法秘籍！",
                    "character_name": char["name"],
                    "sect_id": char.get("sect_id"),
                })

        return events
