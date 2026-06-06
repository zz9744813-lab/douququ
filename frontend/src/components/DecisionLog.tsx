import { Brain } from 'lucide-react';
import { ACTION_LABELS, ACTION_ICONS } from './ui/icons';

interface DecisionEntry {
  id: string;
  turn: number;
  sect_id: string;
  sect_name: string;
  action_type: string;
  reasoning: string;
  confidence?: number;
}

interface Props {
  decisions: DecisionEntry[];
  maxItems?: number;
}

export default function DecisionLog({ decisions, maxItems = 20 }: Props) {
  const sorted = [...decisions]
    .sort((a, b) => b.turn - a.turn)
    .slice(0, maxItems);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-3">
        <Brain className="w-4 h-4 text-ink-400" />
        <h3 className="text-sm font-bold text-ink-300">决策日志</h3>
        <span className="text-xs text-ink-500">{sorted.length} 条</span>
      </div>

      <div className="space-y-1.5">
        {sorted.map((entry) => {
          const Icon = ACTION_ICONS[entry.action_type] || Brain;
          const label = ACTION_LABELS[entry.action_type] || entry.action_type;
          return (
            <div key={entry.id}
              className="p-2.5 rounded-lg bg-ink-800/50 border border-ink-700/30 hover:bg-ink-700 transition-colors">
              <div className="flex items-start gap-2">
                <Icon className="w-4 h-4 mt-0.5 text-ink-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm text-ink-200">
                      <span className="font-medium">{entry.sect_name}</span>
                      <span className="text-ink-500 mx-1">-</span>
                      <span>{label}</span>
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      {entry.confidence !== undefined && (
                        <span className="text-xs text-ink-500">{Math.round(entry.confidence * 100)}%</span>
                      )}
                      <span className="text-xs text-ink-500">回合 {entry.turn}</span>
                    </div>
                  </div>
                  <p className="text-xs text-ink-400 mt-1 line-clamp-3">{entry.reasoning}</p>
                </div>
              </div>
            </div>
          );
        })}
        {sorted.length === 0 && (
          <div className="text-center text-ink-600 py-8 text-sm">暂无决策记录</div>
        )}
      </div>
    </div>
  );
}
