import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
// DiplomacyGraph type used via API client return type inference
import * as echarts from 'echarts';
import { useEffect, useRef } from 'react';

const RELATION_COLORS: Record<string, string> = {
  alliance: '#22c55e', trade: '#3b82f6', non_aggression: '#14b8a6',
  neutral: '#6b7280', friendly: '#a3e635', vassal: '#a855f7',
  hostile: '#f97316', war: '#ef4444', mortal_enemy: '#dc2626',
};

export default function WorldDetailPage() {
  const { worldId } = useParams<{ worldId: string }>();
  const navigate = useNavigate();
  const chartRef = useRef<HTMLDivElement>(null);

  const { data: graph } = useQuery({
    queryKey: ['diplomacy-graph', worldId],
    queryFn: () => api.getDiplomacyGraph(worldId!),
    enabled: !!worldId,
  });

  useEffect(() => {
    if (!chartRef.current || !graph) return;
    const chart = echarts.init(chartRef.current, 'dark');

    const nodes = graph.nodes.map((n) => ({
      id: n.id,
      name: n.name,
      symbolSize: n.status === 'active' ? 30 : 15,
      itemStyle: { color: n.status === 'active' ? '#6366f1' : '#4b5563' },
      label: { show: true, fontSize: 11 },
    }));

    const links = graph.edges.map((e) => ({
      source: e.source,
      target: e.target,
      lineStyle: { color: RELATION_COLORS[e.relation_type] || '#6b7280', width: 2 },
      label: { show: true, formatter: e.relation_type, fontSize: 9, color: '#9ca3af' },
    }));

    chart.setOption({
      backgroundColor: '#0f172a',
      series: [{
        type: 'graph',
        layout: 'force',
        roam: true,
        force: { repulsion: 400, edgeLength: 150 },
        data: nodes,
        links: links,
      }],
    }, true);

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [graph]);

  return (
    <div className="max-w-5xl mx-auto p-6">
      <button onClick={() => navigate(`/worlds/${worldId}`)} className="text-slate-400 hover:text-white mb-4 block">
        ← 返回世界
      </button>
      <h1 className="text-2xl font-bold text-white mb-4">外交关系图</h1>
      <div className="flex gap-3 mb-4 flex-wrap">
        {Object.entries(RELATION_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1 text-xs">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-slate-400">{type}</span>
          </div>
        ))}
      </div>
      <div ref={chartRef} className="w-full h-[500px] bg-slate-900 rounded-xl border border-slate-700" />
    </div>
  );
}