import type { Sect, Region } from '../api/client';

const SECT_COLORS: Record<string, string> = {
  sword: '#ef4444', alchemy: '#22c55e', formation: '#3b82f6',
  demon: '#a855f7', beast: '#f97316', artifact: '#eab308',
  merchant: '#14b8a6', hidden: '#6b7280',
};

interface Props {
  sect: Sect;
  regions: Region[];
  isSelected: boolean;
  onClick: () => void;
}

export default function SectCard({ sect, regions, isSelected, onClick }: Props) {
  const color = SECT_COLORS[sect.sect_type] || '#888';
  const regionCount = sect.controlled_regions.length;
  const military = sect.stats.military_power || 0;
  const stones = sect.resources.spirit_stones || 0;

  return (
    <div
      onClick={onClick}
      className={`p-3 border-b border-slate-700 cursor-pointer transition-colors ${
        isSelected ? 'bg-slate-700' : 'hover:bg-slate-800'
      } ${sect.status !== 'active' ? 'opacity-50' : ''}`}
    >
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
          <span className="text-sm font-medium text-white">{sect.name}</span>
        </div>
        <span className="text-xs text-slate-500">#{regionCount}</span>
      </div>
      <div className="flex items-center gap-3 text-xs text-slate-400">
        <span>⚔ {military}</span>
        <span>💎 {stones}</span>
      </div>
      <div className="mt-1">
        <div className="w-full bg-slate-700 rounded-full h-1">
          <div
            className="h-1 rounded-full transition-all"
            style={{
              width: `${Math.min(100, (military / 200) * 100)}%`,
              backgroundColor: color,
            }}
          />
        </div>
      </div>
    </div>
  );
}