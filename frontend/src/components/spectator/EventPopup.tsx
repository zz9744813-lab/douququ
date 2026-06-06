import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertTriangle } from 'lucide-react';
import { getEventIcon, getActionLabel } from '../ui/icons';
import type { WorldEvent } from '../../api/client';

interface Props {
  events: WorldEvent[];
}

export default function EventPopup({ events }: Props) {
  const [visibleEvents, setVisibleEvents] = useState<WorldEvent[]>([]);
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // 过滤高严重度事件
  useEffect(() => {
    const highSeverity = events
      .filter((e) => e.severity >= 0.7 && !dismissedIds.has(e.id))
      .slice(-5);

    // 为新出现的事件设置自动消失定时器
    highSeverity.forEach((event) => {
      if (!timersRef.current.has(event.id)) {
        const timer = setTimeout(() => {
          handleDismiss(event.id);
          timersRef.current.delete(event.id);
        }, 4000);
        timersRef.current.set(event.id, timer);
      }
    });

    setVisibleEvents(highSeverity);
  }, [events, dismissedIds]);

  // 组件卸载时清理所有定时器
  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer));
      timersRef.current.clear();
    };
  }, []);

  const handleDismiss = (id: string) => {
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
    setDismissedIds((prev) => new Set(prev).add(id));
  };

  return (
    <div className="fixed top-16 right-4 z-40 space-y-2 max-w-sm">
      <AnimatePresence mode="popLayout">
        {visibleEvents.map((event) => {
          const Icon = getEventIcon(event.event_type);
          const label = getActionLabel(event.event_type);

          return (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: 80, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 80, scale: 0.95 }}
              transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
              className="flex items-start gap-3 p-3 rounded-lg border border-gold-700/30 bg-ink-900/95 backdrop-blur-sm shadow-lg"
            >
              <AlertTriangle className="w-4 h-4 text-gold-400 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Icon className="w-3.5 h-3.5 text-gold-400" />
                  <span className="text-xs font-medium text-gold-300">
                    {label}
                  </span>
                  <span className="text-[10px] text-ink-400 ml-auto">
                    回合 {event.turn}
                  </span>
                </div>
                <div className="text-sm text-ink-100 font-medium truncate">
                  {event.title}
                </div>
                <div className="text-xs text-ink-400 mt-0.5 line-clamp-2">
                  {event.description}
                </div>
              </div>
              <button
                onClick={() => handleDismiss(event.id)}
                className="text-ink-500 hover:text-ink-300 transition-colors shrink-0"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}