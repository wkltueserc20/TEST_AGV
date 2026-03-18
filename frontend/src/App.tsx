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

  // 自動同步選中狀態
  useEffect(() => {
    if (telemetry?.agvs.length && !selectedAgvId) {
      setSelectedAgvId(telemetry.agvs[0].id);
    }
  }, [telemetry, selectedAgvId]);

  const selectedAgv = telemetry?.agvs.find(a => a.id === selectedAgvId);

  // 網格吸附函數：將座標對齊到 1000mm 的中心點 (500, 1500, 2500...)
  const snapToGrid = (val: number) => {
    return Math.floor(val / 1000) * 1000 + 500;
  };

  const handleCanvasClick = (x: number, y: number) => {
    if (!telemetry) return;

    // AGV 放置保持自由，不吸附網格
    if (addAgvMode) {
      sendCommand('add_agv', { x, y });
      setAddAgvMode(false);
      return;
    }

    const clickedOb = telemetry.obstacles.find(ob => Math.sqrt((ob.x-x)**2+(ob.y-y)**2) < 1000);
    if (clickedOb) {
      setSelectedObId(clickedOb.id);
    } else {
      // 障礙物放置：啟動網格吸附，確保完美貼齊
      const snappedX = snapToGrid(x);
      const snappedY = snapToGrid(y);

      // 檢查該位置是否已有障礙物 (防止完全重疊放置)
      const isOccupied = telemetry.obstacles.some(ob => ob.x === snappedX && ob.y === snappedY);
      if (isOccupied) return;

      const newOb = addMode === 'rectangle' 
        ? { id: Math.random().toString(36).substr(2,9), type: 'rectangle', x: snappedX, y: snappedY, width: 1000, height: 1000, angle: 0 }
        : { id: Math.random().toString(36).substr(2,9), type: 'circle', x: snappedX, y: snappedY, radius: 500 };
      
      sendCommand('add_obstacle', { data: newOb });
      setSelectedObId(null);
    }
  };

  const updateObstacle = (id: string, field: string, value: number) => {
    const ob = telemetry?.obstacles.find(o => o.id === id);
    if (ob) {
      // 編輯時也進行吸附，確保邏輯一致
      const snappedVal = (field === 'x' || field === 'y') ? snapToGrid(value) : value;
      sendCommand('update_obstacle', { data: { ...ob, [field]: snappedVal } });
    }
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <h2 style={{ margin: '0 0 10px 0' }}>Multi-AGV Pro</h2>
        
        <div className={`status-badge ${isConnected ? 'online' : 'offline'}`}>
          {isConnected ? '● SYSTEM CONNECTED' : '○ CONNECTING...'}
        </div>

        <div className="section">
          <h3>Fleet Management</h3>
          <div className="agv-list">
            {telemetry?.agvs.map(a => (
              <div key={a.id} className={`agv-item ${selectedAgvId === a.id ? 'active' : ''}`} onClick={() => setSelectedAgvId(a.id)}>
                <span>{a.id}</span>
                <button className="small-del" onClick={() => sendCommand('remove_agv', { agv_id: a.id })}>×</button>
              </div>
            ))}
          </div>
          <button className={addAgvMode ? 'warning' : 'primary'} style={{ width: '100%', marginTop: '10px' }} onClick={() => setAddAgvMode(!addAgvMode)}>
            {addAgvMode ? 'CANCEL' : '+ ADD CUSTOM AGV'}
          </button>
        </div>

        {selectedAgv && (
          <div className="section">
            <h3>Control: {selectedAgvId}</h3>
            <div className="btn-group">
              <button className="primary" onClick={() => sendCommand('start', { agv_id: selectedAgvId })}>START</button>
              <button className="warning" onClick={() => sendCommand('pause', { agv_id: selectedAgvId })}>PAUSE</button>
              <button className="danger" onClick={() => sendCommand('reset', { agv_id: selectedAgvId })}>RESET</button>
            </div>
            <div className="telemetry-grid" style={{ marginTop: '10px' }}>
              <div className="tele-item"><span>X:</span><strong>{Math.round(selectedAgv.x)}</strong></div>
              <div className="tele-item"><span>Y:</span><strong>{Math.round(selectedAgv.y)}</strong></div>
              <div className="tele-item"><span>RPM:</span><strong>{Math.round(selectedAgv.l_rpm)}/{Math.round(selectedAgv.r_rpm)}</strong></div>
            </div>
          </div>
        )}

        <div className="section">
          <h3>Obstacle Snapping (1m)</h3>
          <select value={addMode} onChange={(e) => setAddMode(e.target.value as any)} style={{ width: '100%' }}>
            <option value="rectangle">Square (1m x 1m)</option>
            <option value="circle">Circle (D: 1m)</option>
          </select>
          
          <div className="list-container" style={{ marginTop: '10px' }}>
            {telemetry?.obstacles.map(ob => (
              <div key={ob.id} className={`list-item-detailed ${selectedObId === ob.id ? 'active' : ''}`} onClick={() => setSelectedObId(ob.id)}>
                <div className="item-coords">
                  <span>X:</span><input type="number" step="1000" value={Math.round(ob.x)} onClick={(e)=>e.stopPropagation()} onChange={(e) => updateObstacle(ob.id, 'x', parseInt(e.target.value)||0)} />
                  <span>Y:</span><input type="number" step="1000" value={Math.round(ob.y)} onClick={(e)=>e.stopPropagation()} onChange={(e) => updateObstacle(ob.id, 'y', parseInt(e.target.value)||0)} />
                  <button className="small-del" onClick={() => sendCommand('remove_obstacle', { id: ob.id })}>×</button>
                </div>
              </div>
            ))}
          </div>
          
          <button className="secondary" style={{ marginTop: '10px', width: '100%' }} onClick={() => sendCommand('clear_obstacles')}>
            CLEAR ALL
          </button>
        </div>
      </div>

      <div className="main-content">
        <SimulatorCanvas 
          telemetry={telemetry} 
          selectedAgvId={selectedAgvId}
          selectedObstacleId={selectedObId}
          onCanvasClick={handleCanvasClick}
          onAgvSelect={setSelectedAgvId}
          onCanvasRightClick={(x, y) => selectedAgvId && sendCommand('set_target', { agv_id: selectedAgvId, data: { x, y } })}
        />
        <div className="hud-info">
          Obstacles will snap to 1m grid to prevent overlap.
        </div>
      </div>
    </div>
  );
}

export default App;
