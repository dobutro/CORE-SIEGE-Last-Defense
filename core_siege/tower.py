"""Tower logic and upgrades."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .enemy import Enemy
from .projectile import Projectile


@dataclass
class TowerStats:
    name: str
    damage: float
    range: float
    rate: float
    color: Tuple[int, int, int]
    cost: int
    projectile_speed: float = 0.0
    slow_factor: float = 1.0
    slow_duration: float = 0.0
    splash_radius: float = 0.0
    laser: bool = False
    flying_only: bool = False
    ground_only: bool = False
    upgrade_order: Tuple[str, ...] = ("damage", "rate", "range")


TOWER_TYPES: Dict[str, TowerStats] = {
    "пулемётная": TowerStats(
        "Пулемётная",
        6,
        150,
        4.0,
        (120, 200, 255),
        45,
        projectile_speed=200,
        upgrade_order=("rate", "damage", "range"),
    ),
    "лазерная": TowerStats(
        "Лазерная",
        10,
        140,
        6.0,
        (255, 80, 200),
        70,
        laser=True,
        upgrade_order=("damage", "range"),
    ),
    "замедляющая": TowerStats(
        "Замедляющая",
        2,
        120,
        1.8,
        (120, 255, 160),
        55,
        projectile_speed=170,
        slow_factor=0.6,
        slow_duration=2.5,
        ground_only=True,
        upgrade_order=("range", "rate"),
    ),
    "ракетная": TowerStats(
        "Ракетная",
        30,
        170,
        0.8,
        (255, 160, 80),
        90,
        projectile_speed=160,
        splash_radius=40,
        ground_only=True,
        upgrade_order=("damage", "range"),
    ),
}


class Tower:
    """A single tower that can attack enemies and be upgraded."""

    def __init__(self, tower_type: TowerStats, position: Tuple[int, int]):
        self.base_stats = tower_type
        self.position = position
        self.level = 1
        self.cooldown = 0.0
        self.target: Optional[Enemy] = None
        self.invested = tower_type.cost

        self.damage_bonus = 0.0
        self.rate_bonus = 0.0
        self.range_bonus = 0.0
        self.upgrade_step = 0

    def total_damage(self) -> float:
        return self.base_stats.damage + self.damage_bonus

    def total_rate(self) -> float:
        return self.base_stats.rate + self.rate_bonus

    def total_range(self) -> float:
        return self.base_stats.range + self.range_bonus

    def update(self, dt: float, enemies: List[Enemy]) -> List[Projectile]:
        projectiles: List[Projectile] = []
        if self.cooldown > 0:
            self.cooldown -= dt
        self.target = self.find_target(enemies)
        if not self.target:
            return projectiles

        if self.base_stats.laser:
            self.target.apply_damage(self.total_damage() * dt)
            return projectiles

        if self.cooldown <= 0:
            self.cooldown = 1.0 / self.total_rate()
            projectile = Projectile(
                position=[self.position[0], self.position[1]],
                target=self.target,
                speed=self.base_stats.projectile_speed,
                damage=self.total_damage(),
                splash_radius=self.base_stats.splash_radius,
            )
            projectiles.append(projectile)
        return projectiles

    def apply_effects(self, enemy: Enemy) -> None:
        if self.base_stats.slow_duration > 0:
            enemy.apply_slow(self.base_stats.slow_factor, self.base_stats.slow_duration)

    def find_target(self, enemies: List[Enemy]) -> Optional[Enemy]:
        for enemy in enemies:
            if not enemy.is_alive():
                continue
            if self.base_stats.ground_only and enemy.stats.flying:
                continue
            if self.base_stats.flying_only and not enemy.stats.flying:
                continue
            if self.distance_to(enemy) <= self.total_range():
                return enemy
        return None

    def distance_to(self, enemy: Enemy) -> float:
        ex, ey = enemy.center()
        dx = ex - self.position[0]
        dy = ey - self.position[1]
        return (dx**2 + dy**2) ** 0.5

    def upgrade_cost(self) -> int:
        return int(self.base_stats.cost * (1.5 ** self.level))

    def next_upgrade(self) -> Optional[str]:
        if self.upgrade_step >= len(self.base_stats.upgrade_order):
            return None
        return self.base_stats.upgrade_order[self.upgrade_step]

    def upgrade(self) -> Optional[str]:
        upgrade_type = self.next_upgrade()
        if not upgrade_type:
            return None
        if upgrade_type == "damage":
            self.damage_bonus += self.base_stats.damage * 0.3
        elif upgrade_type == "rate":
            self.rate_bonus += self.base_stats.rate * 0.2
        elif upgrade_type == "range":
            self.range_bonus += self.base_stats.range * 0.1
        self.invested += self.upgrade_cost()
        self.level += 1
        self.upgrade_step += 1
        return upgrade_type

    def upgrade_damage(self) -> None:
        self.damage_bonus += self.base_stats.damage * 0.3
        self.invested += self.upgrade_cost()
        self.level += 1

    def upgrade_rate(self) -> None:
        self.rate_bonus += self.base_stats.rate * 0.2
        self.invested += self.upgrade_cost()
        self.level += 1

    def upgrade_range(self) -> None:
        self.range_bonus += self.base_stats.range * 0.1
        self.invested += self.upgrade_cost()
        self.level += 1

    def sell_value(self) -> int:
        return int(self.invested * 0.6)
