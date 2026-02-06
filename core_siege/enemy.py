"""Enemy logic and stats."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

Point = Tuple[float, float]


@dataclass
class EnemyStats:
    name: str
    max_hp: float
    speed: float
    reward: int
    flying: bool = False


ENEMY_TYPES = {
    "обычный": EnemyStats("Обычный", 40, 35, 10),
    "быстрый": EnemyStats("Быстрый", 25, 55, 12),
    "тяжёлый": EnemyStats("Тяжёлый", 100, 25, 20),
    "летающий": EnemyStats("Летающий", 35, 45, 15, flying=True),
}


class Enemy:
    """Single enemy following a path."""

    def __init__(self, stats: EnemyStats, path: List[Point]):
        self.stats = stats
        if stats.flying and len(path) > 1:
            self.path = [path[0], path[-1]]
        else:
            self.path = path
        self.hp = stats.max_hp
        self.position = [float(path[0][0]), float(path[0][1])]
        self.path_index = 0
        self.reached_end = False
        self.slow_factor = 1.0
        self.slow_timer = 0.0

    def is_alive(self) -> bool:
        return self.hp > 0

    def apply_damage(self, amount: float) -> None:
        self.hp -= amount

    def apply_slow(self, factor: float, duration: float) -> None:
        if factor < self.slow_factor:
            self.slow_factor = factor
            self.slow_timer = duration

    def update(self, dt: float) -> None:
        if not self.is_alive() or self.reached_end:
            return

        if self.slow_timer > 0:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.slow_factor = 1.0

        speed = self.stats.speed * self.slow_factor
        target_index = min(self.path_index + 1, len(self.path) - 1)
        target = self.path[target_index]
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        dist = (dx**2 + dy**2) ** 0.5
        if dist == 0:
            self.path_index = target_index
        else:
            step = speed * dt
            if step >= dist:
                self.position[0], self.position[1] = target
                self.path_index = target_index
            else:
                self.position[0] += dx / dist * step
                self.position[1] += dy / dist * step

        if self.path_index >= len(self.path) - 1 and dist < 1.0:
            self.reached_end = True

    def draw_color(self) -> Tuple[int, int, int]:
        if self.stats.flying:
            return (180, 220, 255)
        if self.stats.name == "Быстрый":
            return (255, 220, 100)
        if self.stats.name == "Тяжёлый":
            return (255, 120, 120)
        return (200, 200, 200)

    def size(self) -> int:
        return 14 if self.stats.flying else 16

    def center(self) -> Tuple[float, float]:
        return self.position[0], self.position[1]
