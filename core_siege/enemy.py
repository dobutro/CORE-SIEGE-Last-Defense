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
    shield_hp: float = 0.0
    healer: bool = False
    heal_amount: float = 0.0
    heal_radius: float = 0.0
    heal_cooldown: float = 0.0


ENEMY_TYPES = {
    "обычный": EnemyStats("Обычный", 40, 35, 10),
    "быстрый": EnemyStats("Быстрый", 25, 55, 12),
    "тяжёлый": EnemyStats("Тяжёлый", 100, 25, 20),
    "летающий": EnemyStats("Летающий", 35, 45, 15, flying=True),
    "истребитель": EnemyStats("Истребитель", 55, 70, 22, flying=True),
    "хиллер": EnemyStats(
        "Хиллер",
        70,
        30,
        18,
        healer=True,
        heal_amount=6,
        heal_radius=70,
        heal_cooldown=3.0,
    ),
    "щитоносец": EnemyStats("Щитоносец", 80, 28, 24, shield_hp=50),
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
        self.shield_hp = stats.shield_hp
        self.position = [float(path[0][0]), float(path[0][1])]
        self.path_index = 0
        self.reached_end = False
        self.slow_factor = 1.0
        self.slow_timer = 0.0
        self.heal_timer = 0.0
        self.took_damage = False

    def is_alive(self) -> bool:
        return self.hp > 0

    def apply_damage(self, amount: float) -> None:
        self.took_damage = True
        if self.shield_hp > 0:
            absorbed = min(self.shield_hp, amount)
            self.shield_hp -= absorbed
            amount -= absorbed
        if amount > 0:
            self.hp -= amount

    def apply_slow(self, factor: float, duration: float) -> None:
        if factor < self.slow_factor:
            self.slow_factor = factor
            self.slow_timer = duration

    def apply_heal(self, amount: float) -> None:
        if self.stats.flying:
            return
        if self.hp <= 0:
            return
        self.hp = min(self.stats.max_hp, self.hp + amount)

    def update(self, dt: float) -> None:
        if not self.is_alive() or self.reached_end:
            return

        if self.slow_timer > 0:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.slow_factor = 1.0

        if self.stats.healer:
            self.heal_timer = max(0.0, self.heal_timer - dt)

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
            if self.stats.name == "Истребитель":
                return (120, 180, 255)
            return (180, 220, 255)
        if self.stats.name == "Хиллер":
            return (120, 255, 180)
        if self.stats.name == "Щитоносец":
            return (170, 170, 200)
        if self.stats.name == "Быстрый":
            return (255, 220, 100)
        if self.stats.name == "Тяжёлый":
            return (255, 120, 120)
        return (200, 200, 200)

    def size(self) -> int:
        return 10 if self.stats.flying else 12

    def can_heal(self) -> bool:
        return self.stats.healer and self.heal_timer <= 0.0

    def reset_heal_timer(self) -> None:
        self.heal_timer = self.stats.heal_cooldown

    def center(self) -> Tuple[float, float]:
        return self.position[0], self.position[1]
