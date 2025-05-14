import numpy as np
import random
import heapq
import matplotlib.pyplot as plt

class Node:
    """
    Node class for RRT algorithm
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None
        self.cost = 0.0  # for RRT*

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.x == other.x and self.y == other.y
        return False
    
    def distance(self, other):
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def as_tuple(self):
        return (self.x, self.y)


class RRTPlanner:
    """
    Rapidly-exploring Random Tree (RRT) path planner
    """
    def __init__(self, environment, step_size=1.0, max_iterations=1000, goal_sample_rate=0.1):
        self.env = environment
        self.step_size = step_size
        self.max_iterations = max_iterations
        self.goal_sample_rate = goal_sample_rate
        self.nodes = []
        self.path = []
        self.goal_node = None
        
    def plan(self):
        """
        Plan a path using RRT algorithm
        """
        if self.env.robot_pos is None or self.env.goal_pos is None:
            return None
        
        # Initialize the tree with start node
        start_node = Node(self.env.robot_pos[0], self.env.robot_pos[1])
        self.goal_node = Node(self.env.goal_pos[0], self.env.goal_pos[1])
        self.nodes = [start_node]
        
        # Main loop
        for i in range(self.max_iterations):
            # Sample random node (with bias towards goal)
            if random.random() < self.goal_sample_rate:
                random_node = self.goal_node
            else:
                random_x = random.randint(0, self.env.width - 1)
                random_y = random.randint(0, self.env.height - 1)
                random_node = Node(random_x, random_y)
            
            # Find nearest node in the tree
            nearest_node = self._find_nearest(random_node)
            
            # Create new node by steering from nearest toward random
            new_node = self._steer(nearest_node, random_node)
            
            # Check if the path is obstacle-free
            if new_node and self._obstacle_free(nearest_node, new_node):
                # Add new node to tree
                new_node.parent = nearest_node
                self.nodes.append(new_node)
                
                # Check if goal is reached
                if self._reached_goal(new_node):
                    self.path = self._extract_path(new_node)
                    return self._convert_path_to_tuples()
                
        # If max iterations reached without finding path
        print("Failed to find path after maximum iterations")
        return None
    
    def _find_nearest(self, target_node):
        """Find the nearest node in the tree to the target node"""
        distances = [node.distance(target_node) for node in self.nodes]
        return self.nodes[np.argmin(distances)]
    
    def _steer(self, from_node, to_node):
        """
        Create a new node by moving from 'from_node' towards 'to_node'
        with step size
        """
        # Calculate direction
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        
        # Calculate distance
        distance = np.sqrt(dx**2 + dy**2)
        
        # If distance is less than step size, return to_node
        if distance < self.step_size:
            new_x, new_y = to_node.x, to_node.y
        else:
            # Scale direction vector to step size
            dx = dx * self.step_size / distance
            dy = dy * self.step_size / distance
            
            # Create new point
            new_x = int(from_node.x + dx)
            new_y = int(from_node.y + dy)
        
        # Check if the new position is valid
        if self.env.is_valid_position(new_x, new_y):
            new_node = Node(new_x, new_y)
            return new_node
        
        return None
    
    def _obstacle_free(self, from_node, to_node):
        """Check if the path between two nodes is obstacle-free"""
        # Simple implementation: check only a few points along the line
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        distance = np.sqrt(dx**2 + dy**2)
        
        # Number of points to check (at least 10 or the distance, whichever is greater)
        n_points = max(10, int(distance))
        
        for i in range(1, n_points):
            # Get point i along the line
            x = int(from_node.x + dx * i / n_points)
            y = int(from_node.y + dy * i / n_points)
            
            # Check if point is valid
            if not self.env.is_valid_position(x, y):
                return False
                
        return True
    
    def _reached_goal(self, node):
        """Check if the node has reached the goal"""
        return node.distance(self.goal_node) < self.step_size
    
    def _extract_path(self, end_node):
        """Extract the path from start to end node"""
        path = []
        current = end_node
        
        while current is not None:
            path.append(current)
            current = current.parent
            
        # Reverse to get path from start to goal
        path.reverse()
        return path
    
    def _convert_path_to_tuples(self):
        """Convert the path from Node objects to coordinate tuples"""
        return [node.as_tuple() for node in self.path]
    
    def visualize_tree(self, ax=None):
        """Visualize the RRT tree"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.set_xlim(0, self.env.width)
            ax.set_ylim(0, self.env.height)
            
        # Draw all edges in the tree
        for node in self.nodes:
            if node.parent is not None:
                ax.plot([node.x, node.parent.x], [node.y, node.parent.y], 'g-', alpha=0.5)
                
        # Draw the path if found
        if self.path:
            path_x = [node.x for node in self.path]
            path_y = [node.y for node in self.path]
            ax.plot(path_x, path_y, 'r-', linewidth=2)
        
        return ax


class RRTStarPlanner(RRTPlanner):
    """
    RRT* algorithm - an optimized version of RRT that finds
    more optimal paths
    """
    def __init__(self, environment, step_size=1.0, max_iterations=1000, 
                goal_sample_rate=0.1, search_radius=5.0):
        super().__init__(environment, step_size, max_iterations, goal_sample_rate)
        self.search_radius = search_radius  # Radius for rewiring
        
    def plan(self):
        """
        Plan a path using RRT* algorithm
        """
        if self.env.robot_pos is None or self.env.goal_pos is None:
            return None
        
        # Initialize the tree with start node
        start_node = Node(self.env.robot_pos[0], self.env.robot_pos[1])
        self.goal_node = Node(self.env.goal_pos[0], self.env.goal_pos[1])
        self.nodes = [start_node]
        
        # Main loop
        for i in range(self.max_iterations):
            # Sample random node (with bias towards goal)
            if random.random() < self.goal_sample_rate:
                random_node = self.goal_node
            else:
                random_x = random.randint(0, self.env.width - 1)
                random_y = random.randint(0, self.env.height - 1)
                random_node = Node(random_x, random_y)
            
            # Find nearest node in the tree
            nearest_node = self._find_nearest(random_node)
            
            # Create new node by steering from nearest toward random
            new_node = self._steer(nearest_node, random_node)
            
            # Check if the path is obstacle-free
            if new_node and self._obstacle_free(nearest_node, new_node):
                # Find nearby nodes for potential rewiring
                nearby_nodes = self._find_nearby_nodes(new_node)
                
                # Connect new_node to best parent
                self._choose_parent(new_node, nearby_nodes)
                
                # Add new node to tree
                self.nodes.append(new_node)
                
                # Rewire the tree
                self._rewire(new_node, nearby_nodes)
                
                # Check if goal is reached
                if self._reached_goal(new_node):
                    self.path = self._extract_path(new_node)
                    return self._convert_path_to_tuples()
                
        # If max iterations reached without finding path
        print("Failed to find path after maximum iterations")
        return None
    
    def _find_nearby_nodes(self, node):
        """
        Find nodes within search_radius of the given node
        """
        nearby = []
        for potential_node in self.nodes:
            if potential_node.distance(node) < self.search_radius:
                nearby.append(potential_node)
        return nearby
    
    def _choose_parent(self, new_node, nearby_nodes):
        """
        Choose the best parent for new_node from nearby_nodes
        """
        if not nearby_nodes:
            return
        
        # Calculate costs to come to new_node through each nearby node
        costs = []
        for node in nearby_nodes:
            # Cost to reach nearby node
            cost_to_node = node.cost
            
            # Cost from nearby node to new_node
            if self._obstacle_free(node, new_node):
                cost_to_new = node.distance(new_node)
                costs.append((cost_to_node + cost_to_new, node))
        
        # Choose the node with lowest cost as parent
        if costs:
            costs.sort()  # Sort by cost
            best_cost, best_node = costs[0]
            
            # Set the new parent and cost
            new_node.parent = best_node
            new_node.cost = best_cost
    
    def _rewire(self, new_node, nearby_nodes):
        """
        Rewire the tree to minimize costs
        """
        for node in nearby_nodes:
            # Skip the parent of new_node
            if node == new_node.parent:
                continue
                
            # Check if the path is obstacle-free
            if self._obstacle_free(new_node, node):
                # Calculate new cost
                potential_cost = new_node.cost + new_node.distance(node)
                
                # If new path is better, rewire
                if potential_cost < node.cost:
                    node.parent = new_node
                    node.cost = potential_cost
                    
                    # Recursively update costs for all descendants
                    self._update_descendants_cost(node)
    
    def _update_descendants_cost(self, node):
        """
        Update costs for all descendants of node
        """
        # Find all descendants (children nodes)
        descendants = [n for n in self.nodes if n.parent == node]
        
        for descendant in descendants:
            # Update cost
            descendant.cost = node.cost + node.distance(descendant)
            
            # Recursively update descendants of current descendant
            self._update_descendants_cost(descendant)
