import { useEffect, useRef, useState, useCallback } from 'react';
import { useRealtimeStore } from '../api/realtimeStore';
import { api } from '../api/client';
import type { World, Sect, MapData, WorldEvent, Battle } from '../api/client';

interface UseRealtimeWorldReturn {
  world: World | null;
  sects: Sect[];
  mapData: MapData | null;
  events: WorldEvent[];
  battles: Battle[];
  connected: boolean;
  speed: number;
  setSpeed: (speed: number) => void;
  paused: boolean;
  setPaused: (paused: boolean) => void;
  stop: () => void;
  selectedSectId: string | null;
  setSelectedSectId: (id: string | null) => void;
}

export function useRealtimeWorld(worldId: string): UseRealtimeWorldReturn {
  const store = useRealtimeStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [speed, setSpeed] = useState(1);
  const [paused, setPaused] = useState(false);
  const [selectedSectId, setSelectedSectId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      try {
        const [worldData, sectsData, mapData, eventsData, battlesData] = await Promise.all([
          api.getWorld(worldId),
          api.getSects(worldId),
          api.getMap(worldId),
          api.getEvents(worldId),
          api.getBattles(worldId),
        ]);

        if (!cancelled) {
          store.loadSnapshot({
            world: worldData,
            sects: sectsData,
            mapData,
            events: eventsData,
            battles: battlesData,
          });
        }
      } catch (err: any) {
        store.setError(err?.message || 'Failed to load world data');
      }
    }

    loadInitialData();

    return () => { cancelled = true; };
  }, [worldId]);

  useEffect(() => {
    if (!worldId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/worlds/${worldId}/ws`;

    function connect() {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => { store.setConnected(true); };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'event') {
              store.addEvent(data.payload as WorldEvent);
            } else if (data.type === 'battle') {
              store.addBattle(data.payload as Battle);
            } else if (data.type === 'update') {
              const payload = data.payload as {
                sect_id: string;
                resources: Record<string, number>;
                power: number;
              };
              store.updateResources(payload.sect_id, payload.resources, payload.power);
            } else if (data.type === 'world_update') {
              store.loadSnapshot(data.payload as {
                world: World;
                sects: Sect[];
                mapData: MapData;
                events: WorldEvent[];
                battles: Battle[];
              });
            }
          } catch {
            // Ignore malformed messages
          }
        };

        ws.onclose = () => {
          store.setConnected(false);
          reconnectTimerRef.current = setTimeout(connect, 3000);
        };

        ws.onerror = () => { store.setConnected(false); };
      } catch {
        reconnectTimerRef.current = setTimeout(connect, 3000);
      }
    }

    connect();

    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
      store.setConnected(false);
    };
  }, [worldId]);

  const stop = useCallback(() => {
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
    store.clear();
  }, []);

  return {
    world: store.world,
    sects: store.sects,
    mapData: store.mapData,
    events: store.events,
    battles: store.battles,
    connected: store.connected,
    speed,
    setSpeed,
    paused,
    setPaused,
    stop,
    selectedSectId,
    setSelectedSectId,
  };
}
