class TerrainType:
    """
    Class representing different terrain types
    """
    FREE = 0
    OBSTACLE = 1
    ROUGH = 2
    SLIPPERY = 3
    STEEP = 4
    WATER = 5
    
    @staticmethod
    def color(terrain_type):
        """
        Returns the color for a given terrain type for visualization
        """
        colors = {
            TerrainType.FREE: 'white',
            TerrainType.OBSTACLE: 'black',
            TerrainType.ROUGH: 'brown',
            TerrainType.SLIPPERY: 'lightblue',
            TerrainType.STEEP: 'darkgray',
            TerrainType.WATER: 'blue'
        }
        return colors.get(terrain_type, 'gray')
