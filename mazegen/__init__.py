"""
mazegen - Reusable Maze Generation Library
==========================================

Quick start::

    from mazegen import MazeGenerator

    gen = MazeGenerator(width=20, height=15, seed=42, perfect=True)
    gen.generate(entry=(0, 0), exit=(19, 14))
    print(gen.solution)  # ['S', 'E', 'E', ...]
    gen.save("maze.txt")
"""

from .maze_generator import MazeGenerator, MazeGenerationError

__version__: str = "1.0.0"
__all__ = ["MazeGenerator", "MazeGenerationError"]
