"""
a_maze_ing.py - Main entry point.
Usage: python3 a_maze_ing.py config.txt
"""

import sys
import os


def parse_config(filepath):
    if not os.path.isfile(filepath):
        sys.exit(f"Error: config file not found: {filepath}")

    config = {}
    with open(filepath) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                sys.exit(f"Error: line {lineno} invalid: '{line}'")
            key, _, value = line.partition("=")
            config[key.strip()] = value.strip()

    required = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"]
    for key in required:
        if key not in config:
            sys.exit(f"Error: missing key '{key}' in config.")

    try:
        width  = int(config["WIDTH"])
        height = int(config["HEIGHT"])
    except ValueError:
        sys.exit("Error: WIDTH and HEIGHT must be integers.")

    try:
        entry = tuple(map(int, config["ENTRY"].split(",")))
        exit_ = tuple(map(int, config["EXIT"].split(",")))
    except ValueError:
        sys.exit("Error: ENTRY and EXIT must be x,y format.")

    perfect = config["PERFECT"].strip().lower() == "true"
    seed = int(config["SEED"]) if "SEED" in config else None

    return {
        "width":       width,
        "height":      height,
        "entry":       entry,
        "exit":        exit_,
        "output_file": config["OUTPUT_FILE"],
        "perfect":     perfect,
        "seed":        seed,
    }


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 a_maze_ing.py config.txt")

    cfg = parse_config(sys.argv[1])

    # Import the generator from config_parser.py
    from config_parser import MazeGenerator, MazeGenerationError

    try:
        gen = MazeGenerator(cfg["width"], cfg["height"], seed=cfg["seed"])
        gen.generate(entry=cfg["entry"], exit=cfg["exit"])
        gen.save(cfg["output_file"])
        print(f"Maze generated: {cfg['width']}x{cfg['height']} "
              f"| seed={gen.seed} "
              f"| solution={len(gen.solution)} steps "
              f"| output={cfg['output_file']}")
    except MazeGenerationError as e:
        sys.exit(f"Error: {e}")

    # Launch display only if not called with --no-display
    if "--no-display" not in sys.argv:
        import renderer
        renderer.run(cfg["output_file"])


if __name__ == "__main__":
    main()