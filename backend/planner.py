import heapq
import math
from typing import List, Tuple, Dict, Any

class AStarPlanner:
    def __init__(self, map_size=50000, grid_size=200):
        self.map_size = map_size
        self.grid_size = grid_size
        self.nodes_x = map_size // grid_size
        self.nodes_y = map_size // grid_size

    def get_path(self, start: List[float], goal: List[float], obstacles: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
        """計算全局路徑 - 採用幾何倒角實現絕對穩定的圓弧"""
        
        # 1. 對齊網格
        start_grid = (int(round(start[0] / self.grid_size)), int(round(start[1] / self.grid_size)))
        goal_grid = (int(round(goal[0] / self.grid_size)), int(round(goal[1] / self.grid_size)))
        
        obs_geoms = []
        for ob in obstacles:
            ox, oy = ob['x'], ob['y']
            w, h = ob.get('width', 1000), ob.get('height', 1000)
            r = ob.get('radius', 500)
            if ob['type'] == 'rectangle':
                obs_geoms.append(('rect', [ox - w/2, oy - h/2, ox + w/2, oy + h/2]))
            else:
                obs_geoms.append(('circle', [ox, oy, r]))

        def get_grid_penalty(gx, gy):
            wx, wy = gx * self.grid_size, gy * self.grid_size
            min_dist = min(wx, self.map_size - wx, wy, self.map_size - wy)
            is_blocked = False
            for kind, data in obs_geoms:
                if kind == 'rect':
                    dx = max(data[0] - wx, 0, wx - data[2])
                    dy = max(data[1] - wy, 0, wy - data[3])
                    d = math.sqrt(dx**2 + dy**2)
                else:
                    d = math.sqrt((wx - data[0])**2 + (wy - data[1])**2) - data[2]
                if d <= 0: is_blocked = True; break
                if d < min_dist: min_dist = d
            
            if is_blocked or min_dist < 550: return 1000000.0
            if min_dist < 2000: return (2000.0 / min_dist) ** 4
            return 0

        # --- A* 搜尋核心 ---
        # 佇列結構改為 (Priority, H_cost, Node) 來防止 Python 使用 Node 座標進行偏見排序
        queue = [(0, 0, start_grid)]
        came_from = {start_grid: None}
        cost_so_far = {start_grid: 0}

        while queue:
            _, _, current = heapq.heappop(queue)
            if current == goal_grid: break
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < self.nodes_x and 0 <= neighbor[1] < self.nodes_y:
                    p = get_grid_penalty(neighbor[0], neighbor[1])
                    if p >= 1000000 and neighbor != goal_grid: continue
                    
                    new_cost = cost_so_far[current] + math.sqrt(dx**2 + dy**2) * self.grid_size + p * 100
                    
                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        
                        # Tie-Breaker 1: 優先選擇離目標更近的點
                        h_cost = math.sqrt((goal_grid[0]-neighbor[0])**2 + (goal_grid[1]-neighbor[1])**2) * self.grid_size
                        
                        # Tie-Breaker 2: Heuristic Inflation (微幅放大預估值 0.1%)
                        # 這會打破平手僵局，強迫演算法果斷朝目標前進，大幅減少擴展節點數，且消除方向性偏差
                        priority = new_cost + h_cost * 1.001
                        
                        heapq.heappush(queue, (priority, h_cost, neighbor))
                        came_from[neighbor] = current

        if goal_grid not in came_from: return []
        
        path = []
        curr = goal_grid
        while curr is not None:
            path.append((curr[0]*self.grid_size, curr[1]*self.grid_size))
            curr = came_from[curr]
        path.reverse()

        # --- 2. 幾何平滑化 (五點移動平均) ---
        # 這種方法極度穩定，不會產生發散，且能有效圓滑化轉角
        if len(path) > 5:
            smooth_path = []
            smooth_path.append(path[0])
            for i in range(1, len(path) - 1):
                # 對周圍點進行加權平均
                p_prev = path[i-1]
                p_curr = path[i]
                p_next = path[i+1]
                
                # 簡單且穩定的平均值
                sx = (p_prev[0] + p_curr[0] + p_next[0]) / 3.0
                sy = (p_prev[1] + p_curr[1] + p_next[1]) / 3.0
                smooth_path.append((sx, sy))
            smooth_path.append(path[-1])
            
            # 進行第二次迭代增加圓潤度
            final_path = [smooth_path[0]]
            for i in range(1, len(smooth_path)-1):
                fx = (smooth_path[i-1][0] + smooth_path[i][0] + smooth_path[i+1][0]) / 3.0
                fy = (smooth_path[i-1][1] + smooth_path[i][1] + smooth_path[i+1][1]) / 3.0
                final_path.append((fx, fy))
            final_path.append(smooth_path[-1])
            
            return final_path

        return path
