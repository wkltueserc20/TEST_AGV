import { useState, useEffect } from 'react';
import { useSimulation } from './useSimulation';
import type { Telemetry, AGVData } from './useSimulation';
import SimulatorCanvas from './SimulatorCanvas';
import './App.css';

function App() {
  const { telemetry, isConnected, sendCommand } = useSimulation('ws://localhost:8000/ws');
  const [selectedAgvId, setSelectedAgvId] = useState<string | null>(null);
  const [selectedObId, setSelectedObId] = useState<string | null>(null);
  const [addAgvMode, setAddAgvMode] = useState(false);
  const [addMode, setAddMode] = useState<'rectangle' | 'circle'>('rectangle');
  const [showSearch, setShowSearch] = useState(true);

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
    const clickedOb = telemetry.obstacles.find(ob => {
      if (ob.type === 'rectangle') return Math.abs(x - ob.x) <= 500 && Math.abs(y - ob.y) <= 500;
      return Math.sqrt((ob.x - x) ** 2 + (ob.y - y) ** 2) <= (ob.radius || 500);
    });
    if (clickedOb) {
      setSelectedObId(clickedOb.id);
    } else {
      const sx = snapToCenter(x), sy = snapToCenter(y);
      if (!telemetry.obstacles.some(ob => ob.x === sx && ob.y === sy)) {
        const newId = `ob-${Date.now()}-${Math.random().toString(36).substr(2,5)}`;
        const newOb = addMode === 'rectangle' 
          ? { id: newId, type: 'rectangle', x: sx, y: sy, width: 1000, height: 1000, angle: 0 }
          : { id: newId, type: 'circle', x: sx, y: sy, radius: 500 };
        sendCommand('add_obstacle', { data: newOb });
      }
      setSelectedObId(null);
    }
  };

  const handleCanvasDoubleClick = (x: number, y: number) => {
    if (!telemetry) return;
    // 尋找被雙擊的障礙物
    const clickedOb = telemetry.obstacles.find(ob => {
      if (ob.type === 'rectangle') return Math.abs(x - ob.x) <= 500 && Math.abs(y - ob.y) <= 500;
      return Math.sqrt((ob.x - x) ** 2 + (ob.y - y) ** 2) <= (ob.radius || 500);
    });
    if (clickedOb) {
      console.log("Double-click delete:", clickedOb.id);
      sendCommand('remove_obstacle', { id: clickedOb.id });
      if (selectedObId === clickedOb.id) setSelectedObId(null);
    }
  };

  const updateObstacle = (id: string, field: string, value: number) => {
    const ob = telemetry?.obstacles.find(o => o.id === id);
    if (ob) sendCommand('update_obstacle', { data: { ...ob, [field]: (field==='x'||field==='y') ? snapToCenter(value) : value } });
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <h2 style={{ margin: '0 0 10px 0' }}>Multi-AGV Pro</h2>
        <div className={`status-badge ${isConnected ? 'online' : 'offline'}`}>
          {isConnected ? '● SYSTEM CONNECTED' : '○ CONNECTING...'}
        </div>
        <div className="section">
          <h3>Simulation Speed</h3>
          <div className="btn-group-grid">
            {[1, 5, 10, 15].map(m => (
              <button key={m} className={telemetry?.multiplier === m ? 'primary active' : 'secondary'} onClick={() => sendCommand('set_multiplier', { data: m })}>{m}x</button>
            ))}
          </div>
          <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input type="checkbox" id="show-search" checked={showSearch} onChange={(e) => setShowSearch(e.target.checked)} />
            <label htmlFor="show-search" style={{ fontSize: '12px', cursor: 'pointer' }}>Show A* Search Process</label>
          </div>
        </div>
        <div className="section">
          <h3>Fleet Management</h3>
          <div className="agv-list">
            {telemetry?.agvs.map(a => (
              <div key={a.id} className={`agv-item ${selectedAgvId === a.id ? 'active' : ''}`} onClick={() => setSelectedAgvId(a.id)}>
                <div className="agv-item-info">
                  <strong>{a.id}</strong>
                  {a.is_planning ? (
                    <span style={{ fontSize: '10px', color: '#ffc107', fontWeight: 'bold' }}>PLANNING...</span>
                  ) : (
                    <span style={{ fontSize: '10px', opacity: 0.7 }}>{a.is_running ? 'RUNNING' : 'IDLE'}</span>
                  )}
                </div>
                <button className="small-del" onClick={(e) => { e.stopPropagation(); sendCommand('remove_agv', { agv_id: a.id }); }}>×</button>
              </div>
            ))}
          </div>
          <button className={addAgvMode ? 'warning' : 'primary'} style={{ width: '100%', marginTop: '10px' }} onClick={() => setAddAgvMode(!addAgvMode)}>
            {addAgvMode ? 'CANCEL' : '+ ADD AGV'}
          </button>
        </div>
        {selectedAgv && (
          <div className="section control-panel">
            <h3>Control: {selectedAgvId}</h3>
            <div className="btn-group">
              {!selectedAgv.is_running 
                ? <button className="primary" onClick={() => sendCommand('start', { agv_id: selectedAgvId })}>START</button>
                : <button className="warning" onClick={() => sendCommand('pause', { agv_id: selectedAgvId })}>PAUSE</button>
              }
              <button className="danger" onClick={() => sendCommand('reset', { agv_id: selectedAgvId })}>RESET</button>
            </div>
            <div className="telemetry-grid" style={{ marginTop: '15px' }}>
              <div className="tele-item"><span>X:</span><strong>{Math.round(selectedAgv.x)}</strong></div>
              <div className="tele-item"><span>Y:</span><strong>{Math.round(selectedAgv.y)}</strong></div>
              <div className="tele-item"><span>Angle:</span><strong>{radToDeg(selectedAgv.theta)}°</strong></div>
              <div className="tele-item"><span>V:</span><strong>{Math.round(selectedAgv.v)}</strong></div>
              <div className="tele-item"><span>L:</span><strong style={{color: '#007bff'}}>{Math.round(selectedAgv.l_rpm)}</strong></div>
              <div className="tele-item"><span>R:</span><strong style={{color: '#28a745'}}>{Math.round(selectedAgv.r_rpm)}</strong></div>
            </div>
            <div style={{ marginTop: '15px' }}>
              <label style={{ fontSize: '11px', color: '#666' }}>MAX: {selectedAgv.max_rpm} RPM</label>
              <input type="range" min="0" max="3000" step="100" value={selectedAgv.max_rpm} 
                onChange={(e) => sendCommand('set_speed', { agv_id: selectedAgvId, data: parseInt(e.target.value) })}
                style={{ width: '100%' }} />
            </div>
          </div>
        )}
        <div className="section">
          <h3>Obstacle Config</h3>
          <select value={addMode} onChange={(e) => setAddMode(e.target.value as any)} style={{ width: '100%' }}>
            <option value="rectangle">Square (1m x 1m)</option>
            <option value="circle">Circle (D: 1m)</option>
          </select>
          <div className="list-container" style={{ marginTop: '10px' }}>
            {selectedObstacle ? (
              <div className="list-item-detailed active">
                <div className="item-header">
                  <strong>EDIT: {selectedObstacle.type.toUpperCase()}</strong>
                  <button className="small-del" onClick={(e) => {
                    e.stopPropagation();
                    sendCommand('remove_obstacle', { id: selectedObstacle.id });
                    setSelectedObId(null);
                  }}>×</button>
                </div>
                <div className="item-coords">
                  <span>X:</span><input type="number" step="1000" value={Math.round(selectedObstacle.x)} onClick={(e)=>e.stopPropagation()} onChange={(e) => updateObstacle(selectedObstacle.id, 'x', parseInt(e.target.value)||0)} />
                  <span>Y:</span><input type="number" step="1000" value={Math.round(selectedObstacle.y)} onClick={(e)=>e.stopPropagation()} onChange={(e) => updateObstacle(selectedObstacle.id, 'y', parseInt(e.target.value)||0)} />
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '20px', background: '#f9f9f9', borderRadius: '4px', fontSize: '12px', color: '#999' }}>
                Select obstacle to edit
              </div>
            )}
          </div>
          <button className="secondary" style={{ marginTop: '10px', width: '100%' }} onClick={() => sendCommand('clear_obstacles')}>CLEAR ALL</button>
        </div>
      </div>
      <div className="main-content">
        <SimulatorCanvas 
          telemetry={telemetry} 
          selectedAgvId={selectedAgvId}
          selectedObstacleId={selectedObId}
          showSearch={showSearch}
          onCanvasClick={handleCanvasClick}
          onCanvasDoubleClick={handleCanvasDoubleClick}
          onAgvSelect={setSelectedAgvId}
          onCanvasRightClick={(x, y) => {
            const targetId = selectedAgvId || (telemetry?.agvs.length ? telemetry.agvs[0].id : null);
            if (targetId) {
              sendCommand('set_target', { agv_id: targetId, data: { x: snapToIntersection(x), y: snapToIntersection(y) } });
            }
          }}
        />
      </div>
    </div>
  );
}

export default App;
