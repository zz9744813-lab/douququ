import { Timer } from './ui/icons';

interface Props {
  currentTurn: number;
  maxTurns?: number | null;
  isRunning?: boolean;
}

export default function WorldClock({ currentTurn, maxTurns, isRunning }: Props) {
  const progress = maxTurns ? (currentTurn / maxTurns) * 100 : 0;

  return (
    <div className="flex items-center gap-2 text-sm">
      <Timer className="w-4 h-4 text-ink-400" />
      <span className="text-ink-200 font-medium">{currentTurn}</span>
      {maxTurns && (
        <>
          <span className="text-ink-500">/</span>
          <span className="text-ink-500">{maxTurns}</span>
        </>
      )}
      {isRunning && <span className="w-1.5 h-1.5 rounded-full bg-jade-500 animate-pulse" />}
      {maxTurns && (
        <div className="w-16 h-1 bg-ink-700 rounded-full overflow-hidden ml-1">
          <div className="h-full bg-ink-400 rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
        </div>
      )}
    </div>
  );
}
