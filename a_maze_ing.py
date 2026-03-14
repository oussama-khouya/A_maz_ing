"""a_maze_ing.py - Main entry point.

Usage: python3 a_maze_ing.py config.txt
"""

import sys


def main() -> None:
    """Run the maze generator.

    Reads the config file, generates the maze, saves it,
    and launches the display unless --no-display is passed.
    """
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 a_maze_ing.py config.txt")

    # import config parser and maze generator
    from config_parser import parse_config
    from mazegen.maze_generator import MazeGenerator, MazeGenerationError

    # parse the config file
    cfg = parse_config(sys.argv[1])

    # generate the maze
    try:
        gen = MazeGenerator(
            width=cfg.width,
            height=cfg.height,
            seed=cfg.seed,
            perfect=cfg.perfect,
        )
        gen.generate(entry=cfg.entry, exit=cfg.exit)
        gen.save(cfg.output_file)
    except MazeGenerationError as e:
        sys.exit(f"Error: {e}")

    # launch display only if not called with --no-display
    if "--no-display" not in sys.argv:
        import renderer
        renderer.run(cfg.output_file)


if __name__ == "__main__":
    main()
