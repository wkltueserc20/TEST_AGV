import { useState, useEffect } from 'react';
import { useSimulation } from './useSimulation';
import type { Telemetry, AGVData } from './useSimulation';
import SimulatorCanvas from './SimulatorCanvas';
import './App.css';

// 移除 NAV 模式，目標設定改為全域右鍵功能
type ToolMode = 'SELECT' | 'BUILD_SQ' | 'BUILD_CIR' | 'BUILD_STAR';

function App() {
  const { telemetry, isConnected, sendCommand } = useSimulation('ws://localhost:8000/ws');
  const [selectedAgvId, setSelectedAgvId] = useState<string | null>(null);
  const [selectedObId, setSelectedObId] = useState<string | null>(null);
  const [addAgvMode, setAddAgvMode] = useState(false);
  const [activeTool, setActiveTool] = useState<ToolMode>('SELECT');
  const [showSearch, setShowSearch] = useState(true);

  const [editingId, setEditingId] = useState("");

  useEffect(() => {
    if (selectedObstacle) setEditingId(selectedObstacle.id);
  }, [selectedObId]);

  useEffect(() => {
    if (telemetry?.agvs.length && !selectedAgvId) {
      setSelectedAgvId(telemetry.agvs[0].id);
    }
  }, [telemetry, selectedAgvId]);

  const selectedAgv = telemetry?.agvs.find(a => a.id === selectedAgvId);
  const selectedObstacle = telemetry?.obstacles.find(o => o.id === selectedObId);

  const snapToCenter = (val: number) => Math.floor(val / 1000) * 1000 + 500;
  const snapToIntersection = (val: number) => Math.round(val / 1000) * 1000;

  const radToDeg = (rad: number) => {
    let deg = (rad * 180) / Math.PI;
    while (deg < 0) deg += 360;
    return Math.round(deg % 360);
  };

  const handleCanvasClick = (x: number, y: number) => {
    if (!telemetry) return;

    if (addAgvMode) {
      sendCommand('add_agv', { x: snapToIntersection(x), y: snapToIntersection(y) });
      setAddAgvMode(false);
      return;
    }

    if (activeTool === 'SELECT') {
      const clickedOb = telemetry.obstacles.find(ob => {
        if (ob.type === 'rectangle') return Math.abs(x - ob.x) <= 500 && Math.abs(y - ob.y) <= 500;
        if (ob.type === 'equipment') return Math.sqrt((ob.x - x) ** 2 + (ob.y - y) ** 2) <= (ob.radius || 1000);
        return Math.sqrt((ob.x - x) ** 2 + (ob.y - y) ** 2) <= (ob.radius || 500);
      });
      if (clickedOb) {
        setSelectedObId(clickedOb.id);
        setSelectedAgvId(null);
      } else {
        setSelectedObId(null);
      }
    } else if (activeTool === 'BUILD_SQ' || activeTool === 'BUILD_CIR' || activeTool === 'BUILD_STAR') {
      const sx = snapToCenter(x), sy = snapToCenter(y);
      if (!telemetry.obstacles.some(ob => ob.x === sx && ob.y === sy)) {
        if (activeTool === 'BUILD_STAR') {
            const newId = `EQP-${Math.random().toString(36).substr(2, 4).toUpperCase()}`;
            const newOb = { id: newId, type: 'equipment', x: sx, y: sy, radius: 1000, status: 'running', docking_angle: 0 };
            sendCommand('add_obstacle', { data: newOb });
        } else {
            const newId = `ob-${Date.now()}-${Math.random().toString(36).substr(2,5)}`;
            const newOb = activeTool === 'BUILD_SQ' 
              ? { id: newId, type: 'rectangle', x: sx, y: sy, width: 1000, height: 1000, angle: 0 }
              : { id: newId, type: 'circle', x: sx, y: sy, radius: 500 };
            sendCommand('add_obstacle', { data: newOb });
        }
      }
    }
  };

  const handleCanvasDoubleClick = (x: number, y: number) => {
    if (!telemetry) return;
    if (activeTool !== 'BUILD_SQ' && activeTool !== 'BUILD_CIR' && activeTool !== 'BUILD_STAR') return;

    const clickedOb = telemetry.obstacles.find(ob => {
      if (ob.type === 'rectangle') return Math.abs(x - ob.x) <= 500 && Math.abs(y - ob.y) <= 500;
      if (ob.type === 'equipment') return Math.sqrt((ob.x - x) ** 2 + (ob.y - y) ** 2) <= (ob.radius || 1000);
      return Math.sqrt((ob.x - x) ** 2 + (ob.y - y) ** 2) <= (ob.radius || 500);
    });
    if (clickedOb) {
      sendCommand('remove_obstacle', { id: clickedOb.id });
      if (selectedObId === clickedOb.id) setSelectedObId(null);
    }
  };

  const updateObstacle = (id: string, field: string, value: any) => {
    const ob = telemetry?.obstacles.find(o => o.id === id);
    if (!ob) return;
    
    if (field === 'new_id') {
        if (telemetry?.obstacles.some(o => o.id === value && o.id !== id)) {
            alert("ID already exists!"); return;
        }
        sendCommand('update_obstacle', { data: { old_id: id, new_id: value } });
        setSelectedObId(value);
    } else {
        sendCommand('update_obstacle', { data: { ...ob, [field]: (field==='x'||field==='y') ? snapToCenter(value) : value } });
    }
  };

  return (
    <div className="app-container">
      <div className="sidebar left-wing">
        <h2>Multi-AGV Pro</h2>
        
        <div className="section">
          <h3>System Control</h3>
          <div className={`status-badge ${isConnected ? 'online' : 'offline'}`}>
            {isConnected ? '● CONNECTED' : '○ DISCONNECTED'}
          </div>
          <div className="btn-group-grid">
            {[1, 10, 20, 30].map(m => (
              <button key={m} className={telemetry?.multiplier === m ? 'primary' : ''} onClick={() => sendCommand('set_multiplier', { data: m })}>{m}x</button>
            ))}
          </div>
          <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input type="checkbox" id="show-search" checked={showSearch} onChange={(e) => setShowSearch(e.target.checked)} />
            <label htmlFor="show-search" style={{ fontSize: '11px', color: '#8b949e', cursor: 'pointer' }}>Search Debug Layer</label>
          </div>
        </div>

        <div className="section">
          <h3>Fleet Status ({telemetry?.agvs.length || 0})</h3>
          <div className="fleet-list">
            {telemetry?.agvs.map(a => (
              <div key={a.id} className={`item-card ${selectedAgvId === a.id ? 'active' : ''}`} onClick={() => { setSelectedAgvId(a.id); setSelectedObId(null); }}>
                <div className="item-header">
                  <span>{a.id}</span>
                  <span style={{ 
                    fontSize: '10px', 
                    fontWeight: 'bold',
                    color: a.status === 'EXECUTING' ? '#39ff14' : 
                           a.status === 'PLANNING' ? '#ffc107' : 
                           a.status === 'EVADING' ? '#bb86fc' :
                           a.status === 'STUCK' ? '#ff4d4d' : '#8b949e' 
                  }}>
                    {a.status === 'EXECUTING' ? 'EXECUTING' :
                     a.status === 'PLANNING' ? 'THINKING' :
                     a.status === 'EVADING' ? 'EVADING PATH' :
                     a.status === 'STUCK' ? 'BLOCKED' : 'STANDBY'}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <button className={`primary ${addAgvMode ? 'warning' : ''}`} style={{ width: '100%', marginTop: '10px' }} onClick={() => setAddAgvMode(!addAgvMode)}>
            {addAgvMode ? 'CANCEL' : '+ DEPLOY NEW AGV'}
          </button>
        </div>

        {selectedObstacle && (
          <div className="section" style={{ borderTop: '1px solid #30363d', paddingTop: '15px' }}>
            <h3>Settings: {selectedObstacle.type === 'equipment' ? 'Equipment' : 'Object'}</h3>
            <div className="item-card active">
              <div className="telemetry-grid">
                <div className="tele-item"><label>ID</label>
                    <input type="text" value={editingId} 
                        onChange={(e) => setEditingId(e.target.value)} 
                        onBlur={() => editingId !== selectedObstacle.id && updateObstacle(selectedObstacle.id, 'new_id', editingId)}
                        onKeyDown={(e) => e.key === 'Enter' && updateObstacle(selectedObstacle.id, 'new_id', editingId)}
                    />
                </div>
                {selectedObstacle.type === 'equipment' && (
                    <>
                    <div className="tele-item"><label>STATUS</label>
                        <select value={selectedObstacle.status || 'running'} onChange={(e) => updateObstacle(selectedObstacle.id, 'status', e.target.value)}>
                            <option value="normal">NORMAL</option>
                            <option value="running">RUNNING</option>
                            <option value="error">ERROR</option>
                        </select>
                    </div>
                    <div className="tele-item"><label>ANGLE</label>
                        <input type="number" min="0" max="359" value={selectedObstacle.docking_angle || 0} 
                            onChange={(e) => updateObstacle(selectedObstacle.id, 'docking_angle', parseInt(e.target.value)||0)} />
                    </div>
                    </>
                )}
                <div className="tele-item"><label>X</label>
                  <input type="number" step="1000" value={Math.round(selectedObstacle.x)} onChange={(e) => updateObstacle(selectedObstacle.id, 'x', parseInt(e.target.value)||0)} />
                </div>
                <div className="tele-item"><label>Y</label>
                  <input type="number" step="1000" value={Math.round(selectedObstacle.y)} onChange={(e) => updateObstacle(selectedObstacle.id, 'y', parseInt(e.target.value)||0)} />
                </div>
              </div>
              <button className="danger" style={{ width: '100%', marginTop: '10px' }} 
                onClick={() => { sendCommand('remove_obstacle', { id: selectedObstacle.id }); setSelectedObId(null); }}>DELETE</button>
            </div>
          </div>
        )}

        {selectedAgv && (
          <div className="section" style={{ borderTop: '1px solid #30363d', paddingTop: '15px' }}>
            <h3>AGV Limits: {selectedAgv.id}</h3>
            <div style={{ marginTop: '5px' }}>
              <label style={{ fontSize: '10px', color: '#8b949e' }}>DRIVE LIMIT: {selectedAgv.max_rpm} RPM</label>
              <input type="range" min="0" max="3000" step="100" value={selectedAgv.max_rpm} 
                onChange={(e) => sendCommand('set_speed', { agv_id: selectedAgvId, data: parseInt(e.target.value) })}
                style={{ width: '100%', accentColor: '#58a6ff' }} />
            </div>
            <button className="danger" style={{ width: '100%', marginTop: '20px', opacity: 0.6 }} onClick={() => sendCommand('remove_agv', { agv_id: selectedAgvId })}>REMOVE AGV</button>
          </div>
        )}

        <div className="section">
          <h3>Global Cleanup</h3>
          <button className="danger" style={{ width: '100%' }} onClick={() => sendCommand('clear_obstacles')}>WIPE ALL OBSTACLES</button>
        </div>
      </div>

      <div className="main-viewport">
        <div className="toolbar-container">
          <div className="toolbar-left">
            <button className={activeTool === 'SELECT' ? 'active' : ''} onClick={() => setActiveTool('SELECT')}>🔍 SELECT</button>
            <button className={activeTool === 'BUILD_STAR' ? 'active' : ''} onClick={() => setActiveTool('BUILD_STAR')}>⭐ EQUIPMENT</button>
            <button className={activeTool === 'BUILD_SQ' ? 'active' : ''} onClick={() => setActiveTool('BUILD_SQ')}>🧱 SQUARE</button>
            <button className={activeTool === 'BUILD_CIR' ? 'active' : ''} onClick={() => setActiveTool('BUILD_CIR')}>⭕ CIRCLE</button>
          </div>
          <div className="toolbar-center">
            {selectedAgv && (
              <div className="agv-quick-controls">
                {!selectedAgv.is_running 
                  ? <button className="primary" onClick={() => sendCommand('start', { agv_id: selectedAgvId })}>▶ START</button>
                  : <button className="warning" onClick={() => sendCommand('pause', { agv_id: selectedAgvId })}>⏸ PAUSE</button>
                }
                <button className="danger" onClick={() => sendCommand('reset', { agv_id: selectedAgvId })}>🔄 RESET</button>
              </div>
            )}
          </div>
          <div className="toolbar-right">
            <span className="toolbar-hint">Right-click to set target</span>
          </div>
        </div>

        <div className="canvas-container">
          <SimulatorCanvas 
            telemetry={telemetry} 
            selectedAgvId={selectedAgvId}
            selectedObstacleId={selectedObId}
            showSearch={showSearch}
            onCanvasClick={handleCanvasClick}
            onCanvasDoubleClick={handleCanvasDoubleClick}
            onAgvSelect={(id) => { setSelectedAgvId(id); setSelectedObId(null); }}
            onCanvasRightClick={(x, y) => {
              const targetId = selectedAgvId || (telemetry?.agvs.length ? telemetry.agvs[0].id : null);
              if (!targetId || !telemetry) return;
              const clickedEq = telemetry.obstacles.find(ob => 
                ob.type === 'equipment' && Math.sqrt((ob.x - x) ** 2 + (ob.y - y) ** 2) < (ob.radius || 1000)
              );
              const targetX = clickedEq ? clickedEq.x : snapToIntersection(x);
              const targetY = clickedEq ? clickedEq.y : snapToIntersection(y);
              sendCommand('set_target', { agv_id: targetId, data: { x: targetX, y: targetY } });
            }}
          />
        </div>
      </div>

      <div className="sidebar right-wing">
        <h2>Telemetry</h2>
        {selectedAgv ? (
          <div className="section">
            <h3>Status: {selectedAgv.id}</h3>
            <div className="telemetry-grid">
              <div className="tele-item"><label>POS X</label><span>{Math.round(selectedAgv.x)}mm</span></div>
              <div className="tele-item"><label>POS Y</label><span>{Math.round(selectedAgv.y)}mm</span></div>
              <div className="tele-item"><label>HEAD</label><span>{radToDeg(selectedAgv.theta)}°</span></div>
              <div className="tele-item"><label>VEL</label><span>{Math.round(selectedAgv.v)}mm/s</span></div>
              <div className="tele-item"><label>L_RPM</label><span style={{color: 'var(--accent-blue)'}}>{Math.round(selectedAgv.l_rpm)}</span></div>
              <div className="tele-item"><label>R_RPM</label><span style={{color: 'var(--accent-green)'}}>{Math.round(selectedAgv.r_rpm)}</span></div>
            </div>
            <div className="item-card" style={{ marginTop: '20px', borderColor: 'rgba(57, 255, 20, 0.2)' }}>
                <div style={{ fontSize: '11px', color: '#8b949e', marginBottom: '8px' }}>Active Target</div>
                <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#39ff14' }}>
                    X: {selectedAgv.target.x} Y: {selectedAgv.target.y}
                </div>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: '#8b949e', fontSize: '12px' }}>
            Select an AGV to monitor real-time telemetry
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
