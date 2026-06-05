"""
Map Engine - 地图引擎
生成真实连通地图，包含坐标和邻接关系。
"""
import json
import random
import math
from typing import Any

import uuid


class MapEngine:
    """地图引擎：生成连通地图"""

    REGION_NAMES = [
        "苍梧山", "落霞峰", "黑水泽", "白鹿原", "青冥谷",
        "紫竹林", "赤焰岭", "玄武湖", "飞龙渊", "翠微山",
        "金乌崖", "玉虚峰", "碧落谷", "黄泉渊", "星辰海",
        "太虚境", "须弥山", "无妄海", "归墟谷", "琉璃峰",
        "云梦泽", "蓬莱岛", "昆仑墟", "九幽冥", "天剑山",
        "丹霞谷", "冰魄原", "炎魔岭", "神木林", "万毒沼",
    ]

    REGION_TYPES = [
        "spirit_mine", "spirit_vein", "mortal_city", "wilderness",
        "secret_realm", "demon_cave", "border_pass", "sect_peak",
        "ancient_ruins", "forbidden_zone",
    ]

    @staticmethod
    def generate_connected_map(world_id: str, count: int, seed: int) -> list[dict]:
        """
        生成连通地图。
        1. 生成 N 个区域节点，每个有 x/y 坐标
        2. 用最小生成树保证全图连通
        3. 再添加额外边形成多路径
        4. 返回区域列表（含 neighbors_json）
        """
        random.seed(seed)
        regions = MapEngine._generate_nodes(world_id, count)
        MapEngine._assign_positions(regions, count)
        MapEngine._build_neighbors(regions, count)
        random.seed()
        return regions

    @staticmethod
    def _generate_nodes(world_id: str, count: int) -> list[dict]:
        """生成区域节点（不含坐标和邻接）"""
        used_names = set()
        nodes = []
        for i in range(count):
            name = MapEngine.REGION_NAMES[i % len(MapEngine.REGION_NAMES)]
            if name in used_names:
                name = f"{name}{i}"
            used_names.add(name)

            rtype = random.choices(
                MapEngine.REGION_TYPES,
                weights=[0.15, 0.15, 0.12, 0.15, 0.08, 0.08, 0.1, 0.08, 0.05, 0.04],
                k=1,
            )[0]

            resource_level = random.randint(1, 3)
            nodes.append({
                "id": uuid.uuid4().hex[:12],
                "world_id": world_id,
                "name": name,
                "region_type": rtype,
                "owner_sect_id": None,
                "resource_level": resource_level,
                "defense_level": 1,
                "stability": 1.0,
                "pos_x": 0.0,
                "pos_y": 0.0,
                "neighbors": [],
                "special_flags": [],
            })
        return nodes

    @staticmethod
    def _assign_positions(nodes: list[dict], count: int):
        """为每个区域分配 2D 坐标，使用环形布局 + 随机扰动"""
        # 使用环形布局 + 随机扰动
        for i, node in enumerate(nodes):
            angle = (i / count) * math.pi * 2
            # 主半径 + 随机扰动
            radius = 180 + random.uniform(-40, 40)
            node["pos_x"] = 200 + math.cos(angle) * radius
            node["pos_y"] = 200 + math.sin(angle) * radius

    @staticmethod
    def _build_neighbors(nodes: list[dict], count: int):
        """构建邻接关系：最小生成树 + 额外边"""
        if count <= 1:
            return

        # 计算所有点对之间的距离
        edges = []
        for i in range(count):
            for j in range(i + 1, count):
                dx = nodes[i]["pos_x"] - nodes[j]["pos_x"]
                dy = nodes[i]["pos_y"] - nodes[j]["pos_y"]
                dist = math.sqrt(dx * dx + dy * dy)
                edges.append((dist, i, j))

        edges.sort(key=lambda x: x[0])

        # Kruskal 最小生成树
        parent = list(range(count))

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x: int, y: int):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        mst_edges = []
        for dist, i, j in edges:
            if find(i) != find(j):
                union(i, j)
                mst_edges.append((i, j))

        # 添加额外边（形成多路径，增加战略性）
        extra_edges = []
        # 添加一些短距离的额外边
        short_edges = [e for e in edges if (e[1], e[2]) not in mst_edges and (e[2], e[1]) not in mst_edges]
        short_edges.sort(key=lambda x: x[0])
        extra_count = min(count // 3, len(short_edges))
        for k in range(extra_count):
            extra_edges.append((short_edges[k][1], short_edges[k][2]))

        # 设置邻接关系
        all_edges = mst_edges + extra_edges
        for i, j in all_edges:
            nodes[i]["neighbors"].append(nodes[j]["id"])
            nodes[j]["neighbors"].append(nodes[i]["id"])

        # 确保每个区域至少有 1 个邻居
        for node in nodes:
            if not node["neighbors"]:
                # 找到最近的区域
                min_dist = float('inf')
                nearest = None
                for other in nodes:
                    if other["id"] == node["id"]:
                        continue
                    dx = node["pos_x"] - other["pos_x"]
                    dy = node["pos_y"] - other["pos_y"]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < min_dist:
                        min_dist = dist
                        nearest = other
                if nearest:
                    node["neighbors"].append(nearest["id"])
                    nearest["neighbors"].append(node["id"])

    @staticmethod
    def assign_spawn_points(nodes: list[dict], sect_count: int, seed: int) -> list[list[str]]:
        """
        为宗门分配出生点，尽量分散。
        返回：每个宗门分配的区域 ID 列表
        """
        random.seed(seed)
        # 按角度排序，均匀分配
        nodes_with_angle = []
        for node in nodes:
            angle = math.atan2(node["pos_y"] - 200, node["pos_x"] - 200)
            nodes_with_angle.append((angle, node["id"]))
        nodes_with_angle.sort(key=lambda x: x[0])

        regions_per_sect = max(1, len(nodes) // sect_count)
        assignments = []
        for i in range(sect_count):
            start = i * regions_per_sect
            end = start + regions_per_sect if i < sect_count - 1 else len(nodes_with_angle)
            assigned = [nodes_with_angle[j][1] for j in range(start, end)]
            assignments.append(assigned)

        random.seed()
        return assignments

    @staticmethod
    def get_border_regions(nodes: list[dict], sect_id: str) -> list[str]:
        """获取宗门的边境区域（与敌方相邻的区域）"""
        owned = {n["id"] for n in nodes if n.get("owner_sect_id") == sect_id}
        borders = []
        for node in nodes:
            if node.get("owner_sect_id") != sect_id:
                continue
            for neighbor_id in node.get("neighbors", []):
                neighbor = next((n for n in nodes if n["id"] == neighbor_id), None)
                if neighbor and neighbor.get("owner_sect_id") != sect_id:
                    if node["id"] not in borders:
                        borders.append(node["id"])
                    break
        return borders

    @staticmethod
    def get_war_targets(nodes: list[dict], sect_id: str) -> list[dict]:
        """获取可攻击的敌方区域（与己方边境相邻的敌方区域）"""
        owned = {n["id"] for n in nodes if n.get("owner_sect_id") == sect_id}
        targets = []
        seen = set()
        for node in nodes:
            if node.get("owner_sect_id") != sect_id:
                continue
            for neighbor_id in node.get("neighbors", []):
                if neighbor_id in owned:
                    continue
                if neighbor_id not in seen:
                    seen.add(neighbor_id)
                    neighbor = next((n for n in nodes if n["id"] == neighbor_id), None)
                    if neighbor:
                        targets.append(neighbor)
        return targets
