import { useMemo, useState, useEffect } from 'react';
import type { Region, Sect } from '../api/client';

interface Props {
  regions: Region[];
  sects: Sect[];
  selectedSectId?: string | null;
  onSelectSect?: (id: string) => void;
  battles?: Array<{
    attacker_sect_id: string;
    defender_sect_id: string;
    turn: number;
    result_type: string;
  }>;
  recentCaptures?: Array<{
    region_id: string;
    from_sect_id: string;
    to_sect_id: string;
    turn: number;
  }>;
}

const SECT_COLORS: Record<string, string> = {
  sword: '#ef4444', alchemy: '#22c55e', formation: '#3b82f6',
  demon: '#a855f7', beast: '#f97316', artifact: '#eab308',
  merchant: '#14b8a6', hidden: '#6b7280',
};

export default function StrategicWorldMap({
  regions,
  sects,
  selectedSectId,
  onSelectSect,
  battles = [],
  recentCaptures = [],
}: Props) {
  const [animatedRegions, setAnimatedRegions] = useState<Set<string>>(new Set());

  // 计算布局
  const layout = useMemo(() => {
    if (!regions.length) return { nodes: [] as Array<{ id: string; x: number; y: number; region: Region }>, edges: [] as Array<{ from: string; to: string }> };

    const positions = regions.map((r, i) => {
      return {
        id: r.id,
        x: (i % 5) * 180 + 80,
        y: Math.floor(i / 5) * 140 + 60,
        region: r,
      };
    });

    // 构建边（邻接关系）
    const edges: Array<{ from: string; to: string }> = [];
    regions.forEach((r) => {
      const adj = r.neighbors || [];
      adj.forEach((adjId: string) => {
        if (adjId > r.id) { // 避免重复
          edges.push({ from: r.id, to: adjId });
        }
      });
    });

    return { nodes: positions, edges };
  }, [regions]);

  // 吞并动画
  useEffect(() => {
    if (recentCaptures.length > 0) {
      const newCaptures = new Set(recentCaptures.map(c => c.region_id));
      setAnimatedRegions(newCaptures);
      const timer = setTimeout(() => setAnimatedRegions(new Set()), 2000);
      return () => clearTimeout(timer);
    }
  }, [recentCaptures]);

  const getSectColor = (sectId: string | null) => {
    if (!sectId) return '#334155';
    const sect = sects.find(s => s.id === sectId);
    return sect ? SECT_COLORS[sect.sect_type] || '#6b7280' : '#334155';
  };

  const getSectName = (sectId: string | null) => {
    if (!sectId) return '无主';
    const sect = sects.find(s => s.id === sectId);
    return sect?.name || '未知';
  };

  // 活跃战线（不同宗门相邻的区域）
  const warLines = useMemo(() => {
    const lines: Array<{ from: { x: number; y: number }; to: { x: number; y: number }; color: string }> = [];
    layout.edges.forEach((edge) => {
      const fromNode = layout.nodes.find(n => n.id === edge.from);
      const toNode = layout.nodes.find(n => n.id === edge.to);
      const fromRegion = regions.find(r => r.id === edge.from);
      const toRegion = regions.find(r => r.id === edge.to);
      if (fromNode && toNode && fromRegion && toRegion) {
        const fromOwner = fromRegion.owner_sect_id;
        const toOwner = toRegion.owner_sect_id;
        if (fromOwner && toOwner && fromOwner !== toOwner) {
          // 检查是否有战争
          const hasWar = battles.some(b =>
            (b.attacker_sect_id === fromOwner && b.defender_sect_id === toOwner) ||
            (b.attacker_sect_id === toOwner && b.defender_sect_id === fromOwner)
          );
          lines.push({
            from: { x: fromNode.x, y: fromNode.y },
            to: { x: toNode.x, y: toNode.y },
            color: hasWar ? '#ef4444' : '#f59e0b',
          });
        }
      }
    });
    return lines;
  }, [layout, regions, sects, battles]);

  const svgWidth = Math.max(800, ...layout.nodes.map(n => n.x + 120));
  const svgHeight = Math.max(600, ...layout.nodes.map(n => n.y + 100));

  return (
    <svg width="100%" height="100%" viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="bg-gradient-to-b from-slate-950 to-slate-900">
      {/* 背景网格 */}
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.5" />
        </pattern>
        {/* 吞并动画 */}
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />

      {/* 战线 */}
      {warLines.map((line, i) => (
        <line
          key={`war-${i}`}
          x1={line.from.x} y1={line.from.y}
          x2={line.to.x} y2={line.to.y}
          stroke={line.color}
          strokeWidth="2"
          strokeDasharray="5,5"
          opacity="0.6"
        >
          <animate attributeName="stroke-dashoffset" from="0" to="10" dur="1s" repeatCount="indefinite" />
        </line>
      ))}

      {/* 邻接边（和平） */}
      {layout.edges.map((edge, i) => {
        const fromNode = layout.nodes.find(n => n.id === edge.from);
        const toNode = layout.nodes.find(n => n.id === edge.to);
        const fromRegion = regions.find(r => r.id === edge.from);
        const toRegion = regions.find(r => r.id === edge.to);
        const isWarLine = fromRegion && toRegion && fromRegion.owner_sect_id && toRegion.owner_sect_id &&
          fromRegion.owner_sect_id !== toRegion.owner_sect_id;
        if (isWarLine) return null;
        if (!fromNode || !toNode) return null;
        return (
          <line
            key={`edge-${i}`}
            x1={fromNode.x} y1={fromNode.y}
            x2={toNode.x} y2={toNode.y}
            stroke="#475569"
            strokeWidth="1"
            opacity="0.3"
          />
        );
      })}

      {/* 区域节点 */}
      {layout.nodes.map((node) => {
        const region = node.region;
        const ownerId = region.owner_sect_id;
        const color = getSectColor(ownerId);
        const isAnimated = animatedRegions.has(region.id);
        const isSelected = selectedSectId && ownerId === selectedSectId;

        return (
          <g key={node.id}>
            {/* 区域圆圈 */}
            <circle
              cx={node.x}
              cy={node.y}
              r={isSelected ? 28 : 22}
              fill={color + '20'}
              stroke={color}
              strokeWidth={isSelected ? 3 : isAnimated ? 3 : 1.5}
              className="cursor-pointer transition-all"
              filter={isAnimated ? 'url(#glow)' : undefined}
              onClick={() => ownerId && onSelectSect?.(ownerId)}
            >
              {isAnimated && (
                <animate attributeName="r" values="22;28;22" dur="1s" repeatCount="3" />
              )}
            </circle>

            {/* 区域类型图标 */}
            <text
              x={node.x}
              y={node.y - 5}
              textAnchor="middle"
              className="text-xs pointer-events-none"
              fill={color}
              fontSize="10"
            >
              {region.region_type === 'mountain' ? '⛰️' :
               region.region_type === 'plain' ? '🌾' :
               region.region_type === 'forest' ? '🌲' :
               region.region_type === 'river' ? '💧' :
               region.region_type === 'desert' ? '🏜️' :
               region.region_type === 'swamp' ? '🐸' : '🏛️'}
            </text>

            {/* 区域名称 */}
            <text
              x={node.x}
              y={node.y + 8}
              textAnchor="middle"
              className="pointer-events-none"
              fill="#94a3b8"
              fontSize="9"
            >
              {region.name}
            </text>

            {/* 所有者标签 */}
            {ownerId && (
              <text
                x={node.x}
                y={node.y + 38}
                textAnchor="middle"
                className="pointer-events-none"
                fill={color}
                fontSize="8"
                opacity="0.8"
              >
                {getSectName(ownerId)}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
