import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWorldStore } from '../api/worldStore';
import StrategicWorldMap from '../components/StrategicWorldMap';

const SECT_COLORS: Record<string, string> = {
  sword: '#ef4444', alchemy: '#22c55e', formation: '#3b82f6',
  demon: '#a855f7', beast: '#f97316', artifact: '#eab308',
  merchant: '#14b8a6', hidden: '#6b7280',
};

export default function WorldSpectatorPage() {
  const { worldId } = useParams<{ worldId: string }>();
  const navigate = useNavigate();
  const store = useWorldStore();
  const [selectedSectId, setSelectedSectId] = useState<string | null>(null);
  const [liveMode, setLiveMode] = useState(true);
  const eventLogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (worldId) store.loadWorld(worldId);
    return () => { store.clear(); };
  }, [worldId]);

  // Auto-scroll event log
  useEffect(() => {
    if (eventLogRef.current && liveMode) {
      eventLogRef.current.scrollTop = eventLogRef.current.scrollHeight;
    }
  }, [store.events, store.battles, liveMode]);

  const world = store.currentWorld;
  if (!world) return null;

  const selectedSect = store.sects.find(s => s.id === selectedSectId);
  const activeSects = store.sects.filter(s => s.status === 'active');
  const annexedSects = store.sects.filter(s => s.status === 'annexed');

  // 合并事件和战斗为统一格式
  const timelineItems = [
    ...store.events.map(e => ({
      _type: 'event' as const,
      turn: e.turn,
      title: e.title,
      description: e.description,
      severity: e.severity,
      event_type: e.event_type,
    })),
    ...store.battles.map(b => ({
      _type: 'battle' as const,
      turn: b.turn,
      title: `战争: ${b.battle_log?.slice(0, 40) || '战斗'}`,
      description: b.battle_log || '',
      severity: b.result_type === 'decisive_victory' ? 1.0 : b.result_type === 'crushing_defeat' ? 0.9 : 0.7,
      event_type: 'war',
      result_type: b.result_type,
    })),
  ].sort((a, b) => b.turn - a.turn);

  return (
    <div className="h-screen flex flex-col bg-black text-white overflow-hidden">
      {/* Top Bar - 赛事信息 */}
      <header className="h-14 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-amber-500/30 flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/')} className="text-slate-400 hover:text-white text-lg">←</button>
          <div>
            <h1 className="text-lg font-bold text-amber-100">{world.name}</h1>
            <div className="text-xs text-slate-400">第 {world.current_turn} 回合 {world.max_turns ? `/ ${world.max_turns}` : ''}</div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {/* 存活统计 */}
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-green-400">{activeSects.length} 存活</span>
            </div>
            {annexedSects.length > 0 && (
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-red-400">{annexedSects.length} 覆灭</span>
              </div>
            )}
          </div>

          {/* 控制按钮 */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setLiveMode(!liveMode)}
              className={`px-3 py-1.5 rounded text-xs font-medium ${liveMode ? 'bg-red-600/30 text-red-300 border border-red-500/50' : 'bg-slate-700 text-slate-400'}`}
            >
              {liveMode ? '🔴 直播中' : '⏸ 暂停'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Stage - 大屏布局 */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - 宗门势力榜 */}
        <aside className="w-72 bg-slate-900/80 border-r border-slate-700/50 flex flex-col shrink-0">
          <div className="p-3 border-b border-slate-700/50">
            <h3 className="text-sm font-bold text-amber-200">🏆 势力榜</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {store.sects
              .sort((a, b) => (b.stats.military_power || 0) - (a.stats.military_power || 0))
              .map((sect, idx) => (
              <div
                key={sect.id}
                onClick={() => setSelectedSectId(sect.id === selectedSectId ? null : sect.id)}
                className={`p-2.5 rounded-lg cursor-pointer transition-all ${
                  selectedSectId === sect.id
                    ? 'bg-amber-500/10 border border-amber-500/30'
                    : 'bg-slate-800/50 border border-transparent hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-500 w-4">{idx + 1}</span>
                    <span className="text-sm font-medium" style={{ color: SECT_COLORS[sect.sect_type] }}>
                      {sect.name}
                    </span>
                  </div>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    sect.status === 'active' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'
                  }`}>
                    {sect.status === 'active' ? '存活' : '覆灭'}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-1 text-xs">
                  <div className="text-slate-500">⚔️ {sect.stats.military_power || 0}</div>
                  <div className="text-slate-500">🏛️ {sect.controlled_regions.length}</div>
                  <div className="text-slate-500">💰 {sect.resources.spirit_stones || 0}</div>
                </div>
                {/* 势力条 */}
                <div className="mt-1.5 h-1 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(100, ((sect.stats.military_power || 0) / 200) * 100)}%`,
                      backgroundColor: SECT_COLORS[sect.sect_type],
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Center - 战略地图舞台 */}
        <main className="flex-1 relative">
          <StrategicWorldMap
            regions={store.mapData?.nodes?.map((n: Record<string, unknown>) => ({
              id: String(n.id),
              world_id: worldId || '',
              name: String(n.name),
              region_type: String(n.region_type),
              owner_sect_id: n.owner_sect_id as string | null,
              resource_level: Number(n.resource_level) || 0,
              defense_level: Number(n.defense_level) || 0,
              stability: 0.5,
              neighbors: (n.neighbors as string[]) || [],
              special_flags: [],
            })) || []}
            sects={store.sects}
            selectedSectId={selectedSectId}
            onSelectSect={setSelectedSectId}
            battles={store.battles.map(b => ({
              attacker_sect_id: b.attacker_sect_id,
              defender_sect_id: b.defender_sect_id,
              turn: b.turn,
              result_type: b.result_type,
            }))}
          />

          {/* 底部信息条 */}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
            {selectedSect && (
              <div className="flex items-center gap-6 text-sm">
                <span className="font-bold" style={{ color: SECT_COLORS[selectedSect.sect_type] }}>
                  {selectedSect.name}
                </span>
                <span className="text-slate-400">掌门: {selectedSect.leader_name || '未知'}</span>
                <span className="text-slate-400">区域: {selectedSect.controlled_regions.length}</span>
                <span className="text-slate-400">战力: {selectedSect.stats.military_power || 0}</span>
                <span className="text-slate-400">稳定: {Math.round((selectedSect.stats.stability || 0) * 100)}%</span>
              </div>
            )}
          </div>
        </main>

        {/* Right Panel - 事件流 / 解说 */}
        <aside className="w-80 bg-slate-900/80 border-l border-slate-700/50 flex flex-col shrink-0">
          <div className="p-3 border-b border-slate-700/50 flex items-center justify-between">
            <h3 className="text-sm font-bold text-amber-200">📜 天道记录</h3>
            <span className="text-xs text-slate-500">{timelineItems.length} 事件</span>
          </div>
          <div ref={eventLogRef} className="flex-1 overflow-y-auto p-2 space-y-2">
            {timelineItems.slice(0, 50).map((item, idx) => (
              <div key={`${item._type}-${idx}`} className="p-2.5 rounded bg-slate-800/50 border border-slate-700/30">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-slate-500">回合 {item.turn}</span>
                  {item._type === 'battle' ? (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-red-900/50 text-red-400">⚔️ 战争</span>
                  ) : (
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      (item.severity || 0) > 0.8 ? 'bg-red-900/50 text-red-400' :
                      (item.severity || 0) > 0.5 ? 'bg-amber-900/50 text-amber-400' :
                      'bg-blue-900/50 text-blue-400'
                    }`}>
                      {item.event_type}
                    </span>
                  )}
                </div>
                <div className="text-sm text-slate-200">{item.title}</div>
                {item._type === 'battle' && 'result_type' in item && (
                  <div className="mt-1 text-xs text-slate-500">
                    结果: {item.result_type === 'decisive_victory' ? '大胜' : item.result_type === 'victory' ? '小胜' : item.result_type === 'stalemate' ? '僵持' : '战败'}
                  </div>
                )}
              </div>
            ))}
            {timelineItems.length === 0 && (
              <div className="text-center text-slate-600 py-8">暂无事件</div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
