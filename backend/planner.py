import heapq
import math
from typing import List, Tuple, Dict, Any

class AStarPlanner:
    def __init__(self, map_size=50000, grid_size=200):
        self.map_size = map_size
        self.grid_size = grid_size
        self.nodes_x = map_size // grid_size
        self.nodes_y = map_size // grid_size

    def get_path(self, start: List[float], goal: List[float], obstacles: List[Dict[str, Any]], static_costmap=None) -> Tuple[List[Tuple[float, float]], List[Tuple[int, int]]]:
        """
        計算全局路徑，並回傳搜尋過程中探索過的節點 (visited) 用於可視化。
        """
        start_grid = (int(round(start[0] / self.grid_size)), int(round(start[1] / self.grid_size)))
        goal_grid = (int(round(goal[0] / self.grid_size)), int(round(goal[1] / self.grid_size)))
        
        dyn_geoms = []
        for ob in obstacles:
            if ob.get('radius'):
                dyn_geoms.append((ob['x'], ob['y'], ob['radius']))

        def get_grid_penalty(gx, gy):
            if static_costmap is not None:
                igx = max(0, min(gx, static_costmap.shape[0]-1))
                igy = max(0, min(gy, static_costmap.shape[1]-1))
                penalty = static_costmap[igx, igy]
            else:
                penalty = 0
            
            if penalty >= 1000000: return penalty
            
            wx, wy = gx * self.grid_size, gy * self.grid_size
            for dx, dy, dr in dyn_geoms:
                d = math.sqrt((wx - dx)**2 + (wy - dy)**2) - dr
                if d < 520: return 1000000.0
                if d < 1500: penalty += (1500.0 / d) ** 4
            return penalty

        # --- A* 搜尋核心 ---
        queue = [(0, 0, start_grid)]
        came_from = {start_grid: None}
        cost_so_far = {start_grid: 0}
        visited = [] # 記錄探索順序

        while queue:
            _, _, current = heapq.heappop(queue)
            visited.append(current) # 記錄目前彈出的節點
            
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

        # 幾何平滑化
        if len(path) > 5:
            smooth_path = [path[0]]
            for i in range(1, len(path)-1):
                sx = (path[i-1][0] + path[i][0] + path[i+1][0]) / 3.0
                sy = (path[i-1][1] + path[i][1] + path[i+1][1]) / 3.0
                smooth_path.append((sx, sy))
            smooth_path.append(path[-1])
            return smooth_path, visited
            
        return path, visited
