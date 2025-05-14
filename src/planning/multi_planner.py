from src.planning.path_planner import PathPlanner
from src.planning.algorithms.rrt_planner import RRTPlanner, RRTStarPlanner
from src.planning.algorithms.path_optimizer import PathOptimizer

class MultiPlanner:
    """
    A planner that can use different path planning algorithms
    """
    def __init__(self, environment):
        self.env = environment
        self.algorithms = {
            'a_star': PathPlanner(environment),
            'rrt': RRTPlanner(environment),
            'rrt_star': RRTStarPlanner(environment),
        }
        self.optimizer = PathOptimizer(environment)
        
    def plan(self, algorithm='a_star', optimize=False, waypoints=None):
        """
        Plan a path using the specified algorithm
        
        Parameters:
            algorithm: Algorithm to use ('a_star', 'rrt', 'rrt_star')
            optimize: Whether to optimize the path after planning
            waypoints: List of waypoints to visit in order
            
        Returns:
            Planned path
        """
        if algorithm not in self.algorithms:
            print(f"Algorithm {algorithm} not supported. Using A*.")
            algorithm = 'a_star'
            
        planner = self.algorithms[algorithm]
        
        # Handle waypoints if specified
        if waypoints and len(waypoints) > 0:
            return self._plan_with_waypoints(planner, waypoints)
            
        # Plan the path
        if algorithm == 'a_star':
            path = planner.a_star()
        else:  # RRT or RRT*
            path = planner.plan()
            
        # Optimize if requested
        if optimize and path:
            # First prune redundant points
            path = self.optimizer.prune_path(path)
            # Then smooth the path
            path = self.optimizer.smooth_path(path)
            
        return path
        
    def _plan_with_waypoints(self, planner, waypoints):
        """
        Plan a path that visits all waypoints in order
        """
        if self.env.robot_pos is None or self.env.goal_pos is None:
            return None
            
        # Add start and goal positions to the waypoints
        all_points = [self.env.robot_pos] + waypoints + [self.env.goal_pos]
        
        # Plan path between consecutive waypoints
        complete_path = []
        original_robot_pos = self.env.robot_pos
        original_goal_pos = self.env.goal_pos
        
        for i in range(len(all_points) - 1):
            # Set temporary start and goal
            self.env.robot_pos = all_points[i]
            self.env.goal_pos = all_points[i+1]
            
            # Plan segment
            if isinstance(planner, PathPlanner):
                segment = planner.a_star()
            else:  # RRT planners
                segment = planner.plan()
                
            # Restore original positions
            self.env.robot_pos = original_robot_pos
            self.env.goal_pos = original_goal_pos
            
            if segment is None:
                print(f"Could not find path to waypoint {i+1}")
                return None
                
            # Avoid duplicating waypoints
            if complete_path and segment:
                segment = segment[1:]
                
            complete_path.extend(segment)
            
        return complete_path
