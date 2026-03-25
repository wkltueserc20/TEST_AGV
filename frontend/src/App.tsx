import { useState, useEffect } from 'react';
import { useSimulation } from './useSimulation';
import type { Telemetry, AGVData } from './useSimulation';
import SimulatorCanvas from './SimulatorCanvas';
import './App.css';

// 模式定義：SELECT(調測), BUILD_SQ(方塊), BUILD_CIR(圓形), BUILD_STAR(設備), AUTO(物流任務)
type ToolMode = 'SELECT' | 'BUILD_SQ' | 'BUILD_CIR' | 'BUILD_STAR' | 'AUTO';

function App() {
  const { telemetry, isConnected, sendCommand } = useSimulation('ws://localhost:8000/ws');
  const [selectedAgvId, setSelectedAgvId] = useState<string | null>(null);
  const [selectedObId, setSelectedObId] = useState<string | null>(null);
  const [addAgvMode, setAddAgvMode] = useState(false);
  const [activeTool, setActiveTool] = useState<ToolMode>('SELECT');
  const [showSearch, setShowSearch] = useState(true);

  // 本地緩衝狀態
  const [localObFields, setLocalObFields] = useState({ id: "", x: 0, y: 0, angle: 0 });
  const [isEditing, setIsEditing] = useState(false);

  // AUTO 模式狀態管理
  const [autoTaskSource, setAutoTaskSource] = useState<string | null>(null);
  const [lastMissionStatus, setLastMissionStatus] = useState<string | null>(null);

  // 切換模式時重置狀態
  useEffect(() => {
    setAutoTaskSource(null);
    setLastMissionStatus(null);
  }, [activeTool]);

  // 定時清除成功訊息
  useEffect(() => {
    if (lastMissionStatus) {
        const timer = setTimeout(() => setLastMissionStatus(null), 3000);
        return () => clearTimeout(timer);
    }
  }, [lastMissionStatus]);

  const selectedAgv = telemetry?.agvs.find(a => a.id === selectedAgvId);
  const selectedObstacle = telemetry?.obstacles.find(o => o.id === selectedObId);

  // 當選中對象改變時，初始化本地緩衝
  useEffect(() => {
    if (selectedObstacle) {
      setLocalObFields({
        id: selectedObstacle.id,
        x: Math.round(selectedObstacle.x),
        y: Math.round(selectedObstacle.y),
        angle: selectedObstacle.docking_angle || 0
      });
    } else {
      setLocalObFields({ id: "", x: 0, y: 0, angle: 0 });
    }
  }, [selectedObId]);

  // 同步遙測數值
  useEffect(() => {
    if (selectedObstacle && !isEditing) {
      setLocalObFields(prev => {
          if (prev.id !== selectedObstacle.id || 
              Math.abs(prev.x - selectedObstacle.x) > 10 || 
              Math.abs(prev.y - selectedObstacle.y) > 10 ||
              prev.angle !== selectedObstacle.docking_angle) {
              return {
                id: selectedObstacle.id,
                x: Math.round(selectedObstacle.x),
                y: Math.round(selectedObstacle.y),
                angle: selectedObstacle.docking_angle || 0
              };
          }
          return prev;
      });
    }
  }, [telemetry, isEditing]);

  useEffect(() => {
    if (telemetry?.agvs.length && !selectedAgvId) {
      setSelectedAgvId(telemetry.agvs[0].id);
    }
  }, [telemetry, selectedAgvId]);

  const snapToCenter = (val: number) => Math.floor(val / 1000) * 1000 + 500;
  const snapToIntersection = (val: number) => Math.round(val / 1000) * 1000;

  const radToDeg = (rad: number) => {
    let deg = (rad * 180) / Math.PI;
    while (deg < 0) deg += 360;
    return Math.round(deg % 360);
  };

  // 輔助：檢查站點是否被鎖定
  const isStationLocked = (id: string) => {
      return telemetry?.task_queue?.some((t: any) => t.source_id === id || t.target_id === id);
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
    } else if (activeTool === 'AUTO') {
      const clickedEq = telemetry.obstacles.find(ob => 
        ob.type === 'equipment' && Math.sqrt((ob.x - x) ** 2 + (ob.y - y) ** 2) <= 1500
      );
      const clickedAgv = telemetry.agvs.find(a => 
        Math.sqrt((a.x - x) ** 2 + (a.y - y) ** 2) <= 1500
      );

      if (!autoTaskSource) {
          // 第一步：選取一個資源 (站點或 AGV)
          if (clickedEq) {
              if (isStationLocked(clickedEq.id)) {
                  alert(`[卡控] 站點 ${clickedEq.id} 已有任務進行中。`); return;
              }
              setAutoTaskSource(clickedEq.id);
          } else if (clickedAgv) {
              setAutoTaskSource(clickedAgv.id);
          }
      } else {
          // 第二步：完成任務指派
          const sourceIsAgv = telemetry.agvs.some(a => a.id === autoTaskSource);
          
          if (clickedEq) {
              if (clickedEq.id === autoTaskSource) { setAutoTaskSource(null); return; }
              if (isStationLocked(clickedEq.id)) { alert(`[卡控] 站點 ${clickedEq.id} 已被佔用。`); return; }

              if (sourceIsAgv) {
                  // 車 ➔ 站點
                  const agv = telemetry.agvs.find(a => a.id === autoTaskSource);
                  if (agv?.has_goods) {
                      if (clickedEq.has_goods) { alert("[卡控] 站點已有貨，無法卸貨。"); return; }
                      sendCommand('dispatch_task', { source_id: null, target_id: clickedEq.id, agv_id: agv.id });
                      setLastMissionStatus(`🚚 指派 ${agv.id} ➔ ${clickedEq.id} (卸貨)`);
                  } else {
                      if (!clickedEq.has_goods) { alert("[卡控] 站點沒貨，無法取貨。"); return; }
                      sendCommand('dispatch_task', { source_id: clickedEq.id, target_id: null, agv_id: agv.id });
                      setLastMissionStatus(`📦 指派 ${agv.id} ➔ ${clickedEq.id} (取貨)`);
                  }
              } else {
                  // 站點 ➔ 站點 (自動調度)
                  const sEq = telemetry.obstacles.find(o => o.id === autoTaskSource);
                  if (sEq?.has_goods && !clickedEq.has_goods) {
                      sendCommand('dispatch_task', { source_id: autoTaskSource, target_id: clickedEq.id });
                      setLastMissionStatus(`✅ 已建立搬運任務：${autoTaskSource} ➔ ${clickedEq.id}`);
                  } else {
                      alert("[卡控] 搬運任務必須從「有貨站點」到「無貨站點」。");
                  }
              }
              setAutoTaskSource(null);
          } else if (clickedAgv) {
              if (clickedAgv.id === autoTaskSource) { setAutoTaskSource(null); return; }
              if (!sourceIsAgv) {
                  // 站點 ➔ 車 (與 車 ➔ 站點 邏輯相同)
                  const sEq = telemetry.obstacles.find(o => o.id === autoTaskSource);
                  if (sEq?.has_goods) {
                      if (clickedAgv.has_goods) { alert("[卡控] 車身已有貨，無法取貨。"); return; }
                      sendCommand('dispatch_task', { source_id: autoTaskSource, target_id: null, agv_id: clickedAgv.id });
                      setLastMissionStatus(`📦 指派 ${clickedAgv.id} 取貨：${autoTaskSource}`);
                  } else {
                      if (!clickedAgv.has_goods) { alert("[卡控] 車身沒貨，無法卸貨。"); return; }
                      sendCommand('dispatch_task', { source_id: null, target_id: autoTaskSource, agv_id: clickedAgv.id });
                      setLastMissionStatus(`🚚 指派 ${clickedAgv.id} 卸貨：${autoTaskSource}`);
                  }
              }
              setAutoTaskSource(null);
          }
      }
    } else if (activeTool === 'BUILD_SQ' || activeTool === 'BUILD_CIR' || activeTool === 'BUILD_STAR') {
      const sx = snapToCenter(x), sy = snapToCenter(y);
      if (!telemetry.obstacles.some(ob => ob.x === sx && ob.y === sy)) {
        if (activeTool === 'BUILD_STAR') {
            const newId = `EQP-${Math.random().toString(36).substr(2, 4).toUpperCase()}`;
            const newOb = { id: newId, type: 'equipment', x: sx, y: sy, radius: 1000, status: 'running', docking_angle: 0, has_goods: false };
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

  const handleCommit = (field?: string, value?: any) => {
    if (!selectedObstacle) return;
    const dataToSync = { ...localObFields };
    if (field && value !== undefined) (dataToSync as any)[field] = value;
    if (dataToSync.id !== selectedObstacle.id) {
        if (telemetry?.obstacles.some(o => o.id === dataToSync.id && o.id !== selectedObstacle.id)) {
            alert("ID already exists!"); setLocalObFields(prev => ({ ...prev, id: selectedObstacle.id })); return;
        }
        sendCommand('update_obstacle', { data: { old_id: selectedObstacle.id, new_id: dataToSync.id } });
        setSelectedObId(dataToSync.id);
    } else {
        sendCommand('update_obstacle', { data: { ...selectedObstacle, x: snapToCenter(dataToSync.x), y: snapToCenter(dataToSync.y), docking_angle: dataToSync.angle } });
    }
  };

  const getAutoHint = () => {
      if (!autoTaskSource) return "【步驟 1/2】請點選一個「設備」或「AGV」作為任務起點";
      const source = telemetry?.obstacles.find(o => o.id === autoTaskSource) || telemetry?.agvs.find(a => a.id === autoTaskSource);
      const isAgv = telemetry?.agvs.some(a => a.id === autoTaskSource);
      
      if (isAgv) {
          return `【步驟 2/2】已選車輛：${autoTaskSource} (${(source as any).has_goods ? '載貨中' : '空車'})。請點選一個站點執行${(source as any).has_goods ? '卸貨' : '取貨'}`;
      } else {
          return `【步驟 2/2】已選站點：${autoTaskSource} (${(source as any).has_goods ? '有貨' : '沒貨'})。請點選「另一個站點」或「一台 AGV」完成指派`;
      }
  };

  return (
    <div className="app-container">
      <div className="sidebar left-wing">
        <h2>Multi-AGV Pro</h2>
        <div className="section">
          <h3>System Control</h3>
          <div className={`status-badge ${isConnected ? 'online' : 'offline'}`}>{isConnected ? '● CONNECTED' : '○ DISCONNECTED'}</div>
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
                  <span>{a.id} {a.has_goods ? '📦' : ''}</span>
                  <span style={{ fontSize: '10px', fontWeight: 'bold', color: a.status === 'EXECUTING' ? '#39ff14' : a.status === 'PLANNING' ? '#ffc107' : a.status === 'EVADING' ? '#bb86fc' : a.status === 'STUCK' ? '#ff4d4d' : '#8b949e' }}>
                    {a.status}
                  </span>
                </div>
                <div style={{ marginTop: '8px', display: 'flex', gap: '5px' }}>
                  <button style={{ flex: 1, fontSize: '9px', padding: '4px 2px', background: '#30363d', color: '#c9d1d9', border: '1px solid #444' }} onClick={(e) => { e.stopPropagation(); sendCommand('force_idle', { target_id: a.id }); }}>FORCE IDLE</button>
                  <button style={{ flex: 1, fontSize: '9px', padding: '4px 2px', background: '#30363d', color: '#c9d1d9', border: '1px solid #444' }} onClick={(e) => { e.stopPropagation(); sendCommand(a.is_running ? 'pause' : 'start', { target_id: a.id }); }}>{a.is_running ? 'PAUSE' : 'START'}</button>
                </div>
              </div>
            ))}

          </div>
          <button className={`primary ${addAgvMode ? 'warning' : ''}`} style={{ width: '100%', marginTop: '10px' }} onClick={() => setAddAgvMode(!addAgvMode)}>
            {addAgvMode ? 'CANCEL' : '+ DEPLOY NEW AGV'}
          </button>
        </div>

        <div className="section" style={{ borderTop: '1px solid #30363d', paddingTop: '15px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h3 style={{ margin: 0 }}>任務隊列 ({telemetry?.task_queue?.length || 0})</h3>
            {telemetry?.task_queue?.length > 0 && <button style={{ fontSize: '9px', padding: '2px 6px', opacity: 0.6 }} onClick={() => sendCommand('clear_tasks', {})}>CLEAR</button>}
          </div>
          <div className="fleet-list">
            {telemetry?.task_queue?.length ? telemetry.task_queue.map((t: any) => (
              <div key={t.id} className="item-card" style={{ padding: '10px', borderLeft: t.status === 'ASSIGNED' ? '3px solid #39ff14' : '3px solid #8b949e' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: '11px', color: '#c9d1d9', fontWeight: 'bold' }}>{t.source_id || 'AGV'} ➔ {t.target_id || 'AGV'}</span>
                    <button style={{ background: 'transparent', border: 'none', color: '#ff4d4d', cursor: 'pointer', padding: '0 4px', fontSize: '12px' }} onClick={(e) => { e.stopPropagation(); sendCommand('remove_task', { task_id: t.id }); }}>✕</button>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '9px', padding: '2px 4px', borderRadius: '4px', background: t.status === 'ASSIGNED' ? 'rgba(57, 255, 20, 0.1)' : 'rgba(139, 148, 158, 0.1)', color: t.status === 'ASSIGNED' ? '#39ff14' : '#8b949e' }}>{t.status}</span>
                    {t.agv_id && <div style={{ fontSize: '9px', color: '#58a6ff' }}>車輛: {t.agv_id}</div>}
                </div>
              </div>
            )) : <div style={{ textAlign: 'center', padding: '10px', color: '#8b949e', fontSize: '11px' }}>目前無等待中任務</div>}
          </div>
        </div>

        <div className="section" style={{ borderTop: '1px solid #30363d', paddingTop: '15px', marginTop: '10px' }}>
          <h3>任務歷史 ({telemetry?.task_history?.length || 0})</h3>
          <div className="fleet-list" style={{ maxHeight: '200px', overflowY: 'auto' }}>
            {telemetry?.task_history?.length ? telemetry.task_history.map((t: any) => (
              <div key={t.id} className="item-card" style={{ padding: '8px', opacity: 0.8, marginBottom: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '10px', color: '#8b949e' }}>{t.source_id || 'AGV'} ➔ {t.target_id || 'AGV'}</span>
                    <span style={{ fontSize: '9px', color: '#39ff14', fontWeight: 'bold' }}>✓ DONE</span>
                </div>
                {t.agv_id && <div style={{ fontSize: '8px', color: '#58a6ff', marginTop: '2px' }}>執行車輛: {t.agv_id}</div>}
              </div>
            )) : <div style={{ textAlign: 'center', padding: '10px', color: '#8b949e', fontSize: '11px' }}>暫無歷史紀錄</div>}
          </div>
        </div>

        {selectedObstacle && (
          <div className="section" style={{ borderTop: '1px solid #30363d', paddingTop: '15px' }}>
            <h3>Settings: {selectedObstacle.type === 'equipment' ? 'Equipment' : 'Object'}</h3>
            <div className="item-card active">
              <div className="telemetry-grid">
                <div className="tele-item"><label>ID</label>
                    <input type="text" value={localObFields.id} onFocus={() => setIsEditing(true)} onChange={(e) => setLocalObFields(prev => ({ ...prev, id: e.target.value }))} onBlur={() => { handleCommit(); setIsEditing(false); }} onKeyDown={(e) => e.key === 'Enter' && handleCommit()} />
                </div>
                {selectedObstacle.type === 'equipment' && (
                    <>
                    <div className="tele-item"><label>STATUS</label>
                        <select value={selectedObstacle.status || 'running'} onChange={(e) => sendCommand('update_obstacle', { data: { ...selectedObstacle, status: e.target.value } })}>
                            <option value="normal">NORMAL</option>
                            <option value="running">RUNNING</option>
                            <option value="error">ERROR</option>
                        </select>
                    </div>
                    <div className="tele-item"><label>CARGO</label>
                        <button className={selectedObstacle.has_goods ? 'warning' : 'primary'} style={{ height: '24px', fontSize: '10px', padding: '0 8px' }} onClick={() => sendCommand('update_obstacle', { data: { ...selectedObstacle, has_goods: !selectedObstacle.has_goods } })}>
                            {selectedObstacle.has_goods ? '■ LOADED' : '□ EMPTY'}
                        </button>
                    </div>
                    <div className="tele-item"><label>ANGLE</label>
                        <input type="number" min="0" max="359" value={localObFields.angle} onFocus={() => setIsEditing(true)} onChange={(e) => setLocalObFields(prev => ({ ...prev, angle: parseInt(e.target.value)||0 }))} onBlur={() => { handleCommit(); setIsEditing(false); }} onKeyDown={(e) => e.key === 'Enter' && handleCommit()} />
                    </div>
                    </>
                )}
                <div className="tele-item"><label>X</label>
                  <input type="number" step="1000" value={localObFields.x} onFocus={() => setIsEditing(true)} onChange={(e) => setLocalObFields(prev => ({ ...prev, x: parseInt(e.target.value)||0 }))} onBlur={() => { handleCommit(); setIsEditing(false); }} onKeyDown={(e) => e.key === 'Enter' && handleCommit()} />
                </div>
                <div className="tele-item"><label>Y</label>
                  <input type="number" step="1000" value={localObFields.y} onFocus={() => setIsEditing(true)} onChange={(e) => setLocalObFields(prev => ({ ...prev, y: parseInt(e.target.value)||0 }))} onBlur={() => { handleCommit(); setIsEditing(false); }} onKeyDown={(e) => e.key === 'Enter' && handleCommit()} />
                </div>
              </div>
              <button className="danger" style={{ width: '100%', marginTop: '10px' }} onClick={() => { sendCommand('remove_obstacle', { id: selectedObstacle.id }); setSelectedObId(null); }}>DELETE</button>
            </div>
          </div>
        )}

        {selectedAgv && (
          <div className="section" style={{ borderTop: '1px solid #30363d', paddingTop: '15px' }}>
            <h3>AGV Limits: {selectedAgv.id}</h3>
            <div style={{ marginTop: '5px' }}>
              <label style={{ fontSize: '10px', color: '#8b949e' }}>DRIVE LIMIT: {selectedAgv.max_rpm} RPM</label>
              <input type="range" min="0" max="3000" step="100" value={selectedAgv.max_rpm} onChange={(e) => sendCommand('set_speed', { agv_id: selectedAgvId, data: parseInt(e.target.value) })} style={{ width: '100%', accentColor: '#58a6ff' }} />
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
            <button className={activeTool === 'AUTO' ? 'active' : ''} onClick={() => setActiveTool('AUTO')}>🤖 AUTO</button>
            <button className={activeTool === 'BUILD_STAR' ? 'active' : ''} onClick={() => setActiveTool('BUILD_STAR')}>⭐ EQUIPMENT</button>
            <button className={activeTool === 'BUILD_SQ' ? 'active' : ''} onClick={() => setActiveTool('BUILD_SQ')}>🧱 SQUARE</button>
            <button className={activeTool === 'BUILD_CIR' ? 'active' : ''} onClick={() => setActiveTool('BUILD_CIR')}>⭕ CIRCLE</button>
          </div>
          <div className="toolbar-center">
            {selectedAgv && (
              <div className="agv-quick-controls">
                {!selectedAgv.is_running ? <button className="primary" onClick={() => sendCommand('start', { agv_id: selectedAgvId })}>▶ START</button> : <button className="warning" onClick={() => sendCommand('pause', { agv_id: selectedAgvId })}>⏸ PAUSE</button>}
                <button className="danger" onClick={() => sendCommand('reset', { agv_id: selectedAgvId })}>🔄 RESET</button>
              </div>
            )}
          </div>
          <div className="toolbar-right">
            <div className={`status-badge ${isConnected ? 'online' : 'offline'}`} style={{ border: 'none', background: 'transparent' }}>{isConnected ? 'SIGNAL OK' : 'NO SIGNAL'}</div>
          </div>
        </div>

        <div className="mode-status-bar">
            {lastMissionStatus ? <span style={{ color: '#39ff14', fontWeight: 'bold' }}>{lastMissionStatus}</span> : activeTool === 'AUTO' ? <span className="animate-pulse">{getAutoHint()}</span> : activeTool === 'SELECT' ? <span>模式：手動調測 | 選取物件查看屬性，或使用「右鍵」設定導航目標點。</span> : <span>建築模式：點擊畫布空白處新增物件，雙擊物件可直接刪除。</span>}
        </div>

        <div className="canvas-container">
          <SimulatorCanvas telemetry={telemetry} selectedAgvId={selectedAgvId} selectedObstacleId={selectedObId} autoTaskSourceId={autoTaskSource} showSearch={showSearch} onCanvasClick={handleCanvasClick} onCanvasDoubleClick={handleCanvasDoubleClick} onAgvSelect={(id) => { setSelectedAgvId(id); setSelectedObId(null); }} onCanvasRightClick={(x, y) => {
              const targetId = selectedAgvId || (telemetry?.agvs.length ? telemetry.agvs[0].id : null);
              if (!targetId || !telemetry) return;
              const clickedEq = telemetry.obstacles.find(ob => ob.type === 'equipment' && Math.sqrt((ob.x - x) ** 2 + (ob.y - y) ** 2) < (ob.radius || 1000));
              const targetX = clickedEq ? clickedEq.x : snapToIntersection(x);
              const targetY = clickedEq ? clickedEq.y : snapToIntersection(y);
              sendCommand('set_target', { agv_id: targetId, data: { x: targetX, y: targetY } });
            }} />
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
                <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#39ff14' }}>X: {selectedAgv.target.x} Y: {selectedAgv.target.y}</div>
            </div>
          </div>
        ) : <div style={{ textAlign: 'center', padding: '40px 20px', color: '#8b949e', fontSize: '12px' }}>Select an AGV to monitor real-time telemetry</div>}
      </div>
    </div>
  );
}

export default App;
