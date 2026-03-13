*This project has been created as part of the 42 curriculum by okhouya, aghoudan.*

# A-Maze-ing

## Description

A-Maze-ing is a maze generator written in Python. You give it a config file, it generates a maze, saves it to a file in hex format, and displays it in the terminal with colors. The maze can be perfect (one path) or imperfect (multiple paths). It always contains a "42" pattern made of fully closed cells somewhere in the middle.

## Instructions

### Requirements

- Python 3.10 or later
- pip

### Install

```bash
make install
```

### Run

```bash
make run
```

Or directly:

```bash
python3 a_maze_ing.py config.txt
```

### Controls

Once the maze is displayed:

```
1 — generate a new maze
2 — show / hide the solution path
3 — cycle wall colors
4 — quit
```

### Other commands

```bash
make debug        # run with pdb debugger
make lint         # run flake8 and mypy
make lint-strict  # run mypy --strict (optional)
make clean        # remove generated files and caches
make build        # build the pip package
```

## Config file format

The config file uses `KEY=VALUE` pairs, one per line. Lines starting with `#` are comments.

```
# A-Maze-ing configuration
WIDTH=24          # maze width in cells (minimum 2)
HEIGHT=24         # maze height in cells (minimum 2)
ENTRY=0,0         # entry coordinates x,y
EXIT=23,23        # exit coordinates x,y
OUTPUT_FILE=maze.txt  # where to write the maze
PERFECT=True      # True = one path, False = multiple paths
ALGORITHM=dfs     # dfs / prim / kruskal
# SEED=42         # optional, for reproducibility
```

All keys except SEED are mandatory.

## Output file format

Each cell is one hex digit encoding which walls are closed:

```
Bit 0 (LSB) → North
Bit 1       → East
Bit 2       → South
Bit 3       → West
```

Cells are written row by row, one row per line. After an empty line, the file contains the entry coordinates, exit coordinates, and the solution path using N/E/S/W characters.

## Algorithm

We used **DFS (Depth-First Search)** for maze generation.

### Why DFS

DFS was the natural first choice — it is simple to implement, easy to debug, and produces mazes with long winding corridors which look good visually. It also works well with the 42 pattern constraint since we can just skip the 42 cells during carving. We also implemented Prim and Kruskal as options in the config file but DFS is the default.

## Reusable module

The maze generation logic lives entirely in `maze_generator.py`. It can be installed as a standalone pip package:

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

Then used in any Python project:

```python
from maze_generator import MazeGenerator

gen = MazeGenerator(width=20, height=15, seed=42, perfect=True)
gen.generate(entry=(0, 0), exit=(19, 14))

# access the grid
print(gen.grid)

# access the solution
print(gen.solutions[0])

# save to file
gen.save("maze.txt")
```

Custom parameters:

```python
MazeGenerator(
    width=20,       # number of cells horizontally
    height=15,      # number of cells vertically
    seed=42,        # optional seed for reproducibility
    perfect=True,   # True = perfect maze one path, False = multiple paths
)
```

## Team and project management

### Roles

- **okhouya** — terminal renderer (`renderer.py`), main entry point (`a_maze_ing.py`), config file, Makefile, packaging
- **aghoudan** — maze generation (`maze_generator.py`), BFS solver, config parser (`config_parser.py`)

### Planning

We started by agreeing on the output file format and the interface between the two parts so we could work independently. aghoudan worked on the generation and parsing while okhouya worked on the display. We connected the two parts once both sides were working and fixed the integration bugs together.

Originally we planned to finish the display faster but getting the render grid coordinates right took more time than expected. We also spent time on the 42 pattern and making sure it showed correctly in the terminal.

### What worked well

- Splitting the work cleanly by file made it easy to work in parallel without conflicts
- Agreeing on the maze.txt format early meant integration was smooth
- The hex format for the grid made reading and writing the file simple

### What could be improved

- We could have written tests earlier to catch bugs faster
- The imperfect maze solver (`_find_all_solutions`) can be slow on large mazes

### Tools used

- **Git / GitHub** — version control and collaboration
- **VS Code** — code editor
- **Claude (Anthropic)** — used for help understanding flake8 and mypy errors, explaining packaging concepts (pyproject.toml, pip, .whl format), and reviewing code style. All logic and implementation decisions were made by us.

## Resources

- [Python docs — random module](https://docs.python.org/3/library/random.html)
- [Maze generation algorithms — Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Depth-first search — Wikipedia](https://en.wikipedia.org/wiki/Depth-first_search)
- [Breadth-first search — Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search)
- [Python packaging guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [mypy documentation](https://mypy.readthedocs.io/en/stable/)
- [flake8 documentation](https://flake8.pycqa.org/en/latest/)
- [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code)