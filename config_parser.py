import random
from collections import deque
from typing import Optional

NORTH: int = 0b0001
EAST:  int = 0b0010
SOUTH: int = 0b0100
WEST:  int = 0b1000

OPPOSITE: dict[int, int] = {
    NORTH: SOUTH,
    SOUTH: NORTH,
    EAST:  WEST,
    WEST:  EAST,
}

DIR_DELTA: dict[int, tuple[int, int]] = {
    NORTH: (0, -1),
    EAST:  (1,  0),
    SOUTH: (0,  1),
    WEST:  (-1, 0),
}

DIR_CHAR: dict[int, str] = {
    NORTH: "N",
    EAST:  "E",
    SOUTH: "S",
    WEST:  "W",
}

ALL_WALLS: int = NORTH | EAST | SOUTH | WEST

_DIGIT_4: list[tuple[int, int]] = [
    (0, 0), (0, 2),
    (1, 0), (1, 2),
    (2, 0), (2, 1), (2, 2),
    (3, 2),
    (4, 2),
]
_DIGIT_2: list[tuple[int, int]] = [
    (0, 0), (0, 1), (0, 2),
    (1, 2),
    (2, 0), (2, 1), (2, 2),
    (3, 0),
    (4, 0), (4, 1), (4, 2),
]
_GLYPH_ROWS = 5
_GLYPH_COLS = 8


class MazeGenerationError(Exception):
    pass


class MazeGenerator:

    def __init__(
        self,
        width: int,
        height: int,
        seed: Optional[int] = None,
    ) -> None:

        if width < 2 or height < 2:
            raise MazeGenerationError(
                f"Maze must be at least 2x2, got {width}x{height}."
            )

        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self.grid:      list[list[int]] = []
        self.entry:     tuple[int, int] = (0, 0)
        self.exit:      tuple[int, int] = (width - 1, height - 1)
        self.solution:  list[str] = []
        self._rng = random.Random(self.seed)
        self._forty_two_cells: set[tuple[int, int]] = set()
        self._generated = False

    def generate(
        self,
        entry: tuple[int, int] = (0, 0),
        exit:  Optional[tuple[int, int]] = None,
    ) -> None:

        if exit is None:
            exit = (self.width - 1, self.height - 1)

        self._validate_coords(entry, "ENTRY")
        self._validate_coords(exit,  "EXIT")

        if entry == exit:
            raise MazeGenerationError("ENTRY and EXIT must be different.")

        self.entry = entry
        self.exit = exit

        self.grid = [[ALL_WALLS] * self.width for _ in range(self.height)]
        self._forty_two_cells = set()
        self.solution = []

        if not self._embed_forty_two():
            print(f"Warning: maze too small for '42' pattern.")

        self._carve_passages_dfs()
        self._apply_border_walls()
        self._open_entry_exit()
        self.solution = self._bfs_solve()
        self._generated = True

    def save(self, filepath: str) -> None:
        if not self._generated:
            raise MazeGenerationError("Call generate() before save().")
        try:
            with open(filepath, "w", encoding="utf-8") as fh:
                for row in self.grid:
                    fh.write("".join(format(c, "X") for c in row) + "\n")
                fh.write("\n")
                ex, ey = self.entry
                xx, xy = self.exit
                fh.write(f"{ex},{ey}\n")
                fh.write(f"{xx},{xy}\n")
                fh.write("".join(self.solution) + "\n")
        except OSError as exc:
            raise OSError(f"Cannot write '{filepath}': {exc}") from exc

    def cell_walls(self, x: int, y: int) -> dict[str, bool]:
        if not self._generated:
            raise MazeGenerationError("Call generate() first.")
        v = self.grid[y][x]
        return {
            "N": bool(v & NORTH),
            "E": bool(v & EAST),
            "S": bool(v & SOUTH),
            "W": bool(v & WEST),
        }

    def _validate_coords(self, c: tuple[int, int], name: str) -> None:
        x, y = c
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise MazeGenerationError(
                f"{name} ({x},{y}) out of bounds."
            )

    def _embed_forty_two(self) -> bool:
        if self.width < _GLYPH_COLS + 2 or self.height < _GLYPH_ROWS + 2:
            return False

        ox = (self.width - _GLYPH_COLS) // 2
        oy = (self.height - _GLYPH_ROWS) // 2

        def build(bx: int, by: int) -> set[tuple[int, int]]:
            cells: set[tuple[int, int]] = set()
            for dr, dc in _DIGIT_4:
                cells.add((bx + dc, by + dr))
            for dr, dc in _DIGIT_2:
                cells.add((bx + dc + 4, by + dr))
            return cells

        cells = build(ox, oy)
        for dy, dx in [(0, 0), (1, 0), (0, 1), (1, 1), (2, 0)]:
            cand = build(ox + dx, oy + dy)
            if self.entry not in cand and self.exit not in cand:
                cells = cand
                break
        else:
            return False

        for cx, cy in cells:
            if not (0 <= cx < self.width and 0 <= cy < self.height):
                return False

        self._forty_two_cells = cells
        for cx, cy in cells:
            self.grid[cy][cx] = ALL_WALLS
        return True

    def _carve_passages_dfs(self) -> None:
        visited: set[tuple[int, int]] = set()
        sx, sy = self.entry
        stack = [(sx, sy)]
        visited.add((sx, sy))

        while stack:
            cx, cy = stack[-1]
            dirs = list(DIR_DELTA.keys())
            self._rng.shuffle(dirs)
            moved = False

            for d in dirs:
                ddx, ddy = DIR_DELTA[d]
                nx, ny = cx + ddx, cy + ddy

                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and (nx, ny) not in self._forty_two_cells
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

        # reconnect islands lli bqaw maqtu3in 3la 42
        visited.add(self.entry)
        visited -= self._forty_two_cells
        self._reconnect_islands(visited, self._forty_two_cells)

    def _reconnect_islands(
        self,
        visited: set[tuple[int, int]],
        obstacles: set[tuple[int, int]],
    ) -> None:
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in visited or (x, y) in obstacles:
                    continue
                q: deque = deque()
                q.append((x, y, []))
                seen: set[tuple[int, int]] = {(x, y)}
                found = False
                while q and not found:
                    cx, cy, path = q.popleft()
                    for d, (ddx, ddy) in DIR_DELTA.items():
                        nx, ny = cx + ddx, cy + ddy
                        if not (0 <= nx < self.width and 0 <= ny < self.height):
                            continue
                        if (nx, ny) in seen:
                            continue
                        seen.add((nx, ny))
                        npath = path + [(cx, cy, d)]
                        if (nx, ny) in visited:
                            for px, py, pd in npath:
                                pddx, pddy = DIR_DELTA[pd]
                                self.grid[py][px] &= ~pd
                                self.grid[py + pddy][px +
                                                     pddx] &= ~OPPOSITE[pd]
                                visited.add((px, py))
                            visited.add((nx, ny))
                            found = True
                            break
                        if (nx, ny) not in obstacles:
                            q.append((nx, ny, npath))

    def _apply_border_walls(self) -> None:
        for x in range(self.width):
            self.grid[0][x] |= NORTH
            self.grid[self.height - 1][x] |= SOUTH
        for y in range(self.height):
            self.grid[y][0] |= WEST
            self.grid[y][self.width - 1] |= EAST

    def _open_entry_exit(self) -> None:
        ex, ey = self.entry
        self.grid[ey][ex] &= ~self._outward_wall(ex, ey)
        xx, xy = self.exit
        self.grid[xy][xx] &= ~self._outward_wall(xx, xy)

    def _outward_wall(self, x: int, y: int) -> int:
        if y == 0:
            return NORTH
        if y == self.height-1:
            return SOUTH
        if x == 0:
            return WEST
        return EAST

    def _bfs_solve(self) -> list[str]:
        ex, ey = self.entry
        xx, xy = self.exit
        parent: dict = {}
        queue = deque([(ex, ey)])
        seen: set[tuple[int, int]] = {(ex, ey)}

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == (xx, xy):
                break
            for d, (ddx, ddy) in DIR_DELTA.items():
                if self.grid[cy][cx] & d:
                    continue
                nx, ny = cx + ddx, cy + ddy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and (nx, ny) not in seen
                ):
                    seen.add((nx, ny))
                    parent[(nx, ny)] = ((cx, cy), d)
                    queue.append((nx, ny))

        path: list[str] = []
        cur = (xx, xy)
        while cur in parent:
            prev, d = parent[cur]
            path.append(DIR_CHAR[d])
            cur = prev
        path.reverse()
        return path


# ── TEST ────────────────────────────────────────────────────
if __name__ == "__main__":
    maze = MazeGenerator(20, 14)
    maze.generate()
    maze.save("maze_data.txt")

    # print maze b walls
    width = maze.width
    height = maze.height

    # top border
    print("+" + "---+" * width)

    for y in range(height):
        # cells + east walls
        row_str = "|"
        for x in range(width):
            walls = maze.cell_walls(x, y)
            # content dial cell
            if (x, y) == maze.entry:
                cell = " S "
            elif (x, y) == maze.exit:
                cell = " E "
            elif (x, y) in maze._forty_two_cells:
                cell = "███"
            else:
                cell = "   "
            # east wall
            east = "|" if walls["E"] else " "
            row_str += cell + east
        print(row_str)

        # south walls
        south_str = "+"
        for x in range(width):
            walls = maze.cell_walls(x, y)
            south = "---" if walls["S"] else "   "
            south_str += south + "+"
        print(south_str)

    print(f"\nseed:     {maze.seed}")
    print(f"entry:    {maze.entry}")
    print(f"exit:     {maze.exit}")
    print(f"solution: {''.join(maze.solution)}")
    print(f"steps:    {len(maze.solution)}")
    print("\nSolution path:")
    x, y = maze.entry
    for i, step in enumerate(maze.solution):
        print(f"  step {i+1:3}: ({x},{y}) → {step} → ", end="")
        if step == "N":
            y -= 1
        elif step == "S":
            y += 1
        elif step == "E":
            x += 1
        elif step == "W":
            x -= 1
        print(f"({x},{y})")
    print(f"  arrived at exit: ({x},{y})")
