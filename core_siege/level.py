"""Level data and helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

Point = Tuple[int, int]


@dataclass
class Level:
    """Represents a map layout with a fixed enemy path."""

    name: str
    grid_width: int
    grid_height: int
    cell_size: int
    path: List[Point]

    @property
    def pixel_width(self) -> int:
        return self.grid_width * self.cell_size

    @property
    def pixel_height(self) -> int:
        return self.grid_height * self.cell_size

    def path_pixels(self) -> List[Point]:
        return [(x * self.cell_size + self.cell_size // 2, y * self.cell_size + self.cell_size // 2) for x, y in self.path]


def build_levels(cell_size: int) -> List[Level]:
    """Create the three requested levels."""
    desert_path = [(0, 5), (15, 5)]
    maze_path = [(0, 2), (5, 2), (5, 9), (10, 9), (10, 4), (15, 4)]
    city_path = [(0, 3), (6, 3), (6, 8), (15, 8)]
    return [
        Level("Пустыня", 16, 12, cell_size, desert_path),
        Level("Лабиринт", 16, 12, cell_size, maze_path),
        Level("Город", 16, 12, cell_size, city_path),
    ]
