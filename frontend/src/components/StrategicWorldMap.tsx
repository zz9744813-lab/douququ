import { useMemo, useState, useEffect, useRef, useCallback } from 'react';
import type { Region, Sect } from '../api/client';
import {
  Mountain, Wheat, TreePine, Droplets, Sun, Bug, Landmark,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import {
  forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide,
} from 'd3-force';
import type { SimulationNodeDatum, SimulationLinkDatum } from 'd3-force';

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

interface SimNode extends SimulationNodeDatum {
  id: string;
  region: Region;
}

interface SimLink extends SimulationLinkDatum<SimNode> {
  isWar?: boolean;
}

const SECT_COLORS: Record<string, string> = {
  sword: '#ef4444', alchemy: '#22c55e', formation: '#3b82f6',
  demon: '#a855f7', beast: '#f97316', artifact: '#eab308',
  merchant: '#14b8a6', hidden: '#6b7280',
};

const REGION_ICONS: Record<string, LucideIcon> = {
  mountain: Mountain,
  plain: Wheat,
  forest: TreePine,
  river: Droplets,
  desert: Sun,
  swamp: Bug,
  city: Landmark,
};

export default function StrategicWorldMap({
  regions,
  sects,
  selectedSectId,
  onSelectSect,
  battles = [],
  recentCaptures = [],
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [animatedRegions, setAnimatedRegions] = useState<Set<string>>(new Set());
  const [tooltip, setTooltip] = useState<{ x: number; y: number; content: string } | null>(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const isPanning = useRef(false);
  const panStart = useRef({ x: 0, y: 0 });

  const layout = useMemo(() => {
    if (!regions.length) return { nodes: [] as SimNode[], links: [] as SimLink[] };

    const nodes: SimNode[] = regions.map((r) => ({
      id: r.id,
      x: 0,
      y: 0,
      region: r,
    }));

    const linkSet = new Set<string>();
    const links: SimLink[] = [];
    regions.forEach((r) => {
      const adj = r.neighbors || [];
      adj.forEach((adjId: string) => {
        const key = [r.id, adjId].sort().join('-');
        if (!linkSet.has(key)) {
          linkSet.add(key);
          links.push({ source: r.id, target: adjId });
        }
      });
    });

    const sim = forceSimulation<SimNode>(nodes)
      .force('link', forceLink<SimNode, SimLink>(links).id((d: SimNode) => d.id).distance(120))
      .force('charge', forceManyBody<SimNode>().strength(-300))
      .force('center', forceCenter(400, 300))
      .force('collide', forceCollide<SimNode>().radius(35))
      .tick(300);

    sim.stop();

    return { nodes, links };
  }, [regions]);

  useEffect(() => {
    if (recentCaptures.length > 0) {
      const newCaptures = new Set(recentCaptures.map(c => c.region_id));
      setAnimatedRegions(newCaptures);
      const timer = setTimeout(() => setAnimatedRegions(new Set()), 2000);
      return () => clearTimeout(timer);
    }
  }, [recentCaptures]);

  const getSectColor = (sectId: string | null) => {
    if (!sectId) return '#1a1a2e';
    const sect = sects.find(s => s.id === sectId);
    return sect ? SECT_COLORS[sect.sect_type] || '#6b7280' : '#1a1a2e';
  };

  const getSectName = (sectId: string | null) => {
    if (!sectId) return '无主';
    const sect = sects.find(s => s.id === sectId);
    return sect?.name || '未知';
  };

  const warLinkIds = useMemo(() => {
    const ids = new Set<string>();
    battles.forEach((b) => {
      ids.add([b.attacker_sect_id, b.defender_sect_id].sort().join('-'));
    });
    return ids;
  }, [battles]);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    setTransform((prev) => ({
      ...prev,
      k: Math.max(0.3, Math.min(5, prev.k * factor)),
    }));
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0) {
      isPanning.current = true;
      panStart.current = { x: e.clientX - transform.x, y: e.clientY - transform.y };
    }
  }, [transform.x, transform.y]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isPanning.current) {
      setTransform((prev) => ({
        ...prev,
        x: e.clientX - panStart.current.x,
        y: e.clientY - panStart.current.y,
      }));
    }
  }, []);

  const handleMouseUp = useCallback(() => {
    isPanning.current = false;
  }, []);

  const svgWidth = 800;
  const svgHeight = 600;

  return (
    <div className="w-full h-full relative ink-wash-bg">
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="select-none"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isPanning.current ? 'grabbing' : 'grab' }}
      >
        <defs>
          <radialGradient id="bg-gradient" cx="50%" cy="50%" r="70%">
            <stop offset="0%" stopColor="#0a0a14" />
            <stop offset="100%" stopColor="#050508" />
          </radialGradient>
          <filter id="ink-texture" x="-10%" y="-10%" width="120%" height="120%">
            <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="4" result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="2" />
          </filter>
          <filter id="region-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="war-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="coloredBlur" />
            <feFlood floodColor="#ef4444" floodOpacity="0.6" result="color" />
            <feComposite in="color" in2="coloredBlur" operator="in" result="shadow" />
            <feMerge>
              <feMergeNode in="shadow" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="capture-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <rect width="100%" height="100%" fill="url(#bg-gradient)" />

        <pattern id="subtle-grid" width="60" height="60" patternUnits="userSpaceOnUse">
          <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#0f0f1a" strokeWidth="0.3" />
        </pattern>
        <rect width="100%" height="100%" fill="url(#subtle-grid)" />

        <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>
          {layout.links.map((link, i) => {
            const source = link.source as SimNode;
            const target = link.target as SimNode;
            if (!source.x || !target.x) return null;

            const fromRegion = regions.find(r => r.id === source.id);
            const toRegion = regions.find(r => r.id === target.id);
            const fromOwner = fromRegion?.owner_sect_id;
            const toOwner = toRegion?.owner_sect_id;
            const isWar = fromOwner && toOwner && fromOwner !== toOwner &&
              warLinkIds.has([fromOwner, toOwner].sort().join('-'));

            if (isWar) {
              return (
                <line key={`war-${i}`} x1={source.x} y1={source.y} x2={target.x} y2={target.y}
                  stroke="#ef4444" strokeWidth="2.5" strokeDasharray="8,4" opacity="0.8" filter="url(#war-glow)">
                  <animate attributeName="stroke-dashoffset" from="0" to="24" dur="1.5s" repeatCount="indefinite" />
                </line>
              );
            }

            if (fromOwner && toOwner && fromOwner !== toOwner) {
              return (
                <line key={`border-${i}`} x1={source.x} y1={source.y} x2={target.x} y2={target.y}
                  stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="6,4" opacity="0.5">
                  <animate attributeName="stroke-dashoffset" from="0" to="20" dur="2s" repeatCount="indefinite" />
                </line>
              );
            }

            return (
              <line key={`edge-${i}`} x1={source.x} y1={source.y} x2={target.x} y2={target.y}
                stroke="#1e293b" strokeWidth="0.8" opacity="0.4" />
            );
          })}

          {layout.nodes.map((node) => {
            const region = node.region;
            const ownerId = region.owner_sect_id;
            const color = getSectColor(ownerId);
            const isAnimated = animatedRegions.has(region.id);
            const isSelected = selectedSectId && ownerId === selectedSectId;
            const RegionIcon = REGION_ICONS[region.region_type] || Landmark;

            return (
              <g key={node.id} className="cursor-pointer"
                onClick={() => ownerId && onSelectSect?.(ownerId)}
                onMouseEnter={() => {
                  const rect = svgRef.current?.getBoundingClientRect();
                  if (rect) {
                    setTooltip({
                      x: (node.x! * transform.k + transform.x) + rect.left,
                      y: (node.y! * transform.k + transform.y) + rect.top - 10,
                      content: `${region.name} (${region.region_type}) | ${getSectName(ownerId)} | 防御: ${region.defense_level}`,
                    });
                  }
                }}
                onMouseLeave={() => setTooltip(null)}
              >
                {isSelected && (
                  <circle cx={node.x} cy={node.y} r={34} fill="none" stroke={color} strokeWidth="1" opacity="0.3" filter="url(#region-glow)" />
                )}
                <circle cx={node.x} cy={node.y} r={isSelected ? 28 : 22}
                  fill={color + '15'} stroke={color}
                  strokeWidth={isSelected ? 3 : isAnimated ? 3 : 1.5}
                  filter={isAnimated ? 'url(#capture-glow)' : undefined}
                >
                  {isAnimated && (
                    <animate attributeName="r" values="22;30;22" dur="1s" repeatCount="3" />
                  )}
                </circle>
                <foreignObject x={node.x! - 10} y={node.y! - 14} width={20} height={20} className="pointer-events-none">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
                    <RegionIcon size={12} style={{ color }} />
                  </div>
                </foreignObject>
                <text x={node.x} y={node.y! + 10} textAnchor="middle" className="pointer-events-none" fill="#94a3b8" fontSize="9">
                  {region.name}
                </text>
                {ownerId && (
                  <text x={node.x} y={node.y! + 38} textAnchor="middle" className="pointer-events-none" fill={color} fontSize="8" opacity="0.8">
                    {getSectName(ownerId)}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {tooltip && (
        <div className="fixed z-50 px-3 py-1.5 bg-ink-900 border border-ink-700 rounded text-xs text-ink-200 pointer-events-none whitespace-nowrap"
          style={{ left: tooltip.x, top: tooltip.y, transform: 'translate(-50%, -100%)' }}>
          {tooltip.content}
        </div>
      )}
    </div>
  );
}
