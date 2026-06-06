import { create } from 'zustand';
import type { World, Sect, MapData, WorldEvent, Battle } from './client';

interface TimelineEntry {
  id: string;
  turn: number;
  type: 'event' | 'battle' | 'action';
  title: string;
  description: string;
  severity?: number;
  sect_ids?: string[];
}

interface RealtimeState {
  world: World | null;
  sects: Sect[];
  mapData: MapData | null;
  events: WorldEvent[];
  battles: Battle[];
  timeline: TimelineEntry[];
  powerHistory: Record<string, number[]>;
  connected: boolean;
  loading: boolean;
  error: string | null;

  loadSnapshot: (data: {
    world: World;
    sects: Sect[];
    mapData: MapData;
    events: WorldEvent[];
    battles: Battle[];
  }) => void;

  updateResources: (sectId: string, resources: Record<string, number>, power: number) => void;

  addEvent: (event: WorldEvent) => void;
  addBattle: (battle: Battle) => void;
  addTimelineEntry: (entry: TimelineEntry) => void;

  setConnected: (connected: boolean) => void;
  setError: (error: string | null) => void;
  clear: () => void;
}

export const useRealtimeStore = create<RealtimeState>((set, get) => ({
  world: null,
  sects: [],
  mapData: null,
  events: [],
  battles: [],
  timeline: [],
  powerHistory: {},
  connected: false,
  loading: false,
  error: null,

  loadSnapshot: (data) => {
    const powerHistory: Record<string, number[]> = {};
    data.sects.forEach((sect) => {
      powerHistory[sect.id] = [sect.stats.military_power || 0];
    });

    const timeline: TimelineEntry[] = [
      ...data.events.map((e) => ({
        id: e.id,
        turn: e.turn,
        type: 'event' as const,
        title: e.title,
        description: e.description,
        severity: e.severity,
        sect_ids: e.affected_sects,
      })),
      ...data.battles.map((b) => ({
        id: b.id,
        turn: b.turn,
        type: 'battle' as const,
        title: `战争: ${b.attacker_sect_id} vs ${b.defender_sect_id}`,
        description: b.battle_log || '',
        severity: b.result_type === 'decisive_victory' ? 1.0 : 0.7,
        sect_ids: [b.attacker_sect_id, b.defender_sect_id],
      })),
    ].sort((a, b) => b.turn - a.turn);

    set({
      world: data.world,
      sects: data.sects,
      mapData: data.mapData,
      events: data.events,
      battles: data.battles,
      timeline,
      powerHistory,
      connected: true,
      loading: false,
    });
  },

  updateResources: (sectId, resources, power) => {
    const { sects, powerHistory } = get();
    const updatedSects = sects.map((s) =>
      s.id === sectId ? { ...s, resources: { ...s.resources, ...resources }, stats: { ...s.stats, military_power: power } } : s
    );

    const updatedHistory = { ...powerHistory };
    if (!updatedHistory[sectId]) {
      updatedHistory[sectId] = [];
    }
    updatedHistory[sectId] = [...updatedHistory[sectId], power].slice(-50);

    set({ sects: updatedSects, powerHistory: updatedHistory });
  },

  addEvent: (event) => {
    set((state) => ({
      events: [event, ...state.events],
      timeline: [
        {
          id: event.id,
          turn: event.turn,
          type: 'event',
          title: event.title,
          description: event.description,
          severity: event.severity,
          sect_ids: event.affected_sects,
        },
        ...state.timeline,
      ],
    }));
  },

  addBattle: (battle) => {
    set((state) => ({
      battles: [battle, ...state.battles],
      timeline: [
        {
          id: battle.id,
          turn: battle.turn,
          type: 'battle',
          title: `战争: ${battle.attacker_sect_id} vs ${battle.defender_sect_id}`,
          description: battle.battle_log || '',
          severity: battle.result_type === 'decisive_victory' ? 1.0 : 0.7,
          sect_ids: [battle.attacker_sect_id, battle.defender_sect_id],
        },
        ...state.timeline,
      ],
    }));
  },

  addTimelineEntry: (entry) => {
    set((state) => ({
      timeline: [entry, ...state.timeline],
    }));
  },

  setConnected: (connected) => set({ connected }),
  setError: (error) => set({ error, loading: false }),
  clear: () => set({
    world: null,
    sects: [],
    mapData: null,
    events: [],
    battles: [],
    timeline: [],
    powerHistory: {},
    connected: false,
    loading: false,
    error: null,
  }),
}));
