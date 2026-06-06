import { useMemo } from 'react';
import {
  Swords, Handshake, Skull, Radio,
  Coins, Zap, AlertTriangle, Info,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface LiveEvent {
  id: string;
  type: string;
  turn: number;
  title: string;
  description: string;
  severity?: number;
  timestamp: string;
}

interface Props {
  events: LiveEvent[];
  maxItems?: number;
}

const EVENT_ICON_MAP: Record<string, LucideIcon> = {
  war: Swords,
  battle: Swords,
  alliance: Handshake,
  trade: Coins,
  elimination: Skull,
  annexation: Skull,
  disaster: AlertTriangle,
  discovery: Info,
  rebellion: Zap,
  default: Info,
};

function getEventIcon(type: string): LucideIcon {
  return EVENT_ICON_MAP[type] || EVENT_ICON_MAP.default;
}

export default function LiveEventFeed({ events, maxItems = 50 }: Props) {
  const sortedEvents = useMemo(() => {
    return [...events]
      .sort((a, b) => b.turn - a.turn || new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, maxItems);
  }, [events, maxItems]);

  const getSeverityColor = (severity?: number) => {
    if (!severity) return 'border-ink-700/30';
    if (severity > 0.8) return 'border-vermilion-500/50';
    if (severity > 0.5) return 'border-gold-500/50';
    return 'border-ink-700/30';
  };

  const getSeverityBg = (severity?: number) => {
    if (!severity) return 'bg-ink-800/50';
    if (severity > 0.8) return 'bg-vermilion-900/20';
    if (severity > 0.5) return 'bg-gold-900/20';
    return 'bg-ink-800/50';
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-3">
        <Radio className="w-4 h-4 text-ink-400" />
        <h3 className="text-sm font-bold text-ink-300">实时事件</h3>
        <span className="text-xs text-ink-500">{sortedEvents.length} 条</span>
      </div>

      <div className="space-y-1.5">
        {sortedEvents.map((event) => {
          const Icon = getEventIcon(event.type);
          return (
            <div key={event.id}
              className={`p-2.5 rounded-lg border ${getSeverityColor(event.severity)} ${getSeverityBg(event.severity)} hover:bg-ink-700 transition-colors cursor-pointer`}>
              <div className="flex items-start gap-2">
                <Icon className="w-4 h-4 mt-0.5 text-ink-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm text-ink-200 font-medium truncate">{event.title}</span>
                    <span className="text-xs text-ink-500 shrink-0">回合 {event.turn}</span>
                  </div>
                  {event.description && (
                    <p className="text-xs text-ink-400 mt-0.5 line-clamp-2">{event.description}</p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        {sortedEvents.length === 0 && (
          <div className="text-center text-ink-600 py-8 text-sm">暂无事件</div>
        )}
      </div>
    </div>
  );
}
