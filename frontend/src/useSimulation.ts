import { useState, useEffect, useCallback, useRef } from 'react';

export interface AGVData {
  id: string;
  x: number;
  y: number;
  theta: number;
  v: number;
  omega: number;
  l_rpm: number;
  r_rpm: number;
  max_rpm: number;
  is_running: boolean;
  target: { x: number; y: number };
  path: [number, number][];
}

export interface Telemetry {
  agvs: AGVData[];
  obstacles: any[];
}

export const useSimulation = (url: string) => {
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (ws.current) ws.current.close();
    const socket = new WebSocket(url);
    ws.current = socket;
    socket.onopen = () => setIsConnected(true);
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'telemetry') setTelemetry(message.data);
      } catch (e) { console.error("Parse error", e); }
    };
    socket.onclose = (event) => {
      setIsConnected(false);
      if (!event.wasClean) reconnectTimeoutRef.current = window.setTimeout(connect, 2000);
    };
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (ws.current) ws.current.close(1000, "Unmount");
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connect]);

  const sendCommand = useCallback((type: string, payload?: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type, ...payload }));
    }
  }, []);

  return { telemetry, isConnected, sendCommand };
};
