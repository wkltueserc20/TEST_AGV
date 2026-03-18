import heapq
import math

class AStarPlanner:
    def __init__(self, map_size=50000, grid_size=1000):
        self.map_size = map_size
        self.grid_size = grid_size
        self.nodes_x = map_size // grid_size
        self.nodes_y = map_size // grid_size

    def get_path(self, start, goal, obstacles):
        """計算全局路徑 (A*)"""
        start_grid = (int(start[0]//self.grid_size), int(start[1]//self.grid_size))
        goal_grid = (int(goal[0]//self.grid_size), int(goal[1]//self.grid_size))
        
        # 建立障礙物地圖
        obs_grid = set()
        for ob in obstacles:
            ox, oy = ob['x']//self.grid_size, ob['y']//self.grid_size
            # 縮小膨脹半徑：1m 車體，膨脹 1 格 (1m) 即可
            inflation = 1 
            for dx in range(-inflation, inflation + 1):
                for dy in range(-inflation, inflation + 1):
                    obs_grid.add((int(ox+dx), int(oy+dy)))

        # 基礎檢查
        if start_grid in obs_grid: # 如果起點被卡住，嘗試向外尋找最近空點
            pass # 這裡可以擴展，暫時假設起點安全

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
                    
                    move_cost = math.sqrt(dx**2 + dy**2)
                    new_cost = cost_so_far[current] + move_cost
                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        priority = new_cost + math.sqrt((goal_grid[0]-neighbor[0])**2 + (goal_grid[1]-neighbor[1])**2)
                        heapq.heappush(queue, (priority, neighbor))
                        came_from[neighbor] = current

        if goal_grid not in came_from: 
            print("A* Planner: No path found!")
            return []
        
        path = []
        curr = goal_grid
        while curr is not None:
            path.append((curr[0]*self.grid_size + self.grid_size//2, curr[1]*self.grid_size + self.grid_size//2))
            curr = came_from[curr]
        path.reverse()
        return path
