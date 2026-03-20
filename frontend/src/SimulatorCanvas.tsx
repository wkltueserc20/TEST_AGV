import React, { useRef, useEffect, useCallback } from 'react';
import type { Telemetry, AGVData } from './useSimulation';

interface Props {
  telemetry: Telemetry | null;
  selectedAgvId: string | null;
  selectedObstacleId: string | null;
  showSearch: boolean;
  onCanvasClick: (x: number, y: number) => void;
  onCanvasDoubleClick: (x: number, y: number) => void; // 新增雙擊回調
  onCanvasRightClick: (x: number, y: number) => void;
  onAgvSelect: (id: string) => void;
}

const MAP_SIZE = 50000;
const GRID_SIZE = 200; 

const SimulatorCanvas: React.FC<Props> = ({ 
  telemetry, selectedAgvId, selectedObstacleId, showSearch,
  onCanvasClick, onCanvasDoubleClick, onCanvasRightClick, onAgvSelect 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const telemetryRef = useRef<Telemetry | null>(null);
  const selectedAgvIdRef = useRef<string | null>(null);
  const selectedObstacleIdRef = useRef<string | null>(null);
  
  const revealedIndices = useRef<Record<string, number>>({});
  const lastSearchFingerprints = useRef<Record<string, string>>({});

  useEffect(() => { telemetryRef.current = telemetry; }, [telemetry]);
  useEffect(() => { selectedAgvIdRef.current = selectedAgvId; }, [selectedAgvId]);
  useEffect(() => { selectedObstacleIdRef.current = selectedObstacleId; }, [selectedObstacleId]);

  const displayStates = useRef<Record<string, {x: number, y: number, theta: number, lastUpdate: number}>>({});
  const animationFrameId = useRef<number>();

  const worldToCanvas = useCallback((x: number, y: number, canvas: HTMLCanvasElement) => {
    const scale = canvas.width / MAP_SIZE;
    return { cx: x * scale, cy: canvas.height - (y * scale) };
  }, []);

  const canvasToWorld = useCallback((cx: number, cy: number, canvas: HTMLCanvasElement) => {
    const scale = MAP_SIZE / canvas.width;
    return { x: cx * scale, y: (canvas.height - cy) * scale };
  }, []);

  const render = useCallback(() => {
    const canvas = canvasRef.current;
    const currentTelemetry = telemetryRef.current;
    const currentSelectedAgvId = selectedAgvIdRef.current;
    const currentSelectedObId = selectedObstacleIdRef.current;

    if (!canvas || !currentTelemetry) {
        animationFrameId.current = requestAnimationFrame(render);
        return;
    }
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const now = performance.now();
    const multiplier = (currentTelemetry as any).multiplier || 10;

    currentTelemetry.agvs.forEach(a => {
      if (!displayStates.current[a.id]) {
        displayStates.current[a.id] = { x: a.x, y: a.y, theta: a.theta, lastUpdate: now };
      } else {
        const ds = displayStates.current[a.id];
        const dt = (now - ds.lastUpdate) / 1000.0;
        if (a.is_running) {
          const simDt = dt * multiplier;
          ds.x += a.v * Math.cos(ds.theta) * simDt;
          ds.y += a.v * Math.sin(ds.theta) * simDt;
          ds.theta += a.omega * simDt;
          ds.x += (a.x - ds.x) * 0.05;
          ds.y += (a.y - ds.y) * 0.05;
          let dTheta = a.theta - ds.theta;
          while (dTheta > Math.PI) dTheta -= Math.PI * 2;
          while (dTheta < -Math.PI) dTheta += Math.PI * 2;
          ds.theta += dTheta * 0.05;
        } else {
          ds.x = a.x; ds.y = a.y; ds.theta = a.theta;
        }
        ds.lastUpdate = now;
      }

      if (a.visited && a.visited.length > 0) {
        const first = a.visited[0], last = a.visited[a.visited.length - 1];
        const fingerprint = `${a.visited.length}-${first[0]},${first[1]}-${last[0]},${last[1]}`;
        if (fingerprint !== lastSearchFingerprints.current[a.id]) {
            revealedIndices.current[a.id] = 0;
            lastSearchFingerprints.current[a.id] = fingerprint;
        }
        if (revealedIndices.current[a.id] < a.visited.length) {
            revealedIndices.current[a.id] += 50;
        }
      }
    });

    ctx.fillStyle = '#f0f0f0';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = '#ccc';
    for (let i = 0; i <= MAP_SIZE; i += 1000) {
      const p1 = worldToCanvas(i, 0, canvas);
      const p2 = worldToCanvas(i, MAP_SIZE, canvas);
      ctx.beginPath(); ctx.moveTo(p1.cx, p1.cy); ctx.lineTo(p2.cx, p2.cy); ctx.stroke();
      const p3 = worldToCanvas(0, i, canvas);
      const p4 = worldToCanvas(MAP_SIZE, i, canvas);
      ctx.beginPath(); ctx.moveTo(p3.cx, p3.cy); ctx.lineTo(p4.cx, p4.cy); ctx.stroke();
    }

    const scale = canvas.width / MAP_SIZE;

    const selectedAgv = currentTelemetry.agvs.find(a => a.id === currentSelectedAgvId);
    if (showSearch && selectedAgv?.visited) {
        ctx.fillStyle = 'rgba(0, 123, 255, 0.25)';
        const blockSize = GRID_SIZE * scale;
        const count = revealedIndices.current[selectedAgv.id] || 0;
        for (let i = 0; i < Math.min(count, selectedAgv.visited.length); i++) {
            const node = selectedAgv.visited[i];
            const { cx, cy } = worldToCanvas(node[0] * GRID_SIZE, node[1] * GRID_SIZE, canvas);
            ctx.fillRect(cx - blockSize/2, cy - blockSize/2, blockSize, blockSize);
        }
    }

    if (selectedAgv?.path) {
      ctx.setLineDash([5, 5]);
      ctx.strokeStyle = 'rgba(255, 0, 0, 0.6)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      selectedAgv.path.forEach((p, i) => {
        const cp = worldToCanvas(p[0], p[1], canvas);
        if (i === 0) ctx.moveTo(cp.cx, cp.cy); else ctx.lineTo(cp.cx, cp.cy);
      });
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.lineWidth = 1;
    }

    currentTelemetry.obstacles.forEach(ob => {
      const { cx, cy } = worldToCanvas(ob.x, ob.y, canvas);
      ctx.fillStyle = currentSelectedObId === ob.id ? 'rgba(255, 0, 0, 0.7)' : 'rgba(0, 0, 0, 0.5)';
      if (ob.type === 'circle') {
        ctx.beginPath(); ctx.arc(cx, cy, ob.radius * scale, 0, 2*Math.PI); ctx.fill();
      } else {
        ctx.save(); ctx.translate(cx, cy); ctx.rotate(-ob.angle);
        ctx.fillRect(-ob.width*scale/2, -ob.height*scale/2, ob.width*scale, ob.height*scale);
        ctx.restore();
      }
    });

    currentTelemetry.agvs.forEach(a => {
      const ds = displayStates.current[a.id];
      if (!ds) return;
      const { cx, cy } = worldToCanvas(ds.x, ds.y, canvas);
      const agvSize = 1000 * scale;
      const goal = worldToCanvas(a.target.x, a.target.y, canvas);
      ctx.fillStyle = a.id === currentSelectedAgvId ? '#28a745' : '#aaa';
      ctx.beginPath(); ctx.arc(goal.cx, goal.cy, 6, 0, 2*Math.PI); ctx.fill();
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(-ds.theta);
      ctx.fillStyle = a.id === currentSelectedAgvId ? '#007bff' : '#6c757d';
      ctx.fillRect(-agvSize/2, -agvSize/2, agvSize, agvSize);
      if (a.id === currentSelectedAgvId) {
        ctx.strokeStyle = 'white'; ctx.lineWidth = 2; ctx.strokeRect(-agvSize/2, -agvSize/2, agvSize, agvSize);
      }
      ctx.fillStyle = 'white'; ctx.fillRect(agvSize/4, -agvSize/10, agvSize/4, agvSize/5);
      ctx.restore();
      ctx.fillStyle = '#333'; ctx.font = '10px Arial';
      ctx.fillText(a.id, cx - 15, cy - agvSize);
    });

    animationFrameId.current = requestAnimationFrame(render);
  }, [worldToCanvas, showSearch]);

  useEffect(() => {
    animationFrameId.current = requestAnimationFrame(render);
    return () => { if (animationFrameId.current) cancelAnimationFrame(animationFrameId.current); };
  }, [render]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current; if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const { x, y } = canvasToWorld(e.clientX - rect.left, e.clientY - rect.top, canvas);
    const currentTelemetry = telemetryRef.current;
    const clickedAgv = currentTelemetry?.agvs.find(a => Math.sqrt((a.x-x)**2+(a.y-y)**2) < 1500);
    if (clickedAgv) onAgvSelect(clickedAgv.id);
    else onCanvasClick(x, y);
  };

  const handleDoubleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current; if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const { x, y } = canvasToWorld(e.clientX - rect.left, e.clientY - rect.top, canvas);
    onCanvasDoubleClick(x, y);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <canvas ref={canvasRef} width={750} height={750} 
        style={{ border: '2px solid #333', background: '#1a1a1a', cursor: 'crosshair' }} 
        onClick={handleClick} 
        onDoubleClick={handleDoubleClick}
        onContextMenu={(e) => {
            e.preventDefault();
            const rect = canvasRef.current?.getBoundingClientRect();
            if (rect) {
                const { x, y } = canvasToWorld(e.clientX - rect.left, e.clientY - rect.top, canvasRef.current!);
                onCanvasRightClick(x, y);
            }
        }} 
      />
    </div>
  );
};

export default SimulatorCanvas;
