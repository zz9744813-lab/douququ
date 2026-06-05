import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWorldStore } from '../api/worldStore';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import type { Sect, Region } from '../api/client';
import WorldMap from '../components/WorldMap';
import EventFeed from '../components/EventFeed';
import SectCard from '../components/SectCard';

const SECT_COLORS: Record<string, string> = {
  sword: '#ef4444', alchemy: '#22c55e', formation: '#3b82f6',
  demon: '#a855f7', beast: '#f97316', artifact: '#eab308',
  merchant: '#14b8a6', hidden: '#6b7280',
};

export default function WorldRunPage() {
  const { worldId } = useParams<{ worldId: string }>();
  const navigate = useNavigate();
  const store = useWorldStore();
  const [selectedSect, setSelectedSect] = useState<Sect | null>(null);
  const [turnCount, setTurnCount] = useState(1);

  useEffect(() => {
    if (worldId) store.loadWorld(worldId);
    return () => { store.clear(); };
  }, [worldId]);

  const { data: regions } = useQuery({
    queryKey: ['regions', worldId],
    queryFn: () => api.getRegions(worldId!),
    enabled: !!worldId,
  });

  const handleNextTurn = useCallback(async () => {
    if (!worldId) return;
    await store.advanceTurn(worldId);
  }, [worldId, store]);

  const handleAutoRun = useCallback(async () => {
    if (!worldId) return;
    await store.autoRun(worldId, turnCount);
  }, [worldId, store, turnCount]);

  if (store.loading && !store.currentWorld) {
    return <div className="flex items-center justify-center h-screen text-slate-400">加载中...</div>;
  }

  if (store.error && !store.currentWorld) {
    return (
      <div className="flex items-center justify-center h-screen text-red-400">
        <div>
          <p>加载失败: {store.error}</p>
          <button onClick={() => navigate('/')} className="mt-4 text-indigo-400">返回首页</button>
        </div>
      </div>
    );
  }

  const world = store.currentWorld;
  if (!world) return null;

  const regionMap = new Map<string, Region>();
  if (regions) regions.forEach(r => regionMap.set(r.id, r));

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/')} className="text-slate-400 hover:text-white">←</button>
          <h1 className="text-lg font-bold text-white">{world.name}</h1>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
            world.status === 'running' ? 'bg-green-500/20 text-green-400' :
            world.status === 'finished' ? 'bg-blue-500/20 text-blue-400' :
            world.status === 'paused' ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-gray-500/20 text-gray-400'
          }`}>
            {world.status === 'running' ? '运行中' : world.status === 'finished' ? '已结束' : world.status === 'paused' ? '已暂停' : '未开始'}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-slate-400 text-sm">回合 {world.current_turn}{world.max_turns ? `/${world.max_turns}` : ''}</span>
          {(world.status === 'running' || world.status === 'created') && (
            <>
              <input
                type="number"
                value={turnCount}
                onChange={(e) => setTurnCount(Math.max(1, Math.min(50, Number(e.target.value))))}
                className="w-16 bg-slate-700 border border-slate-600 rounded px-2 py-1 text-white text-sm text-center"
                min={1} max={50}
              />
              <button
                onClick={handleAutoRun}
                disabled={store.loading}
                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded text-sm font-medium"
              >
                {store.loading ? '...' : `自动 ×${turnCount}`}
              </button>
              <button
                onClick={handleNextTurn}
                disabled={store.loading}
                className="px-3 py-1 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white rounded text-sm"
              >
                下一回合
              </button>
            </>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Sect List */}
        <aside className="w-64 bg-slate-850 border-r border-slate-700 overflow-y-auto shrink-0">
          <div className="p-3 border-b border-slate-700 text-sm font-medium text-slate-300">宗门列表</div>
          {store.sects.map((sect) => (
            <SectCard
              key={sect.id}
              sect={sect}
              regions={regions || []}
              isSelected={selectedSect?.id === sect.id}
              onClick={() => setSelectedSect(sect)}
            />
          ))}
        </aside>

        {/* Center: Map */}
        <main className="flex-1 relative overflow-hidden">
          <WorldMap
            mapData={store.mapData}
            regions={regions || []}
            sects={store.sects}
            selectedSectId={selectedSect?.id}
            onSelectSect={(id) => {
              const s = store.sects.find((x) => x.id === id);
              if (s) setSelectedSect(s);
            }}
          />
        </main>

        {/* Right: Detail Panel */}
        <aside className="w-80 bg-slate-850 border-l border-slate-700 overflow-y-auto shrink-0">
          {selectedSect ? (
            <div className="p-4">
              <h3 className="text-lg font-bold text-white mb-3">{selectedSect.name}</h3>
              <div className="flex items-center gap-2 mb-4">
                <span className="px-2 py-0.5 rounded text-xs" style={{ backgroundColor: SECT_COLORS[selectedSect.sect_type] + '30', color: SECT_COLORS[selectedSect.sect_type] }}>
                  {selectedSect.sect_type}
                </span>
                <span className={`px-2 py-0.5 rounded text-xs ${selectedSect.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                  {selectedSect.status === 'active' ? '活跃' : selectedSect.status}
                </span>
              </div>

              {/* Stats */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-slate-400 mb-2">宗门属性</h4>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(selectedSect.stats).slice(0, 8).map(([key, value]) => (
                    <div key={key} className="bg-slate-800 rounded p-2">
                      <div className="text-xs text-slate-500">{key}</div>
                      <div className="text-sm font-medium text-white">{value}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Resources */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-slate-400 mb-2">资源</h4>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(selectedSect.resources).map(([key, value]) => (
                    <div key={key} className="bg-slate-800 rounded p-2">
                      <div className="text-xs text-slate-500">{key}</div>
                      <div className="text-sm font-medium text-white">{value}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Personality */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-slate-400 mb-2">性格</h4>
                <div className="space-y-1.5">
                  {Object.entries(selectedSect.personality).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">{key}</span>
                      <div className="w-24 bg-slate-700 rounded-full h-1.5">
                        <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${value * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Strategy */}
              {selectedSect.strategy_summary && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-slate-400 mb-1">战略</h4>
                  <p className="text-sm text-slate-300">{selectedSect.strategy_summary}</p>
                </div>
              )}

              {/* Controlled Regions */}
              <div>
                <h4 className="text-sm font-medium text-slate-400 mb-1">
                  控制区域 ({selectedSect.controlled_regions.length})
                </h4>
                <div className="space-y-1">
                  {selectedSect.controlled_regions.map((rid) => {
                    const r = regionMap.get(rid);
                    return (
                      <div key={rid} className="text-xs text-slate-400 bg-slate-800 rounded px-2 py-1">
                        {r?.name || rid} ({r?.region_type || '?'})
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4">
              <h3 className="text-lg font-bold text-white mb-3">事件流</h3>
              <EventFeed events={store.events} battles={store.battles} sects={store.sects} />
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}