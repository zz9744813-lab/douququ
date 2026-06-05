import { useState, useEffect, useCallback } from 'react';

interface ReplayPhase {
  phase: string;
  title: string;
  description: string;
  effects?: Record<string, unknown>;
  duration?: number;
  visual_hint?: {
    camera?: string;
    effect?: string;
    shake?: boolean;
  };
  character_event?: {
    title: string;
    description: string;
    character_name: string;
  };
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  replay: ReplayPhase[];
  attackerName: string;
  defenderName: string;
  regionName?: string;
}

const PHASE_COLORS: Record<string, string> = {
  preparation: '#3b82f6',
  march: '#6366f1',
  skirmish: '#f59e0b',
  main_battle: '#ef4444',
  climax: '#a855f7',
  result: '#22c55e',
};

const PHASE_ICONS: Record<string, string> = {
  preparation: '📢',
  march: '🏃',
  skirmish: '⚡',
  main_battle: '⚔️',
  climax: '🔥',
  result: '🏆',
};

export default function BattleReplayModal({
  isOpen,
  onClose,
  replay,
  attackerName,
  defenderName,
  regionName,
}: Props) {
  const [currentPhase, setCurrentPhase] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showComplete, setShowComplete] = useState(false);

  const totalPhases = replay.length;
  const phase = replay[currentPhase];

  const nextPhase = useCallback(() => {
    if (currentPhase < totalPhases - 1) {
      setCurrentPhase(p => p + 1);
    } else {
      setIsPlaying(false);
      setShowComplete(true);
    }
  }, [currentPhase, totalPhases]);

  // Auto-play
  useEffect(() => {
    if (!isPlaying || !isOpen) return;
    const timer = setTimeout(nextPhase, (phase?.duration || 2) * 1000);
    return () => clearTimeout(timer);
  }, [isPlaying, currentPhase, phase, isOpen, nextPhase]);

  // Reset when opened
  useEffect(() => {
    if (isOpen) {
      setCurrentPhase(0);
      setIsPlaying(false);
      setShowComplete(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="w-full max-w-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-700 rounded-xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">⚔️ 战斗回放</h2>
            <p className="text-sm text-slate-400">
              {attackerName} vs {defenderName} {regionName ? `@ ${regionName}` : ''}
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl">✕</button>
        </div>

        {/* Progress Bar */}
        <div className="h-1 bg-slate-800">
          <div
            className="h-full transition-all duration-500"
            style={{
              width: `${((currentPhase + 1) / totalPhases) * 100}%`,
              backgroundColor: phase ? PHASE_COLORS[phase.phase] || '#6366f1' : '#6366f1',
            }}
          />
        </div>

        {/* Phase Display */}
        <div className="p-6 min-h-[280px] flex flex-col items-center justify-center text-center">
          {phase && (
            <>
              {/* Phase Icon */}
              <div
                className="text-5xl mb-4 animate-bounce"
                style={{ animationDuration: '2s' }}
              >
                {PHASE_ICONS[phase.phase] || '⚔️'}
              </div>

              {/* Phase Title */}
              <h3
                className="text-2xl font-bold mb-3"
                style={{ color: PHASE_COLORS[phase.phase] || '#fff' }}
              >
                {phase.title}
              </h3>

              {/* Phase Description */}
              <p className="text-slate-300 text-lg leading-relaxed max-w-lg">
                {phase.description}
              </p>

              {/* Character Event */}
              {phase.character_event && (
                <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg max-w-md">
                  <div className="text-sm font-medium text-amber-300 mb-1">
                    👤 {phase.character_event.character_name}
                  </div>
                  <div className="text-sm text-amber-200">
                    {phase.character_event.description}
                  </div>
                </div>
              )}

              {/* Effects */}
              {phase.effects && Object.keys(phase.effects).length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2 justify-center">
                  {Object.entries(phase.effects).map(([key, value]) => (
                    <span key={key} className="text-xs px-2 py-1 bg-slate-800 rounded text-slate-400">
                      {key}: {String(value)}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Complete */}
          {showComplete && (
            <div className="text-center">
              <div className="text-6xl mb-4">🎬</div>
              <h3 className="text-xl font-bold text-white mb-2">回放结束</h3>
              <p className="text-slate-400">战斗已完整呈现</p>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="px-6 py-4 border-t border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {replay.map((_, i) => (
              <button
                key={i}
                onClick={() => { setCurrentPhase(i); setShowComplete(false); }}
                className={`w-2 h-2 rounded-full transition-all ${
                  i === currentPhase ? 'bg-white w-4' : i < currentPhase ? 'bg-slate-500' : 'bg-slate-700'
                }`}
              />
            ))}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setCurrentPhase(Math.max(0, currentPhase - 1))}
              disabled={currentPhase === 0}
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-30 rounded text-sm"
            >
              ⏮ 上一阶段
            </button>
            <button
              onClick={() => { setIsPlaying(!isPlaying); setShowComplete(false); }}
              className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded text-sm font-medium"
            >
              {isPlaying ? '⏸ 暂停' : showComplete ? '▶ 重播' : '▶ 播放'}
            </button>
            <button
              onClick={() => { setCurrentPhase(Math.min(totalPhases - 1, currentPhase + 1)); setShowComplete(false); }}
              disabled={currentPhase >= totalPhases - 1}
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-30 rounded text-sm"
            >
              下一阶段 ⏭
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
