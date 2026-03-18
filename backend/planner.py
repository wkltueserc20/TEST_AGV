import heapq
import math

class AStarPlanner:
    def __init__(self, map_size=50000, grid_size=500):
        self.map_size = map_size
        self.grid_size = grid_size
        self.nodes_x = map_size // grid_size
        self.nodes_y = map_size // grid_size

    def get_path(self, start, goal, obstacles):
        """計算全局路徑 (A*) - 平衡版"""
        start_grid = (int(start[0]//self.grid_size), int(start[1]//self.grid_size))
        goal_grid = (int(goal[0]//self.grid_size), int(goal[1]//self.grid_size))
        
        obs_grid = set()
        for ob in obstacles:
            ox, oy = ob['x'], ob['y']
            
            # 使用精確距離判定膨脹，而不僅僅是格點數
            # 膨脹 650mm (比半機身大 150mm) 確保絕對安全
            inf_range = 650
            gx_start = int((ox - inf_range) // self.grid_size)
            gx_end = int((ox + (ob.get('width', 1000) if ob['type']=='rectangle' else 0) + inf_range) // self.grid_size)
            gy_start = int((oy - inf_range) // self.grid_size)
            gy_end = int((oy + (ob.get('height', 1000) if ob['type']=='rectangle' else 0) + inf_range) // self.grid_size)
            
            for gx in range(gx_start, gx_end + 1):
                for gy in range(gy_start, gy_end + 1):
                    obs_grid.add((gx, gy))

        obs_grid.discard(start_grid)
        obs_grid.discard(goal_grid)

        queue = [(0, start_grid)]
        came_from = {start_grid: None}
        cost_so_far = {start_grid: 0}

        while queue:
            _, current = heapq.heappop(queue)
            if current == goal_grid: break

            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if (0 <= neighbor[0] < self.nodes_x and 0 <= neighbor[1] < self.nodes_y and 
                    neighbor not in obs_grid):
                    
                    new_cost = cost_so_far[current] + math.sqrt(dx**2 + dy**2)
                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        priority = new_cost + math.sqrt((goal_grid[0]-neighbor[0])**2 + (goal_grid[1]-neighbor[1])**2)
                        heapq.heappush(queue, (priority, neighbor))
                        came_from[neighbor] = current

        if goal_grid not in came_from: return []
        
        path = []
        curr = goal_grid
        while curr is not None:
            path.append((curr[0]*self.grid_size + self.grid_size//2, curr[1]*self.grid_size + self.grid_size//2))
            curr = came_from[curr]
        path.reverse()
        return path
