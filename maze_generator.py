"""maze_generator.py - maze generation logic."""

import random
from collections import deque
from typing import Optional

# Direction constants
NORTH = 0b0001
EAST = 0b0010
SOUTH = 0b0100
WEST = 0b1000

OPPOSITE = {NORTH: SOUTH, SOUTH: NORTH, EAST: WEST, WEST: EAST}

DIR_DELTA: dict = {
    NORTH: (0, -1),
    EAST:  (1,  0),
    SOUTH: (0,  1),
    WEST:  (-1, 0),
}

DIR_CHAR: dict = {
    NORTH: "N",
    EAST:  "E",
    SOUTH: "S",
    WEST:  "W",
}

ALL_WALLS = NORTH | EAST | SOUTH | WEST

DIGIT_4 = [(0, 0), (0, 2), (1, 0), (1, 2), (2, 0),
           (2, 1), (2, 2), (3, 2), (4, 2)]
DIGIT_2 = [(0, 0), (0, 1), (0, 2), (1, 2), (2, 0), (2, 1),
           (2, 2), (3, 0), (4, 0), (4, 1), (4, 2)]

GLYPH_H, GLYPH_W = 5, 8


class MazeGenerationError(Exception):
    """raised when maze generation fails."""

    pass


class MazeGenerator:
    """generates a maze from given dimensions and config."""

    def __init__(
        self,
        width: int,
        height: int,
        seed: Optional[int] = None,
        perfect: bool = True,
    ) -> None:
        """set up the generator with size and options.

        Args:
            width: number of cells horizontally.
            height: number of cells vertically.
            seed: random seed for reproducibility.
            perfect: if True, only one path between entry and exit.
        """
        if width < 2 or height < 2:
            raise ValueError(
                f"Maze must be at least 2x2 (got {width}x{height})."
            )
        self.width = width
        self.height = height
        self.perfect = perfect
        self.seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self._rng = random.Random(self.seed)
        self.grid: list = []
        self.entry: tuple = (0, 0)
        self.exit: tuple = (width - 1, height - 1)
        self.solutions: list = []
        self._42_cells: set = set()

    def generate(
        self,
        entry: tuple = (0, 0),
        exit: Optional[tuple] = None,
    ) -> None:
        """generate the maze from entry to exit.

        Args:
            entry: entry coordinates (x, y).
            exit: exit coordinates (x, y). defaults to bottom-right.
        """
        if exit is None:
            exit = (self.width - 1, self.height - 1)
        self._check_coord(entry, "ENTRY")
        self._check_coord(exit, "EXIT")
        if entry == exit:
            raise ValueError("ENTRY and EXIT must be different cells.")
        self.entry = entry
        self.exit = exit
        self.grid = [[ALL_WALLS] * self.width for _ in range(self.height)]
        self._42_cells = set()
        self.solutions = []
        self._place_42_pattern()
        self._dfs_carve()
        self._seal_border()
        self._open_endpoints()
        if not self.perfect:
            self._add_loops()
        if self.perfect:
            path = self._bfs_solve()
            self.solutions = [path]
        else:
            self.solutions = self._find_all_solutions()

    def save(self, filepath: str) -> None:
        """save the maze to a file in hex format.

        Args:
            filepath: path to write the maze file.
        """
        if not self.solutions:
            raise RuntimeError("Call generate() before save().")
        with open(filepath, "w", encoding="utf-8") as f:
            for row in self.grid:
                f.write("".join(format(c, "X") for c in row) + "\n")
            f.write("\n")
            ex, ey = self.entry
            xx, xy = self.exit
            f.write(f"{ex},{ey}\n")
            f.write(f"{xx},{xy}\n")
            for path in self.solutions:
                f.write("".join(path) + "\n")

    def cell_walls(self, x: int, y: int) -> dict:
        """return which walls are present for cell (x, y).

        Args:
            x: cell x coordinate.
            y: cell y coordinate.

        Returns:
            dict with keys N, E, S, W and bool values.
        """
        v = self.grid[y][x]
        return {
            "N": bool(v & NORTH),
            "E": bool(v & EAST),
            "S": bool(v & SOUTH),
            "W": bool(v & WEST),
        }

    def _check_coord(self, c: tuple, name: str) -> None:
        """check that a coordinate is inside the maze bounds.

        Args:
            c: (x, y) coordinate to check.
            name: label used in the error message.
        """
        x, y = c
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"{name} ({x},{y}) is out of bounds.")

    def _place_42_pattern(self) -> None:
        """centre the 42 glyph in the maze — those cells are never carved."""
        if self.width < GLYPH_W + 2 or self.height < GLYPH_H + 2:
            print("Warning: maze too small for '42' pattern - skipped.")
            return
        ox = (self.width - GLYPH_W) // 2
        oy = (self.height - GLYPH_H) // 2
        cells = self._build_42_cells(ox, oy)
        if self.entry in cells or self.exit in cells:
            print("Warning: '42' pattern overlaps entry/exit - skipped.")
            return
        self._42_cells = cells

    def _build_42_cells(self, ox: int, oy: int) -> set:
        """return the set of (x, y) cells that form the 42 glyph.

        Args:
            ox: x offset for centering.
            oy: y offset for centering.

        Returns:
            set of (x, y) tuples.
        """
        cells: set = set()
        for row, col in DIGIT_4:
            cells.add((ox + col, oy + row))
        for row, col in DIGIT_2:
            cells.add((ox + col + 4, oy + row))
        return cells

    def _dfs_carve(self) -> None:
        """carve passages using iterative DFS."""
        visited: set = set()
        sx, sy = self.entry
        stack = [(sx, sy)]
        visited.add((sx, sy))
        while stack:
            cx, cy = stack[-1]
            directions = list(DIR_DELTA.keys())
            self._rng.shuffle(directions)
            moved = False
            for d in directions:
                dx, dy = DIR_DELTA[d]
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and (nx, ny) not in self._42_cells
                    and (nx, ny) not in visited
                ):
                    self.grid[cy][cx] &= ~d
                    self.grid[ny][nx] &= ~OPPOSITE[d]
                    visited.add((nx, ny))
                    stack.append((nx, ny))
                    moved = True
                    break
            if not moved:
                stack.pop()

    def _seal_border(self) -> None:
        """force all outer edge walls closed."""
        for x in range(self.width):
            self.grid[0][x] |= NORTH
            self.grid[self.height - 1][x] |= SOUTH
        for y in range(self.height):
            self.grid[y][0] |= WEST
            self.grid[y][self.width - 1] |= EAST

    def _open_endpoints(self) -> None:
        """remove the outward-facing border wall at entry and exit."""
        ex, ey = self.entry
        self.grid[ey][ex] &= ~self._outward_dir(ex, ey)
        xx, xy = self.exit
        self.grid[xy][xx] &= ~self._outward_dir(xx, xy)

    def _outward_dir(self, x: int, y: int) -> int:
        """return the direction that faces outside the maze for a border cell.

        Args:
            x: cell x coordinate.
            y: cell y coordinate.

        Returns:
            direction constant (NORTH, SOUTH, EAST or WEST).
        """
        if y == 0:
            return NORTH
        if y == self.height - 1:
            return SOUTH
        if x == 0:
            return WEST
        return EAST

    def _add_loops(self) -> None:
        """remove some walls to create loops — only for imperfect mazes."""
        num_removals = (self.width * self.height) // 10
        for _ in range(num_removals):
            x = self._rng.randint(0, self.width - 2)
            y = self._rng.randint(0, self.height - 2)
            if (x, y) in self._42_cells:
                continue
            direction = self._rng.choice([EAST, SOUTH])
            dx, dy = DIR_DELTA[direction]
            nx, ny = x + dx, y + dy
            if (nx, ny) in self._42_cells:
                continue
            self.grid[y][x] &= ~direction
            self.grid[ny][nx] &= ~OPPOSITE[direction]

    def _bfs_solve(self) -> list:
        """find the shortest path from entry to exit using BFS.

        Returns:
            list of direction chars (N, E, S, W).
        """
        ex, ey = self.entry
        xx, xy = self.exit
        parent: dict = {}
        queue = deque([(ex, ey)])
        seen = {(ex, ey)}
        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == (xx, xy):
                break
            for d, (dx, dy) in DIR_DELTA.items():
                if self.grid[cy][cx] & d:
                    continue
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and (nx, ny) not in seen
                ):
                    seen.add((nx, ny))
                    parent[(nx, ny)] = ((cx, cy), d)
                    queue.append((nx, ny))
        path: list = []
        cur = (xx, xy)
        while cur in parent:
            prev, d = parent[cur]
            path.append(DIR_CHAR[d])
            cur = prev
        path.reverse()
        return path

    def _find_all_solutions(self) -> list:
        """find all paths from entry to exit using DFS.

        Returns:
            list of paths, each path is a list of direction chars.
        """
        ex, ey = self.entry
        xx, xy = self.exit
        all_paths: list = []
        current_path: list = []
        on_path: set = {(ex, ey)}

        def dfs(cx: int, cy: int) -> None:
            """recursive DFS to find all paths."""
            if (cx, cy) == (xx, xy):
                all_paths.append(list(current_path))
                return
            for d, (dx, dy) in DIR_DELTA.items():
                if self.grid[cy][cx] & d:
                    continue
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and (nx, ny) not in on_path
                ):
                    current_path.append(DIR_CHAR[d])
                    on_path.add((nx, ny))
                    dfs(nx, ny)
                    current_path.pop()
                    on_path.remove((nx, ny))

        dfs(ex, ey)
        return all_paths
