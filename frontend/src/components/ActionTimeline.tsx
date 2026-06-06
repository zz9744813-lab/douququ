import { ClipboardList } from 'lucide-react';
import { ACTION_LABELS, ACTION_ICONS } from './ui/icons';

interface TimelineAction {
  id: string;
  turn: number;
  sect_id: string;
  sect_name: string;
  action_type: string;
  target?: string;
  result?: string;
  description?: string;
}

interface Props {
  actions: TimelineAction[];
  maxItems?: number;
}

export default function ActionTimeline({ actions, maxItems = 30 }: Props) {
  const sorted = [...actions]
    .sort((a, b) => b.turn - a.turn)
    .slice(0, maxItems);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-3">
        <ClipboardList className="w-4 h-4 text-ink-400" />
        <h3 className="text-sm font-bold text-ink-300">行动时间线</h3>
        <span className="text-xs text-ink-500">{sorted.length} 条</span>
      </div>

      <div className="space-y-1.5">
        {sorted.map((action) => {
          const Icon = ACTION_ICONS[action.action_type] || ClipboardList;
          const label = ACTION_LABELS[action.action_type] || action.action_type;
          return (
            <div key={action.id}
              className="p-2.5 rounded-lg bg-ink-800/50 border border-ink-700/30 hover:bg-ink-700 transition-colors">
              <div className="flex items-start gap-2">
                <Icon className="w-4 h-4 mt-0.5 text-ink-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm text-ink-200">
                      <span className="font-medium">{action.sect_name}</span>
                      <span className="text-ink-500 mx-1">-</span>
                      <span>{label}</span>
                    </span>
                    <span className="text-xs text-ink-500 shrink-0">回合 {action.turn}</span>
                  </div>
                  {action.target && <p className="text-xs text-ink-400 mt-0.5">目标: {action.target}</p>}
                  {action.description && <p className="text-xs text-ink-500 mt-0.5 line-clamp-2">{action.description}</p>}
                </div>
              </div>
            </div>
          );
        })}
        {sorted.length === 0 && (
          <div className="text-center text-ink-600 py-8 text-sm">暂无行动记录</div>
        )}
      </div>
    </div>
  );
}
