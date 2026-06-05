import { useState, useEffect, useCallback } from 'react';

interface Provider {
  id: string;
  name: string;
  provider_type: string;
  base_url: string;
  api_key_masked: string;
  enabled: boolean;
  priority: number;
  timeout_seconds: number;
  max_retries: number;
}

interface LLMModel {
  id: string;
  provider_id: string;
  model_name: string;
  display_name: string;
  enabled: boolean;
  role_tags: string[];
}

const API_BASE = '/api/settings';

export default function ModelConfigPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<LLMModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Form states
  const [showAddProvider, setShowAddProvider] = useState(false);
  const [newProvider, setNewProvider] = useState({
    name: '',
    base_url: '',
    api_key: '',
  });
  const [testingProvider, setTestingProvider] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [pRes, mRes] = await Promise.all([
        fetch(`${API_BASE}/providers`),
        fetch(`${API_BASE}/models`),
      ]);
      const pData = await pRes.json();
      const mData = await mRes.json();
      setProviders(Array.isArray(pData) ? pData : []);
      setModels(Array.isArray(mData) ? mData : []);
    } catch (e) {
      setMessage('加载失败: ' + (e as Error).message);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const addProvider = async () => {
    if (!newProvider.name || !newProvider.base_url || !newProvider.api_key) {
      setMessage('请填写完整信息');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/providers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProvider),
      });
      const data = await res.json();
      if (res.ok) {
        setMessage('Provider 添加成功！');
        setShowAddProvider(false);
        setNewProvider({ name: '', base_url: '', api_key: '' });
        fetchData();
      } else {
        setMessage('添加失败: ' + (data.detail || '未知错误'));
      }
    } catch (e) {
      setMessage('添加失败: ' + (e as Error).message);
    }
    setLoading(false);
  };

  const deleteProvider = async (id: string) => {
    if (!confirm('确定删除此 Provider？')) return;
    setLoading(true);
    try {
      await fetch(`${API_BASE}/providers/${id}`, { method: 'DELETE' });
      setMessage('Provider 已删除');
      fetchData();
    } catch (e) {
      setMessage('删除失败: ' + (e as Error).message);
    }
    setLoading(false);
  };

  const testConnection = async (id: string) => {
    setTestingProvider(id);
    setMessage('正在测试连接...');
    try {
      const res = await fetch(`${API_BASE}/providers/${id}/test`, { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        setMessage(`✅ 连接成功！延迟 ${data.latency_ms}ms，发现 ${data.models_count} 个模型`);
      } else {
        setMessage(`❌ 连接失败: ${data.message} (${data.error_type})`);
      }
    } catch (e) {
      setMessage('测试失败: ' + (e as Error).message);
    }
    setTestingProvider(null);
  };

  const syncModels = async (id: string) => {
    setLoading(true);
    setMessage('正在同步模型列表...');
    try {
      const res = await fetch(`${API_BASE}/providers/${id}/sync-models`, { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        setMessage(`✅ 同步成功！新增 ${data.synced_count} 个模型`);
        fetchData();
      } else {
        setMessage('同步失败: ' + (data.detail || '未知错误'));
      }
    } catch (e) {
      setMessage('同步失败: ' + (e as Error).message);
    }
    setLoading(false);
  };

  const deleteModel = async (id: string) => {
    if (!confirm('确定删除此模型？')) return;
    await fetch(`${API_BASE}/models/${id}`, { method: 'DELETE' });
    fetchData();
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">⚙️ 模型中枢</h1>
          <p className="text-slate-400">配置 LLM Provider，管理模型，绑定宗门 Agent</p>
        </div>

        {/* Message */}
        {message && (
          <div className="mb-4 p-3 bg-slate-800 border border-slate-700 rounded text-sm">
            {message}
          </div>
        )}

        {/* Providers Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">📡 LLM Provider</h2>
            <button
              onClick={() => setShowAddProvider(!showAddProvider)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded text-sm font-medium"
            >
              + 添加 Provider
            </button>
          </div>

          {/* Add Provider Form */}
          {showAddProvider && (
            <div className="mb-4 p-4 bg-slate-800 border border-slate-700 rounded-lg">
              <h3 className="text-sm font-medium mb-3 text-slate-300">新增 Provider</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <input
                  type="text"
                  placeholder="名称 (如: DeepSeek)"
                  value={newProvider.name}
                  onChange={(e) => setNewProvider({ ...newProvider, name: e.target.value })}
                  className="px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm"
                />
                <input
                  type="text"
                  placeholder="Base URL"
                  value={newProvider.base_url}
                  onChange={(e) => setNewProvider({ ...newProvider, base_url: e.target.value })}
                  className="px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm"
                />
                <input
                  type="password"
                  placeholder="API Key"
                  value={newProvider.api_key}
                  onChange={(e) => setNewProvider({ ...newProvider, api_key: e.target.value })}
                  className="px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm"
                />
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={addProvider}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 rounded text-sm font-medium"
                >
                  {loading ? '保存中...' : '保存'}
                </button>
                <button
                  onClick={() => setShowAddProvider(false)}
                  className="px-4 py-2 bg-slate-600 hover:bg-slate-500 rounded text-sm"
                >
                  取消
                </button>
              </div>
            </div>
          )}

          {/* Provider Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {providers.map((p) => (
              <div key={p.id} className="p-4 bg-slate-800 border border-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">{p.name}</h3>
                  <span className={`text-xs px-2 py-1 rounded ${p.enabled ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                    {p.enabled ? '启用' : '禁用'}
                  </span>
                </div>
                <div className="text-xs text-slate-400 space-y-1 mb-3">
                  <div>URL: {p.base_url}</div>
                  <div>Key: {p.api_key_masked}</div>
                  <div>超时: {p.timeout_seconds}s | 重试: {p.max_retries}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => testConnection(p.id)}
                    disabled={testingProvider === p.id}
                    className="px-3 py-1 bg-blue-600/30 hover:bg-blue-600/50 border border-blue-500/50 rounded text-xs"
                  >
                    {testingProvider === p.id ? '测试中...' : '🔌 测试连接'}
                  </button>
                  <button
                    onClick={() => syncModels(p.id)}
                    disabled={loading}
                    className="px-3 py-1 bg-purple-600/30 hover:bg-purple-600/50 border border-purple-500/50 rounded text-xs"
                  >
                    🔄 同步模型
                  </button>
                  <button
                    onClick={() => deleteProvider(p.id)}
                    className="px-3 py-1 bg-red-600/30 hover:bg-red-600/50 border border-red-500/50 rounded text-xs"
                  >
                    🗑️ 删除
                  </button>
                </div>
              </div>
            ))}
            {providers.length === 0 && (
              <div className="col-span-full p-8 text-center text-slate-500 border border-dashed border-slate-700 rounded-lg">
                暂无 Provider，点击上方按钮添加
              </div>
            )}
          </div>
        </div>

        {/* Models Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">🤖 模型列表</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 text-slate-400">
                  <th className="text-left py-2 px-3">模型名称</th>
                  <th className="text-left py-2 px-3">Provider</th>
                  <th className="text-left py-2 px-3">状态</th>
                  <th className="text-left py-2 px-3">角色标签</th>
                  <th className="text-left py-2 px-3">操作</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => {
                  const provider = providers.find((p) => p.id === m.provider_id);
                  return (
                    <tr key={m.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                      <td className="py-2 px-3">
                        <div className="font-medium">{m.display_name || m.model_name}</div>
                        <div className="text-xs text-slate-500">{m.model_name}</div>
                      </td>
                      <td className="py-2 px-3 text-slate-400">{provider?.name || '未知'}</td>
                      <td className="py-2 px-3">
                        <span className={`text-xs px-2 py-1 rounded ${m.enabled ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                          {m.enabled ? '启用' : '禁用'}
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        <div className="flex flex-wrap gap-1">
                          {m.role_tags.map((tag) => (
                            <span key={tag} className="text-xs px-2 py-0.5 bg-slate-700 rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-2 px-3">
                        <button
                          onClick={() => deleteModel(m.id)}
                          className="text-xs text-red-400 hover:text-red-300"
                        >
                          删除
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {models.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      暂无模型，先添加 Provider 并同步模型列表
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Quick Start Guide */}
        <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
          <h3 className="text-sm font-medium mb-2 text-slate-300">📖 快速开始</h3>
          <ol className="text-xs text-slate-400 space-y-1 list-decimal list-inside">
            <li>点击「添加 Provider」配置你的大模型 API（支持 OpenAI、DeepSeek、OpenRouter 等）</li>
            <li>点击「测试连接」验证 API 是否可用</li>
            <li>点击「同步模型」拉取该 Provider 的模型列表</li>
            <li>进入世界页面，开启 🤖 LLM 模式，下一回合将真实调用大模型决策</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
