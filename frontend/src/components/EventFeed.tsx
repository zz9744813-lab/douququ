import type { WorldEvent, Battle, Sect } from '../api/client';

interface Props {
  events: WorldEvent[];
  battles: Battle[];
  sects: Sect[];
  onSelectTurn?: (turn: number) => void;
}

function getSectName(sects: Sect[], id: string): string {
  return sects.find((s) => s.id === id)?.name || id;
}

export default function EventFeed({ events, battles, sects, onSelectTurn }: Props) {
  // Combine and sort events and battles
  const timeline: Array<{
    turn: number;
    type: 'event' | 'battle';
    data: WorldEvent | Battle;
  }> = [];

  events.forEach((e) => timeline.push({ turn: e.turn, type: 'event', data: e }));
  battles.forEach((b) => {
    timeline.push({ turn: b.turn, type: 'battle', data: b });
  });

  timeline.sort((a, b) => b.turn - a.turn);

  return (
    <div className="space-y-2">
      {timeline.slice(0, 50).map((item, idx) => {
        if (item.type === 'event') {
          const evt = item.data as WorldEvent;
          return (
            <div
              key={`evt-${idx}`}
              className="bg-slate-800 rounded-lg p-3 border border-slate-700 cursor-pointer hover:border-slate-500 transition-colors"
              onClick={() => onSelectTurn?.(evt.turn)}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-500">回合 {evt.turn}</span>
                <span className="text-xs px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-400">
                  {evt.event_type}
                </span>
              </div>
              <div className="text-sm font-medium text-white">{evt.title}</div>
              <div className="text-xs text-slate-400 mt-1">{evt.description}</div>
            </div>
          );
        } else {
          const battle = item.data as Battle;
          const resultColors: Record<string, string> = {
            decisive_victory: 'text-green-400',
            victory: 'text-emerald-400',
            stalemate: 'text-yellow-400',
            defeat: 'text-orange-400',
            crushing_defeat: 'text-red-400',
          };
          return (
            <div
              key={`btl-${idx}`}
              className="bg-slate-800 rounded-lg p-3 border border-slate-700 cursor-pointer hover:border-slate-500 transition-colors"
              onClick={() => onSelectTurn?.(battle.turn)}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-500">回合 {battle.turn}</span>
                <span className={`text-xs font-medium ${resultColors[battle.result_type] || 'text-slate-400'}`}>
                  {battle.result_type}
                </span>
              </div>
              <div className="text-xs text-slate-300">{battle.battle_log}</div>
              <div className="flex gap-4 mt-1 text-xs text-slate-500">
                <span>攻: {getSectName(sects, battle.attacker_sect_id)} ({battle.attacker_power})</span>
                <span>防: {getSectName(sects, battle.defender_sect_id)} ({battle.defender_power})</span>
              </div>
            </div>
          );
        }
      })}
      {timeline.length === 0 && (
        <p className="text-slate-500 text-sm">暂无事件</p>
      )}
    </div>
  );
}
