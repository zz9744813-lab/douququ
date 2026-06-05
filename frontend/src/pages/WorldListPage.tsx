import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { World } from '../api/client';

export default function WorldListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: worlds, isLoading, error } = useQuery({
    queryKey: ['worlds'],
    queryFn: api.listWorlds,
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteWorld,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['worlds'] }),
  });

  const statusLabel = (s: string) => {
    const map: Record<string, string> = { created: '未开始', running: '运行中', paused: '已暂停', finished: '已结束' };
    return map[s] || s;
  };
  const statusColor = (s: string) => {
    const map: Record<string, string> = {
      created: 'bg-gray-500', running: 'bg-green-500', paused: 'bg-yellow-500', finished: 'bg-blue-500',
    };
    return map[s] || 'bg-gray-500';
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">🏯 AI 宗门争霸</h1>
          <p className="text-slate-400 mt-1">电子蛐蛐式大模型 Agent 沙盒游戏</p>
        </div>
        <button
          onClick={() => navigate('/create')}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-colors"
        >
          创建新世界
        </button>
      </div>

      {isLoading && <p className="text-slate-400">加载中...</p>}
      {error && <p className="text-red-400">加载失败: {String(error)}</p>}

      <div className="grid gap-4">
        {worlds?.map((w: World) => (
          <div
            key={w.id}
            className="bg-slate-800 rounded-xl p-5 border border-slate-700 hover:border-slate-600 transition-colors cursor-pointer"
            onClick={() => navigate(`/worlds/${w.id}`)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className={`w-2.5 h-2.5 rounded-full ${statusColor(w.status)}`} />
                <h3 className="text-lg font-semibold text-white">{w.name}</h3>
                <span className="text-sm text-slate-400 px-2 py-0.5 bg-slate-700 rounded">
                  {w.mode === 'sandbox' ? '无限沙盒' : w.mode === 'season' ? '赛季争霸' : '模型斗蛐蛐'}
                </span>
              </div>
              <div className="flex items-center gap-4 text-sm text-slate-400">
                <span>回合 {w.current_turn}{w.max_turns ? `/${w.max_turns}` : ''}</span>
                <span>{w.sect_count} 宗门</span>
                <span>{statusLabel(w.status)}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(w.id); }}
                  className="text-red-400 hover:text-red-300 text-xs"
                >
                  删除
                </button>
              </div>
            </div>
            {w.description && <p className="text-slate-500 mt-2 text-sm">{w.description}</p>}
          </div>
        ))}
        {worlds?.length === 0 && !isLoading && (
          <div className="text-center py-16 text-slate-500">
            <p className="text-4xl mb-4">🌍</p>
            <p>还没有世界，点击上方按钮创建一个吧</p>
          </div>
        )}
      </div>
    </div>
  );
}