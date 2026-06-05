"""
World Service - 世界创建与管理
负责创建世界、生成地图、初始化宗门
"""
import json
import random
import math
from typing import Any

from app.models.world import World
from app.models.sect import Sect
from app.models.region import Region
from app.models.diplomacy import DiplomacyRelation
from app.models.turn import TurnRecord
from app.models.event import WorldEvent
from app.models.battle import Battle


SECT_TEMPLATES = {
    "sword": {
        "type": "sword", "name_suffix": "剑宗",
        "stats": {"military_power": 70, "spiritual_power": 50, "economy": 30, "alchemy": 20, "artifact_crafting": 30, "formation": 20, "intelligence": 30, "reputation": 50, "stability": 0.6, "trustworthiness": 0.6, "luck": 0.5},
        "personality": {"ambition": 0.7, "aggression": 0.8, "risk_tolerance": 0.6, "honor": 0.7, "patience": 0.3, "diplomacy": 0.4, "greed": 0.4, "paranoia": 0.3, "loyalty": 0.7},
        "resources": {"spirit_stones": 500, "pills": 10, "artifacts": 15, "techniques": 5, "spirit_herbs": 20, "materials": 30},
    },
    "alchemy": {
        "type": "alchemy", "name_suffix": "丹宗",
        "stats": {"military_power": 30, "spiritual_power": 60, "economy": 70, "alchemy": 80, "artifact_crafting": 20, "formation": 30, "intelligence": 40, "reputation": 60, "stability": 0.7, "trustworthiness": 0.8, "luck": 0.5},
        "personality": {"ambition": 0.4, "aggression": 0.2, "risk_tolerance": 0.3, "honor": 0.8, "patience": 0.7, "diplomacy": 0.8, "greed": 0.5, "paranoia": 0.3, "loyalty": 0.8},
        "resources": {"spirit_stones": 800, "pills": 30, "artifacts": 5, "techniques": 5, "spirit_herbs": 40, "materials": 20},
    },
    "formation": {
        "type": "formation", "name_suffix": "阵宗",
        "stats": {"military_power": 40, "spiritual_power": 50, "economy": 40, "alchemy": 30, "artifact_crafting": 30, "formation": 80, "intelligence": 50, "reputation": 50, "stability": 0.8, "trustworthiness": 0.7, "luck": 0.5},
        "personality": {"ambition": 0.3, "aggression": 0.2, "risk_tolerance": 0.2, "honor": 0.7, "patience": 0.9, "diplomacy": 0.6, "greed": 0.3, "paranoia": 0.5, "loyalty": 0.8},
        "resources": {"spirit_stones": 600, "pills": 10, "artifacts": 10, "techniques": 5, "spirit_herbs": 20, "materials": 40},
    },
    "demon": {
        "type": "demon", "name_suffix": "魔宗",
        "stats": {"military_power": 75, "spiritual_power": 55, "economy": 40, "alchemy": 30, "artifact_crafting": 25, "formation": 15, "intelligence": 40, "reputation": 20, "stability": 0.5, "trustworthiness": 0.2, "luck": 0.6},
        "personality": {"ambition": 0.9, "aggression": 0.9, "risk_tolerance": 0.8, "honor": 0.1, "patience": 0.2, "diplomacy": 0.3, "greed": 0.9, "paranoia": 0.7, "loyalty": 0.2},
        "resources": {"spirit_stones": 600, "pills": 10, "artifacts": 10, "techniques": 5, "spirit_herbs": 15, "materials": 25},
    },
    "beast": {
        "type": "beast", "name_suffix": "御兽宗",
        "stats": {"military_power": 60, "spiritual_power": 45, "economy": 35, "alchemy": 25, "artifact_crafting": 20, "formation": 20, "intelligence": 30, "reputation": 40, "stability": 0.6, "trustworthiness": 0.5, "luck": 0.6},
        "personality": {"ambition": 0.5, "aggression": 0.6, "risk_tolerance": 0.5, "honor": 0.5, "patience": 0.5, "diplomacy": 0.4, "greed": 0.5, "paranoia": 0.4, "loyalty": 0.6},
        "resources": {"spirit_stones": 500, "pills": 10, "artifacts": 5, "techniques": 5, "spirit_herbs": 30, "materials": 25},
    },
    "artifact": {
        "type": "artifact", "name_suffix": "器宗",
        "stats": {"military_power": 40, "spiritual_power": 45, "economy": 50, "alchemy": 20, "artifact_crafting": 80, "formation": 25, "intelligence": 35, "reputation": 45, "stability": 0.6, "trustworthiness": 0.6, "luck": 0.5},
        "personality": {"ambition": 0.5, "aggression": 0.4, "risk_tolerance": 0.4, "honor": 0.6, "patience": 0.6, "diplomacy": 0.6, "greed": 0.6, "paranoia": 0.4, "loyalty": 0.6},
        "resources": {"spirit_stones": 600, "pills": 10, "artifacts": 25, "techniques": 5, "spirit_herbs": 15, "materials": 40},
    },
    "merchant": {
        "type": "merchant", "name_suffix": "商盟",
        "stats": {"military_power": 25, "spiritual_power": 35, "economy": 90, "alchemy": 30, "artifact_crafting": 30, "formation": 15, "intelligence": 60, "reputation": 70, "stability": 0.7, "trustworthiness": 0.5, "luck": 0.5},
        "personality": {"ambition": 0.6, "aggression": 0.2, "risk_tolerance": 0.4, "honor": 0.4, "patience": 0.6, "diplomacy": 0.9, "greed": 0.8, "paranoia": 0.5, "loyalty": 0.3},
        "resources": {"spirit_stones": 1200, "pills": 15, "artifacts": 10, "techniques": 3, "spirit_herbs": 25, "materials": 30},
    },
    "hidden": {
        "type": "hidden", "name_suffix": "隐宗",
        "stats": {"military_power": 35, "spiritual_power": 70, "economy": 30, "alchemy": 40, "artifact_crafting": 30, "formation": 40, "intelligence": 50, "reputation": 15, "stability": 0.9, "trustworthiness": 0.5, "luck": 0.8},
        "personality": {"ambition": 0.7, "aggression": 0.2, "risk_tolerance": 0.3, "honor": 0.5, "patience": 0.9, "diplomacy": 0.3, "greed": 0.3, "paranoia": 0.8, "loyalty": 0.5},
        "resources": {"spirit_stones": 400, "pills": 15, "artifacts": 5, "techniques": 10, "spirit_herbs": 20, "materials": 15},
    },
}

REGION_NAMES = [
    "苍梧山", "落霞峰", "黑水泽", "白鹿原", "青冥谷",
    "紫竹林", "赤焰岭", "玄武湖", "飞龙渊", "翠微山",
    "金乌崖", "玉虚峰", "碧落谷", "黄泉渊", "星辰海",
    "太虚境", "须弥山", "无妄海", "归墟谷", "琉璃峰",
]

REGION_TYPES = ["spirit_mine", "spirit_vein", "mortal_city", "wilderness", "secret_realm", "demon_cave", "border_pass", "sect_peak"]


class WorldService:
    """世界创建与管理服务"""

    @staticmethod
    def create_world(db, name: str, description: str = "", mode: str = "season",
                     max_turns: int = 100, sect_count: int = 8, map_size: str = "medium",
                     world_seed: int = 42, rules: dict | None = None) -> World:
        """创建新世界，包括地图和宗门"""
        import uuid
        random.seed(world_seed)

        world = World(
            id=uuid.uuid4().hex[:12],
            name=name,
            description=description,
            status="created",
            current_turn=0,
            max_turns=max_turns,
            world_seed=world_seed,
            mode=mode,
            map_size=map_size,
            sect_count=sect_count,
            rules_json=json.dumps(rules or {}, ensure_ascii=False),
        )
        db.add(world)
        db.flush()

        # 生成地图区域
        region_count = {"small": 12, "medium": 20, "large": 30}.get(map_size, 20)
        regions = WorldService._generate_regions(world.id, region_count, world_seed)
        for r in regions:
            db.add(r)
        db.flush()

        # 生成宗门
        sect_types = list(SECT_TEMPLATES.keys())
        selected_types = random.sample(sect_types, min(sect_count, len(sect_types)))
        if len(selected_types) < sect_count:
            selected_types += random.choices(sect_types, k=sect_count - len(selected_types))

        sects = []
        for i, stype in enumerate(selected_types):
            template = SECT_TEMPLATES[stype]
            sect = Sect(
                id=uuid.uuid4().hex[:12],
                world_id=world.id,
                name=f"{REGION_NAMES[i]}{template['name_suffix']}",
                sect_type=template["type"],
                leader_name=f"掌门{i+1}",
                status="active",
                resources_json=json.dumps(template["resources"], ensure_ascii=False),
                stats_json=json.dumps(template["stats"], ensure_ascii=False),
                personality_json=json.dumps(template["personality"], ensure_ascii=False),
                memory_json=json.dumps([], ensure_ascii=False),
                controlled_regions_json=json.dumps([], ensure_ascii=False),
            )
            db.add(sect)
            sects.append(sect)
        db.flush()

        # 分配宗门初始地盘
        WorldService._assign_initial_regions(sects, regions, db)

        # 初始化外交关系
        WorldService._init_diplomacy(world.id, sects, db)

        db.commit()
        random.seed()
        return world

    @staticmethod
    def _generate_regions(world_id: str, count: int, seed: int) -> list[Region]:
        """生成地图区域"""
        import uuid
        random.seed(seed)
        regions = []
        used_names = set()
        for i in range(count):
            name = REGION_NAMES[i % len(REGION_NAMES)]
            if name in used_names:
                name = f"{name}{i}"
            used_names.add(name)
            rtype = random.choices(
                REGION_TYPES,
                weights=[0.15, 0.15, 0.15, 0.2, 0.1, 0.1, 0.1, 0.05],
                k=1,
            )[0]
            resource_level = random.randint(1, 3)
            region = Region(
                id=uuid.uuid4().hex[:12],
                world_id=world_id,
                name=name,
                region_type=rtype,
                owner_sect_id=None,
                resource_level=resource_level,
                defense_level=1,
                stability=1.0,
                neighbors_json=json.dumps([], ensure_ascii=False),
                special_flags_json=json.dumps([], ensure_ascii=False),
            )
            regions.append(region)
        random.seed()
        return regions

    @staticmethod
    def _assign_initial_regions(sects: list[Sect], regions: list[Region], db):
        """为每个宗门分配初始地盘"""
        random.shuffle(regions)
        regions_per_sect = max(1, len(regions) // len(sects))
        for i, sect in enumerate(sects):
            start = i * regions_per_sect
            end = start + regions_per_sect if i < len(sects) - 1 else len(regions)
            assigned = regions[start:end]
            controlled = []
            for r in assigned:
                r.owner_sect_id = sect.id
                controlled.append(r.id)
            sect.controlled_regions_json = json.dumps(controlled, ensure_ascii=False)

    @staticmethod
    def _init_diplomacy(world_id: str, sects: list[Sect], db):
        """初始化宗门间外交关系"""
        import uuid
        for i, a in enumerate(sects):
            for b in sects[i + 1:]:
                rel = DiplomacyRelation(
                    id=uuid.uuid4().hex[:12],
                    world_id=world_id,
                    sect_a_id=a.id,
                    sect_b_id=b.id,
                    relation_type="neutral",
                    relation_score=0.0,
                    trust_score=0.5,
                    treaties_json=json.dumps([], ensure_ascii=False),
                    history_json=json.dumps([], ensure_ascii=False),
                )
                db.add(rel)