import heapq
import math
from typing import List, Tuple, Dict, Any, Optional

class AStarPlanner:
    def __init__(self, map_size=50000, grid_size=200):
        self.map_size = map_size
        self.grid_size = grid_size
        self.nodes_x = map_size // grid_size
        self.nodes_y = map_size // grid_size

    def get_path(self, start: List[float], goal: List[float], obstacles: List[Dict[str, Any]], static_costmap=None, world=None) -> Tuple[List[Tuple[float, float]], List[Tuple[int, int]]]:
        start_grid = (int(round(start[0] / self.grid_size)), int(round(start[1] / self.grid_size)))
        goal_grid = (int(round(goal[0] / self.grid_size)), int(round(goal[1] / self.grid_size)))
        
        # 1. 預過濾動態障礙物：只保留正在移動且非 IDLE 的車輛
        relevant_dyn_geoms = []
        for ob in obstacles:
            oid = ob.get('id', '')
            # 如果對方是待命中的 AGV，在規劃時就「無視」它，逼它避讓
            if world and oid in world.agvs:
                if world.agvs[oid].status == "IDLE":
                    continue 
            
            if ob.get('radius'):
                relevant_dyn_geoms.append((ob['x'], ob['y'], ob['radius']))

        def get_grid_penalty(gx, gy):
            if static_costmap is not None:
                penalty = static_costmap[max(0, min(gx, self.nodes_x-1)), max(0, min(gy, self.nodes_y-1))]
            else: penalty = 0
            if penalty >= 1000000: return penalty
            
            # 加入動態障礙物權重
            wx, wy = gx * self.grid_size, gy * self.grid_size
            for dx, dy, dr in relevant_dyn_geoms:
                d_sq = (wx - dx)**2 + (wy - dy)**2
                if d_sq < (dr + 300)**2: # 稍微加大碰撞範圍
                    penalty += 10000
            return penalty

        queue = [(0, 0, start_grid)]
        came_from = {start_grid: None}
        cost_so_far = {start_grid: 0}
        visited = []

        while queue:
            _, _, current = heapq.heappop(queue)
            visited.append(current)
            if current == goal_grid: break
            
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < self.nodes_x and 0 <= neighbor[1] < self.nodes_y:
                    p = get_grid_penalty(neighbor[0], neighbor[1])
                    if p >= 1000000 and neighbor != goal_grid: continue
                    
                    new_cost = cost_so_far[current] + math.sqrt(dx**2 + dy**2) * self.grid_size + p * 100
                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        h_cost = math.sqrt((goal_grid[0]-neighbor[0])**2 + (goal_grid[1]-neighbor[1])**2) * self.grid_size
                        priority = new_cost + h_cost * 1.001
                        heapq.heappush(queue, (priority, h_cost, neighbor))
                        came_from[neighbor] = current

        if goal_grid not in came_from: return [], visited
        path = []
        curr = goal_grid
        while curr is not None:
            path.append((curr[0]*self.grid_size, curr[1]*self.grid_size))
            curr = came_from[curr]
        path.reverse()

        # 恢復原始穩定平滑
        if len(path) > 5:
            smooth_path = [path[0]]
            for i in range(1, len(path)-1):
                sx = (path[i-1][0] + path[i][0] + path[i+1][0]) / 3.0
                sy = (path[i-1][1] + path[i][1] + path[i+1][1]) / 3.0
                smooth_path.append((sx, sy))
            smooth_path.append(path[-1])
            return smooth_path, visited
            
        return path, visited

    def find_nearest_safe_spot(self, start_pos: Tuple[float, float], static_costmap, threat_paths: List[List[Tuple[float, float]]], repulsion_vec: Tuple[float, float] = None) -> Optional[Tuple[float, float]]:
        """尋找高品質、定向優先且符合 2m 安全原則的避難點。"""
        if static_costmap is None: return None
        
        start_grid = (int(start_pos[0] // self.grid_size), int(start_pos[1] // self.grid_size))
        queue = [start_grid]
        visited = {start_grid}
        max_dist_grids = 15000 // self.grid_size 
        
        # 建立圓形禁區
        threat_grids = set()
        r_grids = 2000 // self.grid_size
        for path in threat_paths:
            for px, py in path:
                tx, ty = int(px // self.grid_size), int(py // self.grid_size)
                for dx in range(-int(r_grids), int(r_grids) + 1):
                    for dy in range(-int(r_grids), int(r_grids) + 1):
                        if dx*dx + dy*dy <= r_grids**2:
                            threat_grids.add((tx + dx, ty + dy))

        # 為了實作「反方向優先」，我們分兩輪搜尋
        # 第一輪：嚴格限制在反方向 (Dot Product > 0)
        # 第二輪：如果第一輪失敗，則開放全方位
        for stage in ["DIRECTED", "FULL"]:
            current_queue = list(queue)
            current_visited = set(visited)
            
            while current_queue:
                gx, gy = current_queue.pop(0)
                wx, wy = gx * self.grid_size, gy * self.grid_size
                
                # 檢查安全原則 (Cost == 0) 與 衝突
                if static_costmap[gx, gy] == 0 and (gx, gy) not in threat_grids:
                    # 定向過濾
                    if stage == "DIRECTED" and repulsion_vec:
                        vx, vy = wx - start_pos[0], wy - start_pos[1]
                        v_mag = math.sqrt(vx**2 + vy**2)
                        if v_mag > 500:
                            dot = (vx/v_mag) * repulsion_vec[0] + (vy/v_mag) * repulsion_vec[1]
                            if dot < 0: continue # 第一輪只找反方向
                    
                    # 足跡驗證 (5x5)
                    is_footprint_safe = True
                    for bx in range(-2, 3):
                        for by in range(-2, 3):
                            ix, iy = gx + bx, gy + by
                            if not (0 <= ix < self.nodes_x and 0 <= iy < self.nodes_y) or static_costmap[ix, iy] > 0:
                                is_footprint_safe = False; break
                        if not is_footprint_safe: break
                    
                    if is_footprint_safe:
                        if (wx - start_pos[0])**2 + (wy - start_pos[1])**2 > 1000**2:
                            return (wx, wy)
                
                # BFS 擴散
                if abs(gx - start_grid[0]) < max_dist_grids and abs(gy - start_grid[1]) < max_dist_grids:
                    for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                        nx, ny = gx + dx, gy + dy
                        if (nx, ny) not in current_visited and 0 <= nx < self.nodes_x and 0 <= ny < self.nodes_y:
                            if static_costmap[nx, ny] < 1000000:
                                current_visited.add((nx, ny))
                                current_queue.append((nx, ny))
        return None
