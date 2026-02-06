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
    desert_path = [(0, 6), (19, 6)]
    maze_path = [(0, 2), (6, 2), (6, 11), (12, 11), (12, 4), (19, 4)]
    city_path = [(0, 3), (7, 3), (7, 9), (19, 9)]
    tundra_path = [(0, 7), (9, 7), (9, 2), (19, 2)]
    canyon_path = [(0, 12), (5, 12), (5, 6), (14, 6), (14, 10), (19, 10)]
    factory_path = [(0, 5), (4, 5), (4, 10), (10, 10), (10, 3), (19, 3)]
    return [
        Level("Пустыня", 20, 14, cell_size, desert_path),
        Level("Лабиринт", 20, 14, cell_size, maze_path),
        Level("Город", 20, 14, cell_size, city_path),
        Level("Тундра", 20, 14, cell_size, tundra_path),
        Level("Каньон", 20, 14, cell_size, canyon_path),
        Level("Фабрика", 20, 14, cell_size, factory_path),
    ]
