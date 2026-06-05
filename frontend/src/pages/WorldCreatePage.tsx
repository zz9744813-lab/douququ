import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

export default function WorldCreatePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [mode, setMode] = useState('sandbox');
  const [maxTurns, setMaxTurns] = useState(100);
  const [sectCount, setSectCount] = useState(8);
  const [mapSize, setMapSize] = useState('medium');
  const [seed, setSeed] = useState(() => Math.floor(Math.random() * 100000));

  const mutation = useMutation({
    mutationFn: api.createWorld,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['worlds'] });
      navigate(`/worlds/${data.id}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    mutation.mutate({
      name: name.trim(),
      mode,
      max_turns: mode === 'sandbox' ? undefined : maxTurns,
      sect_count: sectCount,
      map_size: mapSize,
      world_seed: seed,
    });
  };

  return (
    <div className="max-w-lg mx-auto p-6">
      <button onClick={() => navigate('/')} className="text-slate-400 hover:text-white mb-6 block">
        ← 返回
      </button>
      <h1 className="text-2xl font-bold text-white mb-6">创建新世界</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm text-slate-400 mb-1">世界名称</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-indigo-500 focus:outline-none"
            placeholder="例如：百宗乱战"
            required
          />
        </div>

        <div>
          <label className="block text-sm text-slate-400 mb-1">游戏模式</label>
          <div className="grid grid-cols-2 gap-3">
            {[
              { value: 'sandbox', label: '无限沙盒', desc: '无回合限制' },
              { value: 'season', label: '赛季争霸', desc: '固定回合数' },
              { value: 'scenario', label: '剧本模式', desc: '预设开局' },
              { value: 'model_battle', label: '模型斗蛐蛐', desc: '不同模型对战' },
            ].map((m) => (
              <button
                key={m.value}
                type="button"
                onClick={() => setMode(m.value)}
                className={`p-3 rounded-lg border text-left transition-colors ${
                  mode === m.value
                    ? 'border-indigo-500 bg-indigo-500/10 text-white'
                    : 'border-slate-700 bg-slate-800 text-slate-400 hover:border-slate-600'
                }`}
              >
                <div className="font-medium">{m.label}</div>
                <div className="text-xs opacity-70">{m.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">宗门数量</label>
            <input
              type="number"
              value={sectCount}
              onChange={(e) => setSectCount(Number(e.target.value))}
              min={2} max={12}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">地图大小</label>
            <select
              value={mapSize}
              onChange={(e) => setMapSize(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-indigo-500 focus:outline-none"
            >
              <option value="small">小 (12区域)</option>
              <option value="medium">中 (20区域)</option>
              <option value="large">大 (30区域)</option>
            </select>
          </div>
        </div>

        {mode !== 'sandbox' && (
          <div>
            <label className="block text-sm text-slate-400 mb-1">最大回合数</label>
            <input
              type="number"
              value={maxTurns}
              onChange={(e) => setMaxTurns(Number(e.target.value))}
              min={10} max={500}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-indigo-500 focus:outline-none"
            />
          </div>
        )}

        <div>
          <label className="block text-sm text-slate-400 mb-1">世界种子</label>
          <div className="flex gap-2">
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-indigo-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => setSeed(Math.floor(Math.random() * 100000))}
              className="px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg"
            >
              🎲
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={mutation.isPending || !name.trim()}
          className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg font-medium transition-colors"
        >
          {mutation.isPending ? '创建中...' : '🏯 创建世界'}
        </button>
        {mutation.error && <p className="text-red-400 text-sm">创建失败: {String(mutation.error)}</p>}
      </form>
    </div>
  );
}