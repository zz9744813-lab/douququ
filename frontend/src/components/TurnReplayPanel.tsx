import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

interface Props {
  worldId: string;
  turn: number;
  onClose: () => void;
}

const PHASE_COLORS: Record<string, string> = {
  declaration: 'border-red-500',
  comparison: 'border-blue-500',
  battle: 'border-yellow-500',
  result: 'border-green-500',
  event: 'border-purple-500',
};

const PHASE_ICONS: Record<string, string> = {
  declaration: '⚔️',
  comparison: '📊',
  battle: '💥',
  result: '🏆',
  event: '✨',
};

export default function TurnReplayPanel({ worldId, turn, onClose }: Props) {
  const [currentPhase, setCurrentPhase] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const { data: replay, isLoading } = useQuery({
    queryKey: ['turn-replay', worldId, turn],
    queryFn: () => api.getTurnReplay(worldId, turn),
    enabled: !!worldId && turn > 0,
  });

  // Auto-play
  useEffect(() => {
    if (!isPlaying || !replay) return;
    const items = replay.timeline || [];
    if (currentPhase >= items.length) {
      setIsPlaying(false);
      return;
    }
    const timer = setTimeout(() => {
      setCurrentPhase((p) => p + 1);
    }, 1500);
    return () => clearTimeout(timer);
  }, [isPlaying, currentPhase, replay]);

  if (isLoading) {
    return <div className="p-4 text-slate-400">加载回放...</div>;
  }

  if (!replay) {
    return <div className="p-4 text-slate-500">无回放数据</div>;
  }

  const items = replay.timeline || [];

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">回合 {turn} 回放</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setIsPlaying(!isPlaying); setCurrentPhase(0); }}
            className="px-2 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs"
          >
            {isPlaying ? '⏸' : '▶'}
          </button>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-sm">✕</button>
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item: any, idx: number) => {
          const isActive = idx <= currentPhase;
          const isCurrent = idx === currentPhase && isPlaying;
          const phase = item.type === 'battle' ? (item.result_type === 'decisive_victory' ? 'battle' : 'battle') : 'event';
          const borderColor = PHASE_COLORS[phase] || 'border-slate-600';
          const icon = PHASE_ICONS[phase] || '📌';

          return (
            <div
              key={idx}
              className={`rounded-lg p-3 border-l-4 ${borderColor} transition-all duration-500 ${
                isActive ? 'bg-slate-800 opacity-100' : 'bg-slate-900 opacity-30'
              } ${isCurrent ? 'ring-1 ring-indigo-500' : ''}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm">{icon}</span>
                <span className="text-sm font-medium text-white">{item.title}</span>
                {item.type === 'battle' && (
                  <span className="text-xs text-slate-500 ml-auto">
                    {item.attacker_power} vs {item.defender_power}
                  </span>
                )}
              </div>
              <div className="text-xs text-slate-400">{item.description}</div>
              {item.type === 'battle' && item.losses && (
                <div className="flex gap-3 mt-2 text-xs">
                  <span className="text-red-400">攻方损失: {item.losses.attacker_loss}</span>
                  <span className="text-red-400">防方损失: {item.losses.defender_loss}</span>
                  {item.rewards?.spirit_stones_looted > 0 && (
                    <span className="text-green-400">掠夺: {item.rewards.spirit_stones_looted} 灵石</span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {items.length === 0 && (
        <p className="text-slate-500 text-sm">本回合无重大事件</p>
      )}
    </div>
  );
}
