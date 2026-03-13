"""renderer.py - reads maze.txt and displays it in the terminal."""

import os
import sys
from typing import Any

# wall bits
NORTH = 0x1
EAST = 0x2
SOUTH = 0x4
WEST = 0x8

# colors
RESET = "\033[0m"
WALL_COLORS = [
    "\033[107m",   # White
    "\033[104m",   # Blue
    "\033[102m",   # Green
    "\033[105m",   # Magenta
]
ENTRY_COLOR = "\033[42m"   # green
EXIT_COLOR = "\033[41m"   # red
PATH_COLOR = "\033[43m"   # yellow
COLOR_42 = "\033[45m"   # pink

WALL_BLOCK = "  "
EMPTY_BLOCK = "  "


def read_maze(path_file: str) -> dict:
    """read maze.txt and return everything as a dict.

    Args:
        path_file: path to the maze file.

    Returns:
        dict with grid, height, width, entry, exit, solution, cells_42.
    """
    with open(path_file, "r") as f:
        lines = f.read().splitlines()
    sep = lines.index("")
    # grid 2d list
    grid = [[int(c, 16) for c in line] for line in lines[:sep]]
    meta = [line for line in lines[sep + 1:] if line.strip()]
    height = len(grid)
    width = len(grid[0])
    entry = tuple(map(int, meta[0].split(",")))
    exit_ = tuple(map(int, meta[1].split(",")))
    # solution
    if len(meta) > 2:
        solution = list(meta[2].strip())
    else:
        solution = []
    # find the 42 cells — fully closed ones
    cells_42 = set()
    for y in range(height):
        for x in range(width):
            if grid[y][x] == 0xF:
                cells_42.add((x, y))
    # returns everything as dict
    return {
        "grid":     grid,
        "height":   height,
        "width":    width,
        "entry":    entry,
        "exit":     exit_,
        "solution": solution,
        "cells_42": cells_42,
    }


def get_path_cells(entry: tuple, solution: list) -> set:
    """walk the solution and return all cells on the path.

    Args:
        entry: entry coordinates (x, y).
        solution: list of direction chars (N, E, S, W).

    Returns:
        set of (x, y) tuples on the solution path.
    """
    path_cells = set()
    x, y = entry
    path_cells.add((x, y))
    for c in solution:
        if c == "N":
            y -= 1
        elif c == "E":
            x += 1
        elif c == "S":
            y += 1
        elif c == "W":
            x -= 1
        path_cells.add((x, y))
    return path_cells


def draw_maze(maze: dict, show_path: bool, wall_color: str) -> None:
    """build the render grid and print the maze to the terminal.

    Args:
        maze: maze dict from read_maze().
        show_path: if True, highlight the solution path.
        wall_color: ANSI color string for walls.
    """
    grid = maze["grid"]
    height = maze["height"]
    width = maze["width"]
    entry = maze["entry"]
    exit_ = maze["exit"]
    solution = maze["solution"]
    cells_42 = maze["cells_42"]

    # control the path display
    path_cells: set = set()
    if show_path:
        path_cells = get_path_cells(entry, solution)

    # build render grid — fill everything with walls first
    render_grid = []
    for ry in range(height * 2 + 1):
        render_row = []
        for rx in range(width * 2 + 1):
            render_row.append(wall_color + WALL_BLOCK + RESET)
        render_grid.append(render_row)

    # loop over every cell
    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            ry = y * 2 + 1
            rx = x * 2 + 1

            # check if that cell is a 42 cell
            if (x, y) in cells_42:
                render_grid[ry][rx] = COLOR_42 + WALL_BLOCK + RESET
                # check if right neighbor is also a 42 cell
                if x + 1 < width and (x + 1, y) in cells_42:
                    render_grid[ry][rx + 1] = COLOR_42 + WALL_BLOCK + RESET
                # check if bottom neighbor is also a 42 cell
                if y + 1 < height and (x, y + 1) in cells_42:
                    render_grid[ry + 1][rx] = COLOR_42 + WALL_BLOCK + RESET

            # normal cell — black by default
            else:
                render_grid[ry][rx] = EMPTY_BLOCK

                # check if entry, exit or path cell
                if (x, y) == entry:
                    render_grid[ry][rx] = ENTRY_COLOR + EMPTY_BLOCK + RESET
                elif (x, y) == exit_:
                    render_grid[ry][rx] = EXIT_COLOR + EMPTY_BLOCK + RESET
                elif (x, y) in path_cells:
                    render_grid[ry][rx] = PATH_COLOR + EMPTY_BLOCK + RESET

                # check north passage
                if not (cell & NORTH) and y > 0:
                    both = (x, y) in path_cells and (x, y - 1) in path_cells
                    if both:
                        render_grid[ry - 1][rx] = (
                            PATH_COLOR + EMPTY_BLOCK + RESET
                        )
                    else:
                        # normal cell — black by default
                        render_grid[ry - 1][rx] = EMPTY_BLOCK

                # check south passage
                if not (cell & SOUTH) and y + 1 < height:
                    both = (x, y) in path_cells and (x, y + 1) in path_cells
                    if both:
                        render_grid[ry + 1][rx] = (
                            PATH_COLOR + EMPTY_BLOCK + RESET
                        )
                    else:
                        render_grid[ry + 1][rx] = EMPTY_BLOCK

                # check east passage
                if not (cell & EAST) and x + 1 < width:
                    both = (x, y) in path_cells and (x + 1, y) in path_cells
                    if both:
                        render_grid[ry][rx + 1] = (
                            PATH_COLOR + EMPTY_BLOCK + RESET
                        )
                    else:
                        render_grid[ry][rx + 1] = EMPTY_BLOCK

                # check west passage
                if not (cell & WEST) and x > 0:
                    both = (x, y) in path_cells and (x - 1, y) in path_cells
                    if both:
                        render_grid[ry][rx - 1] = (
                            PATH_COLOR + EMPTY_BLOCK + RESET
                        )
                    else:
                        render_grid[ry][rx - 1] = EMPTY_BLOCK

    # ── ADDED: open corner blocks between 4 open passages (imperfect maze fix)
    for cy in range(height):
        for cx in range(width):
            cry = cy * 2 + 1
            crx = cx * 2 + 1
            if cx + 1 < width and cy + 1 < height:
                if (render_grid[cry][crx + 1] == EMPTY_BLOCK
                        and render_grid[cry + 1][crx] == EMPTY_BLOCK
                        and render_grid[cry + 2][crx + 1] == EMPTY_BLOCK
                        and render_grid[cry + 1][crx + 2] == EMPTY_BLOCK):
                    render_grid[cry + 1][crx + 1] = EMPTY_BLOCK
    # ── END ADDED

    # print every row
    for row in render_grid:
        print("".join(row))


def print_info(maze_file: str, maze: dict, cfg: Any) -> None:
    """print maze info above the maze in one line.

    Args:
        maze_file: path to the maze file.
        maze: maze dict from read_maze().
        cfg: MazeConfig object from config_parser.
    """
    print(
        f"File: {maze_file}  |  "
        f"Size: {maze['width']}x{maze['height']}  |  "
        f"Entry: {maze['entry']}  |  "
        f"Exit: {maze['exit']}  |  "
        f"Seed: {cfg.seed}  |  "
        f"Perfect: {cfg.perfect}  |  "
        f"Algorithm: {cfg.algorithm}  |  "
        f"Solution: {len(maze['solution'])} steps"
    )
    print("─" * 80)


def run(maze_file: str) -> None:
    """main loop — draw the maze and handle user input.

    Args:
        maze_file: path to the maze file.
    """
    from config_parser import parse_config
    cfg = parse_config("config.txt")
    maze = read_maze(maze_file)
    show_path = False
    color_index = 0

    os.system("clear")
    print_info(maze_file, maze, cfg)
    draw_maze(maze, show_path, WALL_COLORS[color_index])
    print("=== A-Maze-ing ===")
    print("1. Re-generate a new maze")
    print("2. Show/Hide path from entry to exit")
    print("3. Rotate maze colors")
    print("4. Quit")

    # the loop
    while True:
        try:
            choice = input("Choice? (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            os.system("clear")
            break

        if choice == "1":
            os.system(
                f"{sys.executable} a_maze_ing.py config.txt --no-display"
            )
            maze = read_maze(maze_file)
            show_path = False
        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            color_index = (color_index + 1) % len(WALL_COLORS)
        elif choice == "4":
            os.system("clear")
            break
        else:
            continue

        # draw the maze after every valid choice
        os.system("clear")
        print_info(maze_file, maze, cfg)
        draw_maze(maze, show_path, WALL_COLORS[color_index])
        print("=== A-Maze-ing ===")
        print("1. Re-generate a new maze")
        print("2. Show/Hide path from entry to exit")
        print("3. Rotate maze colors")
        print("4. Quit")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 renderer.py maze.txt")
        sys.exit(1)
    if not os.path.isfile(sys.argv[1]):
        print(f"Error: file not found: {sys.argv[1]}")
        sys.exit(1)
    run(sys.argv[1])
