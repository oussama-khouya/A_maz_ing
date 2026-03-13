"""config_parser.py - reads and validates the maze config file."""

import sys
from pathlib import Path
from typing import Optional


REQUIRED_KEYS: frozenset[str] = frozenset(
    {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT", "ALGORITHM"}
)


class ConfigError(Exception):
    """raised when the config file has bad or missing values."""

    pass


class MazeConfig:
    """holds all the settings parsed from the config file."""

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit_: tuple[int, int],
        output_file: str,
        perfect: bool,
        seed: Optional[int] = None,
        algorithm: str = "dfs",
    ) -> None:
        """store each config value as an attribute.

        Args:
            width: maze width in cells.
            height: maze height in cells.
            entry: entry coordinates (x, y).
            exit_: exit coordinates (x, y).
            output_file: path to write the maze to.
            perfect: if True, only one path between entry and exit.
            seed: random seed for reproducibility.
            algorithm: generation algorithm (dfs, prim, kruskal).
        """
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit_
        self.output_file = output_file
        self.perfect = perfect
        self.seed = seed
        self.algorithm = algorithm

    def __repr__(self) -> str:
        """return a readable string of the config."""
        return (
            f"MazeConfig(width={self.width}, height={self.height}, "
            f"entry={self.entry}, exit={self.exit}, "
            f"perfect={self.perfect}, seed={self.seed})"
        )


def parse_config(filepath: str) -> MazeConfig:
    """read the config file and return a MazeConfig object.

    Args:
        filepath: path to the config file.

    Returns:
        a MazeConfig with all the values from the file.
    """
    path = Path(filepath)
    if not path.exists():
        raise ConfigError(f"File not found: '{filepath}'")
    if not path.is_file():
        raise ConfigError(f"Not a regular file: '{filepath}'")

    raw: dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in stripped:
                    raise ConfigError(
                        f"Line {lineno}: expected KEY=VALUE, got: {line!r}"
                    )
                key, _, value = stripped.partition("=")
                key = key.strip().upper()
                value = value.strip()
                if not key:
                    raise ConfigError(f"Line {lineno}: empty key")
                raw[key] = value
    except (OSError, ConfigError) as exc:
        if exc.__class__.__name__ == "ConfigError":
            print(exc)
            sys.exit(1)
        else:
            print(f"Cannot read '{filepath}': {exc}")
            sys.exit(1)

    missing = REQUIRED_KEYS - raw.keys()
    try:
        if missing:
            raise ConfigError(
                f"Missing required keys: {', '.join(sorted(missing))}"
            )
    except ConfigError as e:
        print(e)
        sys.exit(1)

    try:
        cfg = _build_config(raw)
        return cfg
    except ConfigError as e:
        print(e)
        sys.exit(1)


def _build_config(raw: dict[str, str]) -> MazeConfig:
    """build a MazeConfig from the raw key/value dict.

    Args:
        raw: dict of key/value strings from the config file.

    Returns:
        a validated MazeConfig object.
    """
    width = _int(raw, "WIDTH", minimum=2)
    height = _int(raw, "HEIGHT", minimum=2)
    entry = _coord(raw, "ENTRY", width, height)
    exit_ = _coord(raw, "EXIT", width, height)
    if entry == exit_:
        raise ConfigError("ENTRY and EXIT must be different cells.")
    output_file = raw["OUTPUT_FILE"].strip()
    if not output_file:
        raise ConfigError("OUTPUT_FILE must not be empty.")
    perfect = _bool(raw, "PERFECT")
    seed: Optional[int] = None
    if "SEED" in raw:
        seed = _int(raw, "SEED", minimum=0)
    algorithm = raw.get("ALGORITHM", "dfs").lower().strip()
    if algorithm not in {"dfs"}:
        raise ConfigError(
            f"Unknown ALGORITHM '{algorithm}'. Supported: dfs"
        )
    return MazeConfig(
        width=width,
        height=height,
        entry=entry,
        exit_=exit_,
        output_file=output_file,
        perfect=perfect,
        seed=seed,
        algorithm=algorithm,
    )


def _int(raw: dict[str, str], key: str, minimum: int) -> int:
    """parse an integer value from raw config.

    Args:
        raw: the full raw config dict.
        key: the key to read.
        minimum: minimum allowed value.

    Returns:
        the parsed integer.
    """
    try:
        v = int(raw[key])
    except ValueError:
        raise ConfigError(f"{key}: expected integer, got {raw[key]!r}")
    if v < minimum:
        raise ConfigError(f"{key} must be >= {minimum}, got {v}")
    return v


def _coord(
    raw: dict[str, str], key: str, w: int, h: int
) -> tuple[int, int]:
    """parse a coordinate pair from raw config.

    Args:
        raw: the full raw config dict.
        key: the key to read.
        w: maze width for bounds check.
        h: maze height for bounds check.

    Returns:
        a (x, y) tuple.
    """
    parts = raw[key].split(",")
    if len(parts) != 2:
        raise ConfigError(f"{key}: expected 'x,y', got {raw[key]!r}")
    try:
        x, y = int(parts[0].strip()), int(parts[1].strip())
    except ValueError:
        raise ConfigError(f"{key}: coordinates must be integers")
    if not (0 <= x < w and 0 <= y < h):
        raise ConfigError(
            f"{key} ({x},{y}) out of bounds (0..{w - 1} x 0..{h - 1})"
        )
    return (x, y)


def _bool(raw: dict[str, str], key: str) -> bool:
    """parse a boolean value from raw config.

    Args:
        raw: the full raw config dict.
        key: the key to read.

    Returns:
        True or False.
    """
    v = raw[key].strip().lower()
    if v in {"true", "1", "yes"}:
        return True
    if v in {"false", "0", "no"}:
        return False
    raise ConfigError(f"{key}: expected True/False, got {raw[key]!r}")


def generate_default_config(filepath: str = "config.txt") -> None:
    """write a default config file to disk.

    Args:
        filepath: where to write the config file.
    """
    content = (
        "# A-Maze-ing configuration\n"
        "WIDTH=20\n"
        "HEIGHT=15\n"
        "ENTRY=0,0\n"
        "EXIT=19,14\n"
        "OUTPUT_FILE=maze.txt\n"
        "PERFECT=True\n"
        "# SEED=42\n"
        "# ALGORITHM=dfs\n"
    )
    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"Default config written to '{filepath}'.")
