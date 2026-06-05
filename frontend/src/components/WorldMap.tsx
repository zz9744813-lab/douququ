import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { MapData, Sect, Region } from '../api/client';

const SECT_COLORS: Record<string, string> = {
  sword: '#ef4444', alchemy: '#22c55e', formation: '#3b82f6',
  demon: '#a855f7', beast: '#f97316', artifact: '#eab308',
  merchant: '#14b8a6', hidden: '#6b7280',
};

interface Props {
  mapData: MapData | null;
  regions: Region[];
  sects: Sect[];
  selectedSectId?: string;
  onSelectSect: (id: string) => void;
}

export default function WorldMap({ mapData, regions, sects, selectedSectId, onSelectSect }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || !mapData || regions.length === 0) return;

    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current, 'dark');
    }
    const chart = instanceRef.current;

    const sectMap = new Map(mapData.sects.map((s) => [s.id, s]));
    // regionMap available for future use
    void regions;

    // Create nodes
    const nodes = mapData.nodes.map((n, i) => {
      const angle = (i / mapData.nodes.length) * Math.PI * 2;
      const radius = 180;
      const owner = n.owner_sect_id ? sectMap.get(n.owner_sect_id) : null;
      const ownerSect = owner ? sects.find((s) => s.id === owner.id) : null;
      const size = 20 + n.resource_level * 6;

      return {
        id: n.id,
        name: n.name,
        x: 200 + Math.cos(angle) * radius,
        y: 200 + Math.sin(angle) * radius,
        symbolSize: size,
        itemStyle: {
          color: ownerSect ? SECT_COLORS[ownerSect.sect_type] || '#888' : '#555',
          borderColor: n.owner_sect_id === selectedSectId ? '#fff' : 'transparent',
          borderWidth: n.owner_sect_id === selectedSectId ? 3 : 0,
        },
        label: { show: true, fontSize: 10, color: '#ccc' },
        data: {
          ownerName: n.owner_name || '无主',
          type: n.region_type,
          resourceLevel: n.resource_level,
          ownerSectId: n.owner_sect_id,
        },
      };
    });

    // Create edges (neighbors)
    const links: Array<{ source: string; target: string }> = [];
    const nodeIds = new Set(mapData.nodes.map((n) => n.id));
    mapData.nodes.forEach((n) => {
      n.neighbors.forEach((neighborId) => {
        if (nodeIds.has(neighborId)) {
          const key = [n.id, neighborId].sort().join('-');
          if (!links.some((l) => [l.source, l.target].sort().join('-') === key)) {
            links.push({ source: n.id, target: neighborId });
          }
        }
      });
    });

    const option: echarts.EChartsOption = {
      backgroundColor: '#0f172a',
      tooltip: {
        formatter: (params: unknown) => {
          const p = params as { data: { name: string; ownerName: string; type: string; resourceLevel: number } };
          return `<strong>${p.data.name}</strong><br/>
            归属: ${p.data.ownerName}<br/>
            类型: ${p.data.type}<br/>
            资源等级: ${p.data.resourceLevel}`;
        },
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          roam: true,
          draggable: true,
          force: { repulsion: 300, edgeLength: 100 },
          data: nodes,
          links: links.map((l) => ({
            ...l,
            lineStyle: { color: '#334155', width: 1, curveness: 0.1 },
          })),
          emphasis: {
            focus: 'adjacency',
            lineStyle: { width: 3 },
          },
        },
      ],
    };

    chart.setOption(option, true);

    chart.on('click', (params: unknown) => {
      const p = params as { data?: { ownerSectId?: string } };
      if (p.data?.ownerSectId) {
        onSelectSect(p.data.ownerSectId);
      }
    });

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [mapData, regions, sects, selectedSectId, onSelectSect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      instanceRef.current?.dispose();
      instanceRef.current = null;
    };
  }, []);

  if (!mapData || regions.length === 0) {
    return <div className="flex items-center justify-center h-full text-slate-500">加载地图...</div>;
  }

  return <div ref={chartRef} className="w-full h-full" />;
}