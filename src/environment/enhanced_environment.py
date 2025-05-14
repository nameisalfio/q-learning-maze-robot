import numpy as np
from src.environment.environment import Environment # Ensure this path is correct
from src.environment.models.terrain import TerrainType   # Ensure this path is correct

class EnhancedEnvironment(Environment):
    """
    Enhanced environment with support for different terrain types.
    """
    def __init__(self, width, height):
        super().__init__(width, height)
        # We assume that super().__init__ initializes self.grid,
        # typically with TerrainType.FREE. For example:
        # self.width = width
        # self.height = height
        # self.grid = np.full((height, width), TerrainType.FREE, dtype=object) # or a specific type
        # self.robot_pos = None
        # self.goal_pos = None

    def add_terrain(self, x_coord, y_coord, patch_w, patch_h, terrain_type):
        """
        Add a rectangular patch of a specified terrain type to the grid.

        Args:
            x_coord (int): The x-coordinate (column index) of the top-left corner of the patch.
            y_coord (int): The y-coordinate (row index) of the top-left corner of the patch.
            patch_w (int): The width of the patch.
            patch_h (int): The height of the patch.
            terrain_type: The type of terrain to add (from TerrainType enum/class).
        """
        # Convert to int for safety, especially if they come from float calculations
        x_coord, y_coord = int(x_coord), int(y_coord)
        patch_w, patch_h = int(patch_w), int(patch_h)

        # Define the patch boundaries, ensuring they are within the grid
        # NumPy indexing is [row, column]
        row_start = max(0, y_coord)
        # The end limit of slicing is exclusive, so y_coord + patch_h
        row_end = min(self.height, y_coord + patch_h) 
        
        col_start = max(0, x_coord)
        col_end = min(self.width, x_coord + patch_w)

        # Apply the terrain type to the selected grid area
        # Only if the resulting area has valid (non-negative or zero) dimensions
        if row_start < row_end and col_start < col_end:
            self.grid[row_start:row_end, col_start:col_end] = terrain_type

    def create_terrain_map(self, terrain_ratio):
        """
        Generates a random terrain map by adding patches of different non-FREE terrain types.
        The `terrain_ratio` specifies the approximate fraction of the map
        to be covered by these non-FREE terrains.

        Args:
            terrain_ratio (float): The desired approximate ratio of non-FREE cells in the grid.
                                   Example: 0.15 means about 15% of cells should be non-FREE.
        """
        # 1. Start with a completely free grid.
        # This ensures that each generation starts from a clean state.
        self.grid.fill(TerrainType.FREE)

        if terrain_ratio <= 0.0:
            return # No terrain to add if the ratio is zero or negative

        # 2. Define the 'non-free' terrain types to add and their relative probabilities.
        # These should be defined in your TerrainType class/enum.
        possible_terrains = [
            TerrainType.OBSTACLE,
            TerrainType.ROUGH,
            TerrainType.WATER
            # Add other terrain types if necessary
        ]
        # Weights for random selection (should sum to 1 if used with np.random.choice and p)
        terrain_weights = [0.6, 0.3, 0.1]  # Example: 60% obstacles, 30% rough, 10% water
        
        if not possible_terrains:
            # print("Warning: No possible terrain_types defined in create_terrain_map.")
            return
        
        # 3. Calculate the target number of 'non-free' cells
        total_cells = self.width * self.height
        if total_cells == 0: # Avoid division by zero if the grid is empty
            return

        num_target_terrain_cells = int(total_cells * terrain_ratio)
        
        cells_terraformed = 0 # Counter for cells actually changed to non-FREE

        # 4. Heuristic parameters for generating terrain patches
        # Average patch dimensions (can be adjusted)
        avg_patch_dim_w = max(1, int(self.width * 0.05))  # E.g.: 5% of the map width
        avg_patch_dim_h = max(1, int(self.height * 0.05)) # E.g.: 5% of the map height
        
        # Estimate of the average patch area to calculate the number of attempts
        # Add 1 to width and height before multiplying to avoid zero area if avg_patch_dim is small
        avg_patch_area_est = (avg_patch_dim_w + 1) * (avg_patch_dim_h + 1) 
        if avg_patch_area_est == 0: avg_patch_area_est = 1


        # Limit the number of attempts to avoid very long loops
        # Try to generate enough patches, with some margin (e.g., 5x)
        max_attempts = int((num_target_terrain_cells / avg_patch_area_est) * 5) if avg_patch_area_est > 0 else 20
        # Minimum 20 attempts, or if terrain_ratio is very small
        max_attempts = max(20, max_attempts) 

        # 5. Patch generation loop
        attempt_count = 0 # Initialize attempt_count before the loop
        for attempt_count in range(max_attempts):
            if cells_terraformed >= num_target_terrain_cells:
                break # Reached the target number of modified cells

            # a. Select a terrain type for the current patch
            terrain_type = np.random.choice(possible_terrains, p=terrain_weights)
            
            # b. Determine the patch dimensions (with some variability)
            # Ensure dimensions are at least 1.
            # np.random.randint(low, high) -> high is exclusive.
            patch_w = np.random.randint(1, max(2, (avg_patch_dim_w * 2) + 1))
            patch_h = np.random.randint(1, max(2, (avg_patch_dim_h * 2) + 1))
            
            # c. Determine the position (top-left corner) of the patch
            start_x = np.random.randint(0, self.width)  # Column index
            start_y = np.random.randint(0, self.height) # Row index
            
            # d. Calculate the actual area of the patch on the grid
            row_start = max(0, start_y)
            row_end = min(self.height, start_y + patch_h)
            col_start = max(0, start_x)
            col_end = min(self.width, start_x + patch_w)

            # If the actual area of the patch is null (e.g., completely off-grid), skip
            if not (row_start < row_end and col_start < col_end):
                continue

            # e. Count how many currently FREE cells in this area will be converted.
            # This correctly handles overlaps: only new conversions count.
            sub_grid_to_change = self.grid[row_start:row_end, col_start:col_end]
            free_cells_in_target_area = np.sum(sub_grid_to_change == TerrainType.FREE)
            
            # f. Apply the terrain patch and update the counter
            if free_cells_in_target_area > 0:
                # Modify the grid directly for efficiency, having already calculated the limits.
                # Alternatively, self.add_terrain(...) could be called
                self.grid[row_start:row_end, col_start:col_end] = terrain_type
                cells_terraformed += free_cells_in_target_area
        
        # Debug output (optional, can be removed or logged)
        # current_non_free_cells = np.sum(self.grid != TerrainType.FREE)
        # actual_ratio = current_non_free_cells / total_cells if total_cells > 0 else 0
        # print(f"create_terrain_map: Target ratio: {terrain_ratio:.2f}, Actual ratio: {actual_ratio:.2f} "
        #       f"(Target cells: {num_target_terrain_cells}, Actual non-FREE: {current_non_free_cells}) "
        #       f"Attempts: {attempt_count+1}/{max_attempts}")