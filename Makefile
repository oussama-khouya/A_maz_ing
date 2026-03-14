.PHONY: install run debug clean lint  build


run:
	python3 a_maze_ing.py config.txt

install:
	pip install ".[dev]"


debug:
	python3 -m pdb a_maze_ing.py config.txt

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	rm -rf .mypy_cache dist build *.egg-info .pytest_cache
	rm -f maze.txt

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
	       --disallow-untyped-defs --check-untyped-defs


build:
	pip install build
	python3 -m build