const BASE = '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

export interface World {
  id: string;
  name: string;
  description: string;
  status: string;
  current_turn: number;
  max_turns: number | null;
  world_seed: number;
  mode: string;
  map_size: string;
  sect_count: number;
  rules: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Sect {
  id: string;
  world_id: string;
  name: string;
  sect_type: string;
  leader_name: string;
  status: string;
  resources: Record<string, number>;
  stats: Record<string, number>;
  personality: Record<string, number>;
  memory: Array<Record<string, unknown>>;
  controlled_regions: string[];
  strategy_summary: string;
  win_score: number;
  reliability: number;
}

export interface Region {
  id: string;
  world_id: string;
  name: string;
  region_type: string;
  owner_sect_id: string | null;
  resource_level: number;
  defense_level: number;
  stability: number;
  neighbors: string[];
  special_flags: string[];
}

export interface MapData {
  nodes: Array<{
    id: string;
    name: string;
    region_type: string;
    owner_sect_id: string | null;
    owner_name: string;
    owner_color: string;
    resource_level: number;
    defense_level: number;
    neighbors: string[];
  }>;
  sects: Array<{ id: string; name: string; color: string }>;
}

export interface DiplomacyRelation {
  id: string;
  sect_a_id: string;
  sect_b_id: string;
  sect_a_name: string;
  sect_b_name: string;
  relation_type: string;
  relation_score: number;
  trust_score: number;
}

export interface DiplomacyGraph {
  nodes: Array<{ id: string; name: string; type: string; status: string }>;
  edges: Array<{
    source: string;
    target: string;
    relation_type: string;
    score: number;
  }>;
}

export interface WorldEvent {
  id: string;
  world_id: string;
  turn: number;
  event_type: string;
  title: string;
  description: string;
  severity: number;
  affected_sects: string[];
  affected_regions: string[];
  tags: string[];
}

export interface Battle {
  id: string;
  world_id: string;
  turn: number;
  attacker_sect_id: string;
  defender_sect_id: string;
  region_id: string | null;
  result_type: string;
  winner_sect_id: string | null;
  attacker_power: number;
  defender_power: number;
  losses: Record<string, number>;
  rewards: Record<string, unknown>;
  battle_log: string;
}

export interface TurnResult {
  turn: number;
  world_status: string;
  actions_count: number;
  results_count: number;
  events_count: number;
  summary: string;
}

export interface TurnRecord {
  id: string;
  turn: number;
  status: string;
  summary: string;
}

export interface CreateWorldInput {
  name: string;
  description?: string;
  mode?: string;
  max_turns?: number;
  sect_count?: number;
  map_size?: string;
  world_seed?: number;
  rules?: Record<string, unknown>;
}

// API functions
export const api = {
  // Worlds
  listWorlds: () => request<World[]>('/worlds'),
  getWorld: (id: string) => request<World>(`/worlds/${id}`),
  createWorld: (data: CreateWorldInput) => request<World>('/worlds', { method: 'POST', body: JSON.stringify(data) }),
  deleteWorld: (id: string) => request<{ ok: boolean }>(`/worlds/${id}`, { method: 'DELETE' }),

  // Sects
  getSects: (worldId: string) => request<Sect[]>(`/worlds/${worldId}/sects`),
  getSect: (worldId: string, sectId: string) => request<Sect>(`/worlds/${worldId}/sects/${sectId}`),

  // Map
  getMap: (worldId: string) => request<MapData>(`/worlds/${worldId}/map`),
  getRegions: (worldId: string) => request<Region[]>(`/worlds/${worldId}/regions`),

  // Diplomacy
  getDiplomacy: (worldId: string) => request<DiplomacyRelation[]>(`/worlds/${worldId}/diplomacy`),
  getDiplomacyGraph: (worldId: string) => request<DiplomacyGraph>(`/worlds/${worldId}/diplomacy/graph`),

  // Events
  getEvents: (worldId: string, turn?: number, tags?: string) => {
    const params = new URLSearchParams();
    if (turn !== undefined) params.set('turn', String(turn));
    if (tags) params.set('tags', tags);
    return request<WorldEvent[]>(`/worlds/${worldId}/events?${params}`);
  },

  // Battles
  getBattles: (worldId: string) => request<Battle[]>(`/worlds/${worldId}/battles`),

  // Turns
  advanceTurn: (worldId: string, use_llm: boolean = false) =>
    request<TurnResult>(`/worlds/${worldId}/turns/next?use_llm=${use_llm}`, { method: 'POST' }),
  autoRun: (worldId: string, turns: number = 10, use_llm: boolean = false) =>
    request<{ turns_run: number; results: TurnResult[] }>(`/worlds/${worldId}/turns/auto-run?turns=${turns}&use_llm=${use_llm}`, { method: 'POST' }),
  pauseWorld: (worldId: string) => request<{ ok: boolean }>(`/worlds/${worldId}/turns/pause`, { method: 'POST' }),
  resumeWorld: (worldId: string) => request<{ ok: boolean }>(`/worlds/${worldId}/turns/resume`, { method: 'POST' }),
  getTurnRecords: (worldId: string) => request<TurnRecord[]>(`/worlds/${worldId}/turns`),
  getTurnReplay: (worldId: string, turn: number) =>
    request<{ turn: number; summary: string; timeline: Array<Record<string, unknown>> }>(`/worlds/${worldId}/turns/${turn}/replay`),
};