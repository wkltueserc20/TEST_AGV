import heapq
import math
from typing import List, Tuple, Dict, Any

class AStarPlanner:
    def __init__(self, map_size=50000, grid_size=100):
        self.map_size = map_size
        self.grid_size = grid_size
        self.nodes_x = map_size // grid_size
        self.nodes_y = map_size // grid_size

    def get_path(self, start: List[float], goal: List[float], obstacles: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
        """計算全局路徑 (A*) - 座標修正與純物理中線版"""
        
        # 1. 精確對齊 100mm 網格
        start_grid = (int(round(start[0] / self.grid_size)), int(round(start[1] / self.grid_size)))
        goal_grid = (int(round(goal[0] / self.grid_size)), int(round(goal[1] / self.grid_size)))
        
        # 2. 預處理障礙物幾何 (修正：將 Center 轉為正確的 Bounds)
        obs_geoms = []
        for ob in obstacles:
            ox, oy = ob['x'], ob['y'] # 這是中心點
            w = ob.get('width', 1000)
            h = ob.get('height', 1000)
            r = ob.get('radius', 500)
            
            if ob['type'] == 'rectangle':
                # 正確的邊界計算：中心 +/- 半寬
                obs_geoms.append(('rect', [ox - w/2, oy - h/2, ox + w/2, oy + h/2]))
            else:
                obs_geoms.append(('circle', [ox, oy, r]))

        def get_grid_penalty(gx, gy):
            """
            計算該格點的物理勢場代價。
            """
            wx = gx * self.grid_size
            wy = gy * self.grid_size
            
            # 考慮邊界與所有障礙物，找出最近距離
            min_dist = min(wx, self.map_size - wx, wy, self.map_size - wy)
            is_blocked = False
            
            for kind, data in obs_geoms:
                if kind == 'rect':
                    # 點到矩形的精確距離
                    dx = max(data[0] - wx, 0, wx - data[2])
                    dy = max(data[1] - wy, 0, wy - data[3])
                    d = math.sqrt(dx**2 + dy**2)
                else:
                    d = math.sqrt((wx - data[0])**2 + (wy - data[1])**2) - data[2]
                
                if d <= 0: is_blocked = True; break
                if d < min_dist: min_dist = d
            
            # 絕對碰撞區
            if is_blocked or min_dist < 520: return 1000000.0 
            
            # 物理居中引導：
            # 在 2.0m 範圍內產生斥力。使用 (1/d^2) 曲線
            # 這在數學上能保證兩牆之間的中點是唯一的代價極小值
            if min_dist < 2000:
                # 權重設為 500,000，確保斥力遠超距離代價
                return 500000.0 / (min_dist ** 2)
            return 0

        queue = [(0, start_grid)]
        came_from = {start_grid: None}
        cost_so_far = {start_grid: 0}

        while queue:
            _, current = heapq.heappop(queue)
            if current == goal_grid: break

            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < self.nodes_x and 0 <= neighbor[1] < self.nodes_y:
                    
                    penalty = get_grid_penalty(neighbor[0], neighbor[1])
                    if penalty >= 1000000 and neighbor != goal_grid: continue
                    
                    # 移動物理距離 (100 or 141)
                    move_dist = math.sqrt(dx**2 + dy**2) * self.grid_size
                    # 總代價 = 距離 + 極端物理斥力
                    new_cost = cost_so_far[current] + move_dist + penalty
                    
                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        h = math.sqrt((goal_grid[0]-neighbor[0])**2 + (goal_grid[1]-neighbor[1])**2) * self.grid_size
                        priority = new_cost + h
                        heapq.heappush(queue, (priority, neighbor))
                        came_from[neighbor] = current

        if goal_grid not in came_from: return []
        
        path = []
        curr = goal_grid
        while curr is not None:
            path.append((curr[0]*self.grid_size, curr[1]*self.grid_size))
            curr = came_from[curr]
        path.reverse()
        return path
