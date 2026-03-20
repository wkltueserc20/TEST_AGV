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

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomSpeed = 0.1;
    const direction = e.deltaY > 0 ? -1 : 1;
    const newZoom = Math.min(Math.max(viewState.zoom + direction * zoomSpeed, 0.3), 15.0);
    setViewState(prev => ({ ...prev, zoom: newZoom }));
  };

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
    const multiplier = (currentTelemetry as any).multiplier || 10;
    const { width: w, height: h } = dimensions;
    const vs = viewState;

    // 1. 物理位置更新
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
        const fingerprint = `${a.visited.length}-${a.visited[0][0]}`;
        if (fingerprint !== lastSearchFingerprints.current[a.id]) {
            revealedIndices.current[a.id] = 0;
            lastSearchFingerprints.current[a.id] = fingerprint;
        }
        if (revealedIndices.current[a.id] < a.visited.length) revealedIndices.current[a.id] += 50;
      }
    });

    // 2. 繪圖基礎
    ctx.fillStyle = '#0d0e12';
    ctx.fillRect(0, 0, w, h);

    // --- 核心優化：地圖邊界與點陣 ---
    // 繪製地圖邊界線 (50m x 50m)
    const pTopLeft = worldToCanvas(0, MAP_SIZE, w, h, vs);
    const pBottomRight = worldToCanvas(MAP_SIZE, 0, w, h, vs);
    const mapWidth = pBottomRight.cx - pTopLeft.cx;
    const mapHeight = pBottomRight.cy - pTopLeft.cy;

    ctx.strokeStyle = '#2d333b';
    ctx.lineWidth = 2 * vs.zoom;
    ctx.strokeRect(pTopLeft.cx, pTopLeft.cy, mapWidth, mapHeight);

    // 繪製點狀格線 (僅在地圖內繪製)
    ctx.fillStyle = '#3a3f4b';
    for (let x = 0; x <= MAP_SIZE; x += 5000) {
      for (let y = 0; y <= MAP_SIZE; y += 5000) {
        const { cx, cy } = worldToCanvas(x, y, w, h, vs);
        if (cx >= 0 && cx <= w && cy >= 0 && cy <= h) {
            ctx.beginPath(); ctx.arc(cx, cy, 1.5 * vs.zoom, 0, Math.PI * 2); ctx.fill();
        }
      }
    }

    const scale = (w / MAP_SIZE) * vs.zoom;

    // 3. 搜尋雲
    const selectedAgv = currentTelemetry.agvs.find(a => a.id === currentSelectedAgvId);
    if (showSearch && selectedAgv?.visited) {
        ctx.fillStyle = 'rgba(0, 255, 255, 0.08)';
        const blockSize = GRID_SIZE * scale;
        const count = revealedIndices.current[selectedAgv.id] || 0;
        for (let i = 0; i < Math.min(count, selectedAgv.visited.length); i++) {
            const node = selectedAgv.visited[i];
            const { cx, cy } = worldToCanvas(node[0] * GRID_SIZE, node[1] * GRID_SIZE, w, h, vs);
            ctx.fillRect(cx - blockSize/2, cy - blockSize/2, blockSize, blockSize);
        }
    }

    // 4. 導航路徑
    if (selectedAgv?.path) {
      ctx.setLineDash([5, 5]);
      ctx.strokeStyle = '#ff4d4d';
      ctx.lineWidth = 2;
      ctx.shadowBlur = 10; ctx.shadowColor = '#ff4d4d';
      ctx.beginPath();
      selectedAgv.path.forEach((p, i) => {
        const cp = worldToCanvas(p[0], p[1], w, h, vs);
        if (i === 0) ctx.moveTo(cp.cx, cp.cy); else ctx.lineTo(cp.cx, cp.cy);
      });
      ctx.stroke();
      ctx.setLineDash([]); ctx.shadowBlur = 0;
    }

    // 5. 障礙物
    currentTelemetry.obstacles.forEach(ob => {
      const { cx, cy } = worldToCanvas(ob.x, ob.y, w, h, vs);
      const isSelected = currentSelectedObId === ob.id;
      ctx.save();
      ctx.translate(cx, cy);
      if (ob.type === 'circle') {
          const r = (ob.radius || 500) * scale;
          ctx.fillStyle = isSelected ? '#ff6600' : '#d4af37';
          ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
          ctx.restore();
          ctx.save(); ctx.translate(cx, cy);
          ctx.strokeStyle = isSelected ? '#fff' : '#ffd700';
          ctx.lineWidth = 1.5 * vs.zoom;
          ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
      } else {
          ctx.rotate(-ob.angle);
          const ow = ob.width * scale, oh = ob.height * scale;
          ctx.fillStyle = isSelected ? '#ff6600' : '#d4af37';
          ctx.fillRect(-ow/2, -oh/2, ow, oh);
          // 補回斜線細節
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
          ctx.beginPath();
          for (let i = -ow; i < ow + oh; i += 10*vs.zoom) { ctx.moveTo(i, -oh/2); ctx.lineTo(i - oh, oh/2); }
          ctx.clip(); ctx.stroke();
          ctx.restore();
          ctx.save(); ctx.translate(cx, cy); ctx.rotate(-ob.angle);
          ctx.strokeStyle = isSelected ? '#fff' : '#ffd700';
          ctx.lineWidth = 1.5 * vs.zoom;
          if (isSelected) { ctx.shadowBlur = 15; ctx.shadowColor = '#ff6600'; }
          ctx.strokeRect(-ow/2, -oh/2, ow, oh);
      }
      ctx.restore();
    });

    // 6. 目標位置
    currentTelemetry.agvs.forEach(a => {
      const isSelected = a.id === currentSelectedAgvId;
      const { cx, cy } = worldToCanvas(a.target.x, a.target.y, w, h, vs);
      ctx.save();
      ctx.translate(cx, cy);
      const pulse = (1 + Math.sin(now / 200) * 0.15) * vs.zoom;
      ctx.strokeStyle = isSelected ? '#39ff14' : '#1b5e20';
      ctx.lineWidth = 2 * vs.zoom;
      ctx.beginPath(); ctx.arc(0, 0, 12 * pulse, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-15*vs.zoom, 0); ctx.lineTo(15*vs.zoom, 0); ctx.moveTo(0, -15*vs.zoom); ctx.lineTo(0, 15*vs.zoom); ctx.stroke();
      ctx.restore();
    });

    // --- 7. 核心優化：AGV ICON 細節補回 ---
    currentTelemetry.agvs.forEach(a => {
      const ds = displayStates.current[a.id];
      if (!ds) return;
      const { cx, cy } = worldToCanvas(ds.x, ds.y, w, h, vs);
      const isSelected = a.id === currentSelectedAgvId;
      const sz = 1000 * scale;

      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(-ds.theta);

      // A. 掃描光束
      if (isSelected) {
          const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, sz * 1.5);
          gradient.addColorStop(0, 'rgba(0, 242, 255, 0.15)');
          gradient.addColorStop(1, 'rgba(0, 242, 255, 0)');
          ctx.fillStyle = gradient;
          ctx.beginPath(); ctx.moveTo(0, 0);
          ctx.arc(0, 0, sz * 1.5, -Math.PI/6, Math.PI/6); ctx.fill();
      }

      // B. 底盤圓角矩形 (增加金屬陰影)
      ctx.fillStyle = '#1a1a1a';
      ctx.strokeStyle = isSelected ? '#00f2ff' : '#555';
      ctx.lineWidth = 2 * vs.zoom;
      if (isSelected) { ctx.shadowBlur = 15; ctx.shadowColor = '#00f2ff'; }
      
      const r = 10 * scale;
      ctx.beginPath();
      ctx.moveTo(-sz/2 + r, -sz/2); ctx.lineTo(sz/2 - r, -sz/2); ctx.quadraticCurveTo(sz/2, -sz/2, sz/2, -sz/2 + r);
      ctx.lineTo(sz/2, sz/2 - r); ctx.quadraticCurveTo(sz/2, sz/2, sz/2 - r, sz/2);
      ctx.lineTo(-sz/2 + r, sz/2); ctx.quadraticCurveTo(-sz/2, sz/2, -sz/2, sz/2 - r);
      ctx.lineTo(-sz/2, -sz/2 + r); ctx.quadraticCurveTo(-sz/2, -sz/2, -sz/2 + r, -sz/2);
      ctx.fill(); ctx.stroke();
      ctx.shadowBlur = 0;

      // C. 左右輪胎
      ctx.fillStyle = '#000';
      ctx.fillRect(-sz/4, -sz/2 - 3*vs.zoom, sz/2, 6*vs.zoom);
      ctx.fillRect(-sz/4, sz/2 - 3*vs.zoom, sz/2, 6*vs.zoom);

      // D. LiDAR 頂蓋與旋轉掃描線
      ctx.beginPath(); ctx.arc(0, 0, sz/4, 0, Math.PI * 2);
      ctx.fillStyle = '#333'; ctx.fill();
      ctx.strokeStyle = isSelected ? '#00f2ff' : '#444';
      ctx.stroke();
      
      const scanAngle = (now / 400) % (Math.PI * 2);
      ctx.beginPath(); ctx.moveTo(0, 0);
      ctx.lineTo(Math.cos(scanAngle)*sz/4, Math.sin(scanAngle)*sz/4);
      ctx.strokeStyle = isSelected ? '#00f2ff' : '#555';
      ctx.lineWidth = 1.5 * vs.zoom;
      ctx.stroke();

      // E. 車頭導航箭頭
      ctx.fillStyle = isSelected ? '#00f2ff' : '#aaa';
      ctx.beginPath();
      ctx.moveTo(sz/2 - 5*vs.zoom, 0);
      ctx.lineTo(sz/2 - 15*vs.zoom, -10*vs.zoom);
      ctx.lineTo(sz/2 - 15*vs.zoom, 10*vs.zoom);
      ctx.fill();

      // F. 狀態 LED (帶發光)
      const ledColor = a.is_running ? '#00ff00' : (a.is_planning ? '#ffc107' : '#ff3333');
      ctx.beginPath(); ctx.arc(-sz/2 + 15*vs.zoom, -sz/2 + 15*vs.zoom, 4*vs.zoom, 0, Math.PI * 2);
      ctx.fillStyle = ledColor;
      ctx.shadowBlur = 8; ctx.shadowColor = ledColor;
      ctx.fill();

      ctx.restore();
      ctx.shadowBlur = 0;
      ctx.fillStyle = '#fff';
      ctx.font = `bold ${Math.max(8, 11 * vs.zoom)}px monospace`;
      ctx.fillText(a.id, cx - 20, cy - sz * 0.7);
    });

    animationFrameId.current = requestAnimationFrame(render);
  }, [worldToCanvas, showSearch, dimensions, viewState]);

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
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={(e) => {
            if (e.altKey) return;
            const canvas = canvasRef.current; if (!canvas) return;
            const rect = canvas.getBoundingClientRect();
            const { x, y } = canvasToWorld(e.clientX - rect.left, e.clientY - rect.top, dimensions.width, dimensions.height, viewState);
            const currentTelemetry = telemetryRef.current;
            const clickedAgv = currentTelemetry?.agvs.find(a => Math.sqrt((a.x-x)**2+(a.y-y)**2) < 1500);
            if (clickedAgv) onAgvSelect(clickedAgv.id);
            else onCanvasClick(x, y);
        }} 
        onDoubleClick={(e) => handleInteraction(e, onCanvasDoubleClick)}
        onContextMenu={(e) => {
            e.preventDefault();
            handleInteraction(e, onCanvasRightClick);
        }} 
      />
      <button style={{ position: 'absolute', bottom: '20px', right: '20px', opacity: 0.6 }} onClick={() => setViewState({ zoom: 1, offsetX: 0, offsetY: 0 })}>
        RESET VIEW
      </button>
    </div>
  );
};

export default SimulatorCanvas;
