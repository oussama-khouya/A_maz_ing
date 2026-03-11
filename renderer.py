"""
renderer.py  -  Display the maze in the terminal.
Run: python3 renderer.py maze.txt
"""

import os
import sys
#import time

# ─────────────────────────────────────────────────────────────────────────────
# WALL BITS
# ─────────────────────────────────────────────────────────────────────────────
NORTH = 0x1
EAST  = 0x2
SOUTH = 0x4
WEST  = 0x8

# ─────────────────────────────────────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────────────────────────────────────
RESET = "\033[0m"

WALL_COLORS = [
    "\033[107m",   # White
    "\033[104m",   # Blue
    "\033[102m",   # Green
    "\033[105m",   # Magenta
]

ENTRY_COLOR = "\033[42m" #Green
EXIT_COLOR  = "\033[41m" #red
PATH_COLOR  = "\033[43m" #yallow
COLOR_42    = "\033[45m" #pink

WALL_BLOCK  = "  "
EMPTY_BLOCK = "  "


# ─────────────────────────────────────────────────────────────────────────────
# READ MAZE FILE
# ─────────────────────────────────────────────────────────────────────────────
def read_maze(filepath):
    with open(filepath) as f:
        lines = f.read().splitlines()

    sep      = lines.index("")
    grid     = [[int(c, 16) for c in row] for row in lines[:sep]]
    meta     = [l for l in lines[sep + 1:] if l.strip()]
    height   = len(grid)
    width    = len(grid[0])
    entry    = tuple(map(int, meta[0].split(",")))
    exit_    = tuple(map(int, meta[1].split(",")))
    solution = list(meta[2].strip()) if len(meta) > 2 else []

    cells_42 = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if grid[y][x] == 0xF
    }

    return {
        "grid":     grid,
        "width":    width,
        "height":   height,
        "entry":    entry,
        "exit":     exit_,
        "solution": solution,
        "cells_42": cells_42,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET PATH CELLS
# ─────────────────────────────────────────────────────────────────────────────
def get_path_cells(entry, solution):
    cells = set()
    x, y  = entry
    cells.add((x, y))
    for d in solution:
        if   d == "N": y -= 1
        elif d == "S": y += 1
        elif d == "E": x += 1
        elif d == "W": x -= 1
        cells.add((x, y))
    return cells


# ─────────────────────────────────────────────────────────────────────────────
# DRAW MAZE
# ─────────────────────────────────────────────────────────────────────────────
def draw_maze(maze, show_path, wall_color):
    grid     = maze["grid"]
    width    = maze["width"]
    height   = maze["height"]
    entry    = maze["entry"]
    exit_    = maze["exit"]
    cells_42 = maze["cells_42"]

    path_cells = set()
    if show_path:
        path_cells = get_path_cells(entry, maze["solution"])

    render = [
        [wall_color + WALL_BLOCK + RESET  for _ in range(2 * width + 1)]
        for _ in range(2 * height + 1)
    ]

    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            ry   = y * 2 + 1
            rx   = x * 2 + 1

            if (x, y) in cells_42:
                render[ry][rx] = COLOR_42 + WALL_BLOCK + RESET
                if x + 1 < width and (x + 1, y) in cells_42:
                    render[ry][rx + 1] = COLOR_42 + WALL_BLOCK + RESET
                if y + 1 < height and (x, y + 1) in cells_42:
                    render[ry + 1][rx] = COLOR_42 + WALL_BLOCK + RESET
            else:
                render[ry][rx] = EMPTY_BLOCK

                if   (x, y) == entry:      render[ry][rx] = ENTRY_COLOR + EMPTY_BLOCK + RESET
                elif (x, y) == exit_:      render[ry][rx] = EXIT_COLOR  + EMPTY_BLOCK + RESET
                elif (x, y) in path_cells: render[ry][rx] = PATH_COLOR  + EMPTY_BLOCK + RESET

                if not (cell & NORTH) and y > 0:
                    both = (x, y) in path_cells and (x, y - 1) in path_cells
                    render[ry - 1][rx] = PATH_COLOR + EMPTY_BLOCK + RESET if both else EMPTY_BLOCK

                if not (cell & SOUTH) and y + 1 < height:
                    both = (x, y) in path_cells and (x, y + 1) in path_cells
                    render[ry + 1][rx] = PATH_COLOR + EMPTY_BLOCK + RESET if both else EMPTY_BLOCK

                if not (cell & EAST) and x + 1 < width:
                    both = (x, y) in path_cells and (x + 1, y) in path_cells
                    render[ry][rx + 1] = PATH_COLOR + EMPTY_BLOCK + RESET if both else EMPTY_BLOCK

                if not (cell & WEST) and x > 0:
                    both = (x, y) in path_cells and (x - 1, y) in path_cells
                    render[ry][rx - 1] = PATH_COLOR + EMPTY_BLOCK + RESET if both else EMPTY_BLOCK

    for row in render:
        print("".join(row))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────
def run(maze_file):
    maze        = read_maze(maze_file)
    show_path   = False
    color_index = 0

    os.system("clear")
    draw_maze(maze, show_path, WALL_COLORS[color_index])
    print("=== A-Maze-ing ===")
    print("1. Re-generate a new maze")
    print("2. Show/Hide path from entry to exit")
    print("3. Rotate maze colors")
    print("4. Quit")

    while True:
        try:
            choice = input("Choice? (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "1":
            os.system(f"{sys.executable} a_maze_ing.py config.txt --no-display")
            maze = read_maze(maze_file)
            show_path = False

        elif choice == "2":
            show_path = not show_path

        elif choice == "3":
            color_index = (color_index + 1) % len(WALL_COLORS)

        elif choice == "4":
            break

        else:
            continue

        # redraw once after every valid choice
        os.system("clear")
        draw_maze(maze, show_path, WALL_COLORS[color_index])
        print("=== A-Maze-ing ===")
        print("1. Re-generate a new maze")
        print("2. Show/Hide path from entry to exit")
        print("3. Rotate maze colors")
        print("4. Quit")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 renderer.py maze.txt")
        sys.exit(1)
    if not os.path.isfile(sys.argv[1]):
        print(f"Error: file not found: {sys.argv[1]}")
        sys.exit(1)
    run(sys.argv[1])