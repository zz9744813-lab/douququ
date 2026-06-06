import { Swords, Coins, Leaf, Shield, BarChart3, Map } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface SectData {
  id: string;
  name: string;
  sect_type: string;
  status: string;
  resources: Record<string, number>;
  stats: Record<string, number>;
  controlled_regions: string[];
  powerHistory?: number[];
}

interface Props {
  sect: SectData;
  rank?: number;
  isSelected?: boolean;
  onClick?: () => void;
}

const SECT_ICONS: Record<string, LucideIcon> = {
  sword: Swords,
  alchemy: Leaf,
  formation: Shield,
  demon: Swords,
  beast: Map,
  artifact: Shield,
  merchant: Coins,
  hidden: BarChart3,
};

const SECT_COLORS: Record<string, string> = {
  sword: '#ef4444', alchemy: '#22c55e', formation: '#3b82f6',
  demon: '#a855f7', beast: '#f97316', artifact: '#eab308',
  merchant: '#14b8a6', hidden: '#6b7280',
};

function Sparkline({ data, color, width = 80, height = 24 }: {
  data: number[];
  color: string;
  width?: number;
  height?: number;
}) {
  if (!data || data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className="shrink-0">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
   );
}

export default function RealtimeSectCard({ sect, rank, isSelected, onClick }: Props) {
  const Icon = SECT_ICONS[sect.sect_type] || BarChart3;
  const color = SECT_COLORS[sect.sect_type] || '#6b7280';

  return (
    <div onClick={onClick}
      className={`p-3 rounded-lg cursor-pointer transition-all border ${
        isSelected ? 'bg-gold-500/10 border-gold-500/30' : 'bg-ink-800/50 border-transparent hover:bg-ink-800'
      }`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {rank !== undefined && <span className="text-xs font-bold text-ink-500 w-4">{rank}</span>}
          <Icon className="w-4 h-4" style={{ color }} />
          <span className="text-sm font-medium" style={{ color }}>{sect.name}</span>
        </div>
        <span className={`text-xs px-1.5 py-0.5 rounded ${
          sect.status === 'active' ? 'bg-jade-900/50 text-jade-400' : 'bg-vermilion-900/50 text-vermilion-400'
        }`}>
          {sect.status === 'active' ? '存活' : '覆灭'}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-1 text-xs mb-2">
        <div className="text-ink-500 flex items-center gap-0.5">
          <Swords className="w-3 h-3" /> {sect.stats.military_power || 0}
        </div>
        <div className="text-ink-500 flex items-center gap-0.5">
          <Map className="w-3 h-3" /> {sect.controlled_regions.length}
        </div>
        <div className="text-ink-500 flex items-center gap-0.5">
          <Coins className="w-3 h-3" /> {sect.resources.spirit_stones || 0}
        </div>
      </div>

      {sect.powerHistory && sect.powerHistory.length > 1 && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-ink-500">趋势</span>
          <Sparkline data={sect.powerHistory} color={color} />
        </div>
      )}

      <div className="mt-1.5 h-1 bg-ink-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(100, ((sect.stats.military_power || 0) / 200) * 100)}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}
