import { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Swords, X } from 'lucide-react';
import type { Battle, Sect } from '../../api/client';

interface Props {
  battles: Battle[];
  sects: Sect[];
}

function getSectName(sects: Sect[], id: string): string {
  return sects.find((s) => s.id === id)?.name || id;
}

export default function BattleFlashOverlay({ battles, sects }: Props) {
  const [visible, setVisible] = useState(false);
  const [latest, setLatest] = useState<Battle | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (battles.length === 0) return;
    const last = battles[battles.length - 1];
    if (!last) return;

    setLatest(last);
    setDismissed(false);
    setVisible(true);

    const timer = setTimeout(() => {
      setVisible(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, [battles]);

  const handleDismiss = () => {
    setDismissed(true);
    setVisible(false);
  };

  if (!latest) return null;

  const resultLabels: Record<string, string> = {
    decisive_victory: '大胜',
    victory: '胜利',
    stalemate: '僵持',
    defeat: '败北',
    crushing_defeat: '惨败',
  };

  return (
    <AnimatePresence>
      {visible && !dismissed && (
        <motion.div
          key={`battle-${latest.id}`}
          initial={{ opacity: 0, y: -20, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
          className="fixed top-4 left-1/2 -translate-x-1/2 z-50"
        >
          <div className="flex items-center gap-3 px-5 py-3 rounded-lg border border-vermilion-700/50 bg-ink-900/95 backdrop-blur-sm shadow-lg shadow-vermilion-900/20">
            <Swords className="w-5 h-5 text-vermilion-400 shrink-0" />
            <div className="flex items-center gap-2 text-sm">
              <span className="text-ink-100 font-medium">
                {getSectName(sects, latest.attacker_sect_id)}
              </span>
              <span className="text-vermilion-400 font-bold text-xs">
                VS
              </span>
              <span className="text-ink-100 font-medium">
                {getSectName(sects, latest.defender_sect_id)}
              </span>
            </div>
            <span className="text-xs px-2 py-0.5 rounded bg-vermilion-900/50 text-vermilion-300 border border-vermilion-800/50">
              {resultLabels[latest.result_type] || latest.result_type}
            </span>
            <button
              onClick={handleDismiss}
              className="ml-1 text-ink-400 hover:text-ink-200 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}