import { create } from 'zustand';
import { api } from './client';
import type { World, Sect, MapData, DiplomacyGraph, WorldEvent, Battle, TurnResult } from './client';

type WorldStore = {
  currentWorld: World | null;
  sects: Sect[];
  mapData: MapData | null;
  diplomacyGraph: DiplomacyGraph | null;
  events: WorldEvent[];
  battles: Battle[];
  loading: boolean;
  error: string | null;

  setCurrentWorld: (world: World | null) => void;
  loadWorld: (worldId: string) => Promise<void>;
  useLlm: boolean;
  setUseLlm: (value: boolean) => void;
  advanceTurn: (worldId: string, use_llm?: boolean) => Promise<TurnResult | null>;
  autoRun: (worldId: string, turns: number, use_llm?: boolean) => Promise<void>;
  refreshData: () => Promise<void>;
  clear: () => void;
};

export const useWorldStore = create<WorldStore>((set, get) => ({
  currentWorld: null,
  sects: [],
  mapData: null,
  diplomacyGraph: null,
  events: [],
  battles: [],
  loading: false,
  error: null,
  useLlm: false,

  setCurrentWorld: (world) => set({ currentWorld: world }),
  setUseLlm: (value) => set({ useLlm: value }),

  loadWorld: async (worldId) => {
    set({ loading: true, error: null });
    try {
      const world = await api.getWorld(worldId);
      const sects = await api.getSects(worldId);
      const map = await api.getMap(worldId);
      const graph = await api.getDiplomacyGraph(worldId);
      const events = await api.getEvents(worldId);
      const battles = await api.getBattles(worldId);
      set({
        currentWorld: world,
        sects,
        mapData: map,
        diplomacyGraph: graph,
        events: events,
        battles: battles,
        loading: false,
      });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  advanceTurn: async (worldId, use_llm) => {
    set({ loading: true, error: null });
    try {
      const llm = use_llm ?? get().useLlm;
      const result = await api.advanceTurn(worldId, llm);
      await get().loadWorld(worldId);
      return result;
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
      return null;
    }
  },

  autoRun: async (worldId, turns, use_llm) => {
    set({ loading: true, error: null });
    try {
      const llm = use_llm ?? get().useLlm;
      await api.autoRun(worldId, turns, llm);
      await get().loadWorld(worldId);
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  refreshData: async () => {
    const world = get().currentWorld;
    if (!world) return;
    await get().loadWorld(world.id);
  },

  clear: () => set({
    currentWorld: null,
    sects: [],
    mapData: null,
    diplomacyGraph: null,
    events: [],
    battles: [],
    loading: false,
    error: null,
  }),
}));
