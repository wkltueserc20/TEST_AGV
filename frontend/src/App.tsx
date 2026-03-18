import { useState, useEffect } from 'react';
import { useSimulation } from './useSimulation';
import type { Telemetry, AGVData } from './useSimulation';
import SimulatorCanvas from './SimulatorCanvas';
import './App.css';

function App() {
  const { telemetry, isConnected, sendCommand } = useSimulation('ws://localhost:8000/ws');
  const [selectedAgvId, setSelectedAgvId] = useState<string | null>(null);
  const [selectedObId, setSelectedObId] = useState<string | null>(null);
  const [addMode, setAddMode] = useState<'rectangle' | 'circle'>('rectangle');

  // 自動選中第一台 AGV
  useEffect(() => {
    if (!selectedAgvId && telemetry?.agvs.length) {
      setSelectedAgvId(telemetry.agvs[0].id);
    }
  }, [telemetry, selectedAgvId]);

  const selectedAgv = telemetry?.agvs.find(a => a.id === selectedAgvId);

  const handleCanvasClick = (x: number, y: number) => {
    if (!telemetry) return;
    const clickedOb = telemetry.obstacles.find(ob => Math.sqrt((ob.x-x)**2+(ob.y-y)**2) < 1000);
    if (clickedOb) { setSelectedObId(clickedOb.id); } 
    else {
      const newOb = addMode === 'rectangle' 
        ? { id: Math.random().toString(36).substr(2,9), type: 'rectangle', x, y, width: 1000, height: 1000, angle: 0 }
        : { id: Math.random().toString(36).substr(2,9), type: 'circle', x, y, radius: 500 };
      sendCommand('add_obstacle', { data: newOb });
      setSelectedObId(null);
    }
  };

  const handleCanvasRightClick = (x: number, y: number) => {
    if (selectedAgvId) sendCommand('set_target', { agv_id: selectedAgvId, data: { x, y } });
  };

  const updateObstacle = (id: string, field: string, value: number) => {
    const ob = telemetry?.obstacles.find(o => o.id === id);
    if (ob) sendCommand('update_obstacle', { data: { ...ob, [field]: value } });
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <h2 style={{ margin: '0 0 10px 0' }}>Multi-AGV V2</h2>
        
        <div className={`status-badge ${isConnected ? 'online' : 'offline'}`}>
          {isConnected ? '● Connected' : '○ Offline'}
        </div>

        <div className="section">
          <h3>Fleet Management</h3>
          <div className="agv-list">
            {telemetry?.agvs.map(a => (
              <div key={a.id} className={`agv-item ${selectedAgvId === a.id ? 'active' : ''}`} onClick={() => setSelectedAgvId(a.id)}>
                <span>AGV: {a.id}</span>
                <button className="small-del" onClick={() => sendCommand('remove_agv', { agv_id: a.id })}>×</button>
              </div>
            ))}
          </div>
          <button className="primary" style={{ width: '100%', marginTop: '10px' }} onClick={() => sendCommand('add_agv', { x: 5000, y: 5000 })}>
            + Add New AGV
          </button>
        </div>

        {selectedAgv && (
          <div className="section control-panel">
            <h3>Control: {selectedAgvId}</h3>
            <div className="btn-group">
              {!selectedAgv.is_running 
                ? <button className="primary" onClick={() => sendCommand('start', { agv_id: selectedAgvId })}>Start</button>
                : <button className="warning" onClick={() => sendCommand('pause', { agv_id: selectedAgvId })}>Pause</button>
              }
              <button className="danger" onClick={() => sendCommand('reset', { agv_id: selectedAgvId })}>Reset</button>
            </div>
            <div style={{ marginTop: '15px' }}>
              <label style={{ fontSize: '12px' }}>Speed Limit: {selectedAgv.max_rpm} RPM</label>
              <input type="range" min="0" max="3000" step="100" value={selectedAgv.max_rpm} 
                onChange={(e) => sendCommand('set_speed', { agv_id: selectedAgvId, data: parseInt(e.target.value) })}
                style={{ width: '100%' }} />
            </div>
          </div>
        )}

        {selectedAgv && (
          <div className="section telemetry-info">
            <h3>AGV Telemetry</h3>
            <div className="grid-info">
              <span>X:</span> <strong>{Math.round(selectedAgv.x)}</strong>
              <span>Y:</span> <strong>{Math.round(selectedAgv.y)}</strong>
              <span>V:</span> <strong>{Math.round(selectedAgv.v)} mm/s</strong>
              <span>ω:</span> <strong>{selectedAgv.omega.toFixed(2)} rad/s</strong>
              <span>L RPM:</span> <strong style={{color: '#007bff'}}>{Math.round(selectedAgv.l_rpm)}</strong>
              <span>R RPM:</span> <strong style={{color: '#28a745'}}>{Math.round(selectedAgv.r_rpm)}</strong>
            </div>
          </div>
        )}

        <div className="section">
          <h3>Obstacles</h3>
          <select value={addMode} onChange={(e) => setAddMode(e.target.value as any)}>
            <option value="rectangle">Square (1m x 1m)</option>
            <option value="circle">Circle (D: 1m)</option>
          </select>
          <button className="secondary" style={{ marginTop: '10px' }} onClick={() => sendCommand('clear_obstacles')}>
            Clear All
          </button>
        </div>
      </div>

      <div className="main-content">
        <SimulatorCanvas 
          telemetry={telemetry} 
          selectedAgvId={selectedAgvId}
          selectedObstacleId={selectedObId}
          onCanvasClick={handleCanvasClick}
          onCanvasRightClick={handleCanvasRightClick}
          onAgvSelect={setSelectedAgvId}
        />
        <div className="hud-info">
          Click AGV to Select | Left-Click: Add Obstacle | Right-Click: Set Target
        </div>
      </div>
    </div>
  );
}

export default App;
