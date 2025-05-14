import heapq

class PathPlanner:
    """
    Class for path planning.
    Implements the A* algorithm to find the optimal path.
    """
    def __init__(self, environment):
        self.env = environment
    
    def heuristic(self, a, b):
        """Calculates the Manhattan distance between two points"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_neighbors(self, node):
        """Returns valid neighbors of a node"""
        x, y = node
        neighbors = []
        # 4 directions: up, right, down, left
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.env.is_valid_position(nx, ny):
                neighbors.append((nx, ny))
        return neighbors
    
    def a_star(self):
        """Implements the A* algorithm to find the optimal path"""
        if self.env.robot_pos is None or self.env.goal_pos is None:
            return None
        
        start = self.env.robot_pos
        goal = self.env.goal_pos
        
        # Priority queue for nodes to explore
        open_set = []
        heapq.heappush(open_set, (0, start))
        
        # Visited nodes
        came_from = {}
        
        # Cost from start node
        g_score = {start: 0}
        
        # Estimated total cost
        f_score = {start: self.heuristic(start, goal)}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal:
                # Reconstruct the path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            
            for neighbor in self.get_neighbors(current):
                tentative_g_score = g_score.get(current, float('inf')) + 1
                
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    
                    # Add to priority queue if not already present
                    if all(neighbor != item[1] for item in open_set):
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None  # No path found

class RRTPlanner:
    """
    Implementation of the Rapidly-exploring Random Tree (RRT) algorithm.
    An alternative to the A* algorithm for path planning.
    """
    def __init__(self, environment):
        self.env = environment
        # Future implementation
        pass
