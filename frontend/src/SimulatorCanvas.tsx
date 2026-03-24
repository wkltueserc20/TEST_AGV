import React, { useRef, useEffect, useCallback, useState } from 'react';
import type { Telemetry, AGVData } from './useSimulation';

interface Props {
  telemetry: Telemetry | null;
  selectedAgvId: string | null;
  selectedObstacleId: string | null;
  showSearch: boolean;
  onCanvasClick: (x: number, y: number) => void;
  onCanvasDoubleClick: (x: number, y: number) => void;
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
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 750, height: 750 });
  const [viewState, setViewState] = useState({ zoom: 1.0, offsetX: 0, offsetY: 0 });
  const isDragging = useRef(false);
  const lastMousePos = useRef({ x: 0, y: 0 });

  const telemetryRef = useRef<Telemetry | null>(null);
  const selectedAgvIdRef = useRef<string | null>(null);
  const selectedObstacleIdRef = useRef<string | null>(null);
  const revealedIndices = useRef<Record<string, number>>({});
  const lastSearchFingerprints = useRef<Record<string, string>>({});

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        const size = Math.min(clientWidth, clientHeight) - 40;
        setDimensions({ width: size, height: size });
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const handleWheelNative = (e: WheelEvent) => {
      e.preventDefault();
      const zoomSpeed = 0.15;
      const direction = e.deltaY > 0 ? -1 : 1;
      setViewState(prev => ({ 
        ...prev, 
        zoom: Math.min(Math.max(prev.zoom + direction * zoomSpeed * prev.zoom, 0.2), 20.0) 
      }));
    };
    canvas.addEventListener('wheel', handleWheelNative, { passive: false });
    return () => canvas.removeEventListener('wheel', handleWheelNative);
  }, []);

  useEffect(() => { telemetryRef.current = telemetry; }, [telemetry]);
  useEffect(() => { selectedAgvIdRef.current = selectedAgvId; }, [selectedAgvId]);
  useEffect(() => { selectedObstacleIdRef.current = selectedObstacleId; }, [selectedObstacleId]);

  const displayStates = useRef<Record<string, {x: number, y: number, theta: number, lastUpdate: number}>>({});
  const animationFrameId = useRef<number>();

  const worldToCanvas = useCallback((x: number, y: number, w: number, h: number, vs: any) => {
    const scale = (w / MAP_SIZE) * vs.zoom;
    return { cx: (x * scale) + vs.offsetX, cy: h - (y * scale) + vs.offsetY };
  }, []);

  const canvasToWorld = useCallback((cx: number, cy: number, w: number, h: number, vs: any) => {
    const scale = (w / MAP_SIZE) * vs.zoom;
    return { x: (cx - vs.offsetX) / scale, y: (h + vs.offsetY - cy) / scale };
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 1 || (e.button === 0 && e.altKey)) {
        isDragging.current = true;
        lastMousePos.current = { x: e.clientX, y: e.clientY };
        e.preventDefault();
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging.current) {
        const dx = e.clientX - lastMousePos.current.x;
        const dy = e.clientY - lastMousePos.current.y;
        setViewState(prev => ({ ...prev, offsetX: prev.offsetX + dx, offsetY: prev.offsetY + dy }));
        lastMousePos.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseUp = () => { isDragging.current = false; };

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
    const { width: w, height: h } = dimensions;
    const vs = viewState;
    const scale = (w / MAP_SIZE) * vs.zoom;

    // --- 1. 更新 AGV 動畫狀態 ---
    currentTelemetry.agvs.forEach(a => {
      if (!displayStates.current[a.id]) {
        displayStates.current[a.id] = { x: a.x, y: a.y, theta: a.theta, lastUpdate: now };
      } else {
        const ds = displayStates.current[a.id];
        const dt = (now - ds.lastUpdate) / 1000.0;
        if (a.is_running) {
          ds.x += a.v * Math.cos(ds.theta) * dt;
          ds.y += a.v * Math.sin(ds.theta) * dt;
          ds.theta += a.omega * dt;
          ds.x += (a.x - ds.x) * 0.3;
          ds.y += (a.y - ds.y) * 0.3;
          let dTheta = a.theta - ds.theta;
          while (dTheta > Math.PI) dTheta -= Math.PI * 2;
          while (dTheta < -Math.PI) dTheta += Math.PI * 2;
          ds.theta += dTheta * 0.3;
        } else {
          ds.x = a.x; ds.y = a.y; ds.theta = a.theta;
        }
        ds.lastUpdate = now;
      }
    });

    // --- 2. 背景繪製 ---
    ctx.fillStyle = '#0d0e12';
    ctx.fillRect(0, 0, w, h);

    const pTopLeft = worldToCanvas(0, MAP_SIZE, w, h, vs);
    const pBottomRight = worldToCanvas(MAP_SIZE, 0, w, h, vs);
    ctx.strokeStyle = '#2d333b';
    ctx.lineWidth = Math.max(1, 2 * vs.zoom);
    ctx.strokeRect(pTopLeft.cx, pTopLeft.cy, pBottomRight.cx - pTopLeft.cx, pBottomRight.cy - pTopLeft.cy);

    ctx.fillStyle = '#3a3f4b';
    for (let x = 0; x <= MAP_SIZE; x += 5000) {
      for (let y = 0; y <= MAP_SIZE; y += 5000) {
        const { cx, cy } = worldToCanvas(x, y, w, h, vs);
        if (cx >= 0 && cx <= w && cy >= 0 && cy <= h) {
            ctx.beginPath(); ctx.arc(cx, cy, Math.max(0.1, 1.5 * vs.zoom), 0, Math.PI * 2); ctx.fill();
        }
      }
    }

    // --- 2.5 繪製 Search Debug Layer (A* 搜尋軌跡) ---
    const selectedAgv = currentTelemetry.agvs.find(a => a.id === currentSelectedAgvId);
    if (showSearch && selectedAgv?.visited) {
        const fingerprint = `${selectedAgv.visited.length}-${selectedAgv.visited[0] ? selectedAgv.visited[0][0] : 0}`;
        if (fingerprint !== lastSearchFingerprints.current[selectedAgv.id]) {
            revealedIndices.current[selectedAgv.id] = 0;
            lastSearchFingerprints.current[selectedAgv.id] = fingerprint;
        }
        if (revealedIndices.current[selectedAgv.id] < selectedAgv.visited.length) {
            revealedIndices.current[selectedAgv.id] += 100;
        }
        ctx.fillStyle = 'rgba(0, 255, 255, 0.08)';
        const blockSize = GRID_SIZE * scale;
        const count = revealedIndices.current[selectedAgv.id] || 0;
        for (let i = 0; i < Math.min(count, selectedAgv.visited.length); i++) {
            const node = selectedAgv.visited[i];
            const { cx, cy } = worldToCanvas(node[0] * GRID_SIZE, node[1] * GRID_SIZE, w, h, vs);
            ctx.fillRect(cx - blockSize/2, cy - blockSize/2, blockSize, blockSize);
        }
    }

    // --- 3. 目標與路徑繪製 ---
    currentTelemetry.agvs.forEach(a => {
      const isSelected = a.id === currentSelectedAgvId;
      const { cx, cy } = worldToCanvas(a.target.x, a.target.y, w, h, vs);
      
      // 繪製目標點
      ctx.save(); ctx.translate(cx, cy);
      const pulse = Math.max(0.1, (1 + Math.sin(now / 200) * 0.15) * vs.zoom);
      ctx.strokeStyle = isSelected ? '#39ff14' : '#1b5e20';
      ctx.lineWidth = 2 * vs.zoom;
      ctx.beginPath(); ctx.arc(0, 0, 12 * pulse, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-15*vs.zoom, 0); ctx.lineTo(15*vs.zoom, 0); ctx.moveTo(0, -15*vs.zoom); ctx.lineTo(0, 15*vs.zoom); ctx.stroke();
      ctx.restore();

      // 繪製路徑
      if (isSelected && a.path) {
        ctx.save();
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = '#ff4d4d';
        ctx.lineWidth = 2 * vs.zoom;
        ctx.shadowBlur = 10; ctx.shadowColor = '#ff4d4d';
        ctx.beginPath();
        a.path.forEach((p, i) => {
          const cp = worldToCanvas(p[0], p[1], w, h, vs);
          if (i === 0) ctx.moveTo(cp.cx, cp.cy); else ctx.lineTo(cp.cx, cp.cy);
        });
        ctx.stroke();
        ctx.restore();
      }
    });

    // --- 3.5 繪製路徑預演 (Path Occupancy / Repulsion Zones) ---
    if (currentTelemetry.path_occupancy) {
        ctx.save();
        Object.entries(currentTelemetry.path_occupancy).forEach(([id, points]) => {
            ctx.fillStyle = 'rgba(255, 77, 77, 0.08)';
            points.forEach(p => {
                const cp = worldToCanvas(p[0], p[1], w, h, vs);
                ctx.beginPath();
                ctx.arc(cp.cx, cp.cy, 800 * scale, 0, Math.PI * 2);
                ctx.fill();
            });
        });
        ctx.restore();
    }

    // --- 3.6 繪製社交連結 (Yielding / Waiting Lines) ---
    if (currentTelemetry.social_links) {
        currentTelemetry.social_links.forEach(link => {
            const fromAgv = currentTelemetry.agvs.find(a => a.id === link.from);
            const toAgv = currentTelemetry.agvs.find(a => a.id === link.to);
            if (fromAgv && toAgv) {
                const p1 = worldToCanvas(fromAgv.x, fromAgv.y, w, h, vs);
                const p2 = worldToCanvas(toAgv.x, toAgv.y, w, h, vs);
                ctx.save();
                ctx.setLineDash([5, 5]);
                const color = link.type === 'WAITING' ? 'rgba(255, 152, 0, 0.6)' : 'rgba(187, 134, 252, 0.6)';
                ctx.strokeStyle = color;
                ctx.lineWidth = 2 * vs.zoom;
                ctx.beginPath(); ctx.moveTo(p1.cx, p1.cy); ctx.lineTo(p2.cx, p2.cy); ctx.stroke();
                const angle = Math.atan2(p2.cy - p1.cy, p2.cx - p1.cx);
                ctx.translate(p2.cx - Math.cos(angle) * 30 * vs.zoom, p2.cy - Math.sin(angle) * 30 * vs.zoom);
                ctx.rotate(angle);
                ctx.fillStyle = color;
                ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-10 * vs.zoom, -5 * vs.zoom); ctx.lineTo(-10 * vs.zoom, 5 * vs.zoom); ctx.fill();
                ctx.restore();
            }
        });
    }

    // --- 4. 靜態障礙物繪製 ---
    currentTelemetry.obstacles.filter(ob => ob.type !== 'equipment').forEach(ob => {
      const { cx, cy } = worldToCanvas(ob.x, ob.y, w, h, vs);
      const isSelected = currentSelectedObId === ob.id;
      ctx.save(); ctx.translate(cx, cy);
      if (ob.type === 'circle') {
          const r = Math.max(0.1, (ob.radius || 500) * scale);
          ctx.fillStyle = isSelected ? '#ff6600' : '#d4af37';
          ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
          ctx.restore(); ctx.save(); ctx.translate(cx, cy);
          ctx.strokeStyle = isSelected ? '#fff' : '#ffd700';
          ctx.lineWidth = 1.5 * vs.zoom;
          ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
      } else {
          ctx.rotate(-ob.angle);
          const ow = ob.width * scale, oh = ob.height * scale;
          ctx.fillStyle = isSelected ? '#ff6600' : '#d4af37';
          ctx.fillRect(-ow/2, -oh/2, ow, oh);
          ctx.restore(); ctx.save(); ctx.translate(cx, cy); ctx.rotate(-ob.angle);
          ctx.strokeStyle = isSelected ? '#fff' : '#ffd700';
          ctx.lineWidth = 1.5 * vs.zoom;
          ctx.strokeRect(-ow/2, -oh/2, ow, oh);
      }
      ctx.restore();
    });

    // --- 5. AGV 本體繪製 ---
    currentTelemetry.agvs.forEach(a => {
      const ds = displayStates.current[a.id];
      if (!ds) return;
      const { cx, cy } = worldToCanvas(ds.x, ds.y, w, h, vs);
      const isSelected = a.id === currentSelectedAgvId;
      const sz = 1000 * scale;
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(-ds.theta);
      let strokeColor = isSelected ? '#00f2ff' : '#555';
      ctx.fillStyle = '#1a1a1a'; ctx.strokeStyle = strokeColor; ctx.lineWidth = 2 * vs.zoom;
      const r = Math.max(0.1, 10 * scale);
      ctx.beginPath(); ctx.moveTo(-sz/2 + r, -sz/2); ctx.lineTo(sz/2 - r, -sz/2);
      ctx.quadraticCurveTo(sz/2, -sz/2, sz/2, -sz/2 + r); ctx.lineTo(sz/2, sz/2 - r);
      ctx.quadraticCurveTo(sz/2, sz/2, sz/2 - r, sz/2); ctx.lineTo(-sz/2 + r, sz/2);
      ctx.quadraticCurveTo(-sz/2, sz/2, -sz/2, sz/2 - r); ctx.lineTo(-sz/2, -sz/2 + r);
      ctx.quadraticCurveTo(-sz/2, -sz/2, -sz/2 + r, -sz/2); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.arc(0, 0, Math.max(0.1, sz/4), 0, Math.PI * 2); ctx.fillStyle = '#333'; ctx.fill();
      ctx.fillStyle = isSelected ? '#00f2ff' : '#aaa';
      ctx.beginPath(); ctx.moveTo(sz/2 - 5*vs.zoom, 0); ctx.lineTo(sz/2 - 15*vs.zoom, -10*vs.zoom); ctx.lineTo(sz/2 - 15*vs.zoom, 10*vs.zoom); ctx.fill();
      ctx.restore();
      ctx.fillStyle = '#fff'; ctx.font = `bold ${Math.max(8, 11 * vs.zoom)}px monospace`;
      ctx.fillText(a.id, cx - 20, cy - sz * 0.7);
    });

    // --- 6. 設備 (星星) 在最上層 ---
    const drawStar = (ctx: CanvasRenderingContext2D, cx: number, cy: number, spikes: number, outerRadius: number, innerRadius: number) => {
      let rot = Math.PI / 2 * 3;
      let step = Math.PI / spikes;
      ctx.beginPath(); ctx.moveTo(cx, cy - outerRadius)
      for (let i = 0; i < spikes; i++) {
        ctx.lineTo(cx + Math.cos(rot) * outerRadius, cy + Math.sin(rot) * outerRadius); rot += step;
        ctx.lineTo(cx + Math.cos(rot) * innerRadius, cy + Math.sin(rot) * innerRadius); rot += step;
      }
      ctx.lineTo(cx, cy - outerRadius); ctx.closePath();
    };

    currentTelemetry.obstacles.filter(ob => ob.type === 'equipment').forEach(ob => {
      const { cx, cy } = worldToCanvas(ob.x, ob.y, w, h, vs);
      const isSelected = currentSelectedObId === ob.id;
      const size = (ob.radius || 1000) * scale;
      const colors: Record<string, string> = { 'normal': '#ffd700', 'running': '#39ff14', 'error': '#ff4d4d' };
      const baseColor = colors[ob.status || 'running'] || '#39ff14';
      ctx.save(); ctx.translate(cx, cy);
      ctx.globalAlpha = 0.7; ctx.fillStyle = isSelected ? '#ff6600' : baseColor;
      drawStar(ctx, 0, 0, 5, size, size * 0.45); ctx.fill();
      ctx.globalAlpha = 1.0; ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5 * vs.zoom;
      ctx.stroke();
      if (ob.docking_angle !== undefined) {
          const angleRad = (ob.docking_angle * Math.PI) / 180;
          // 指向入口：旋轉角度加 PI
          ctx.rotate(-angleRad + Math.PI); ctx.strokeStyle = '#00f2ff'; ctx.lineWidth = 2 * vs.zoom;
          ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(size * 0.8, 0);
          ctx.lineTo(size * 0.6, -size * 0.1); ctx.moveTo(size * 0.8, 0);
          ctx.lineTo(size * 0.6, size * 0.1); ctx.stroke();
      }

      ctx.restore();
      ctx.fillStyle = '#fff'; ctx.font = `bold ${Math.max(10, 12 * vs.zoom)}px monospace`;
      ctx.textAlign = 'center'; ctx.fillText(ob.id, cx, cy - size - 10 * vs.zoom);
    });

    animationFrameId.current = requestAnimationFrame(render);
  }, [worldToCanvas, dimensions, viewState, showSearch]);

  useEffect(() => {
    animationFrameId.current = requestAnimationFrame(render);
    return () => { if (animationFrameId.current) cancelAnimationFrame(animationFrameId.current); };
  }, [render]);

  const handleInteraction = (e: React.MouseEvent<HTMLCanvasElement>, callback: (x: number, y: number) => void) => {
    const canvas = canvasRef.current; if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const { x, y } = canvasToWorld(e.clientX - rect.left, e.clientY - rect.top, dimensions.width, dimensions.height, viewState);
    callback(x, y);
  };

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
      <canvas ref={canvasRef} width={dimensions.width} height={dimensions.height} 
        style={{ border: '2px solid #333', background: '#0d0e12', cursor: isDragging.current ? 'grabbing' : 'crosshair' }} 
        onMouseDown={handleMouseDown} onMouseMove={handleMouseMove} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}
        onClick={(e) => {
            if (e.altKey) return;
            const canvas = canvasRef.current; if (!canvas) return;
            const rect = canvas.getBoundingClientRect();
            const { x, y } = canvasToWorld(e.clientX - rect.left, e.clientY - rect.top, dimensions.width, dimensions.height, viewState);
            const currentTelemetry = telemetryRef.current;
            const clickedEq = currentTelemetry?.obstacles.find(ob => ob.type === 'equipment' && Math.sqrt((ob.x-x)**2+(ob.y-y)**2) < 1500);
            if (clickedEq) onCanvasClick(x, y);
            else {
                const clickedAgv = currentTelemetry?.agvs.find(a => Math.sqrt((a.x-x)**2+(a.y-y)**2) < 1500);
                if (clickedAgv) onAgvSelect(clickedAgv.id);
                else onCanvasClick(x, y);
            }
        }} 
        onDoubleClick={(e) => handleInteraction(e, onCanvasDoubleClick)}
        onContextMenu={(e) => { e.preventDefault(); handleInteraction(e, onCanvasRightClick); }} 
      />
      <button style={{ position: 'absolute', bottom: '20px', right: '20px', opacity: 0.6 }} onClick={() => setViewState({ zoom: 1, offsetX: 0, offsetY: 0 })}>
        RESET VIEW
      </button>
    </div>
  );
};

export default SimulatorCanvas;
