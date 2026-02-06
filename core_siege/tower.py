"""Tower logic and upgrades."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import math

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
    projectile_radius: int = 3
    slow_factor: float = 1.0
    slow_duration: float = 0.0
    splash_radius: float = 0.0
    laser: bool = False
    flying_only: bool = False
    ground_only: bool = False
    upgrade_order: Tuple[str, ...] = ("damage", "rate", "range")
    multi_shot: int = 1
    spread_deg: float = 0.0
    warmup_time: float = 0.0
    weapon_class: int = 1


TOWER_TYPES: Dict[str, TowerStats] = {
    "пулемётная": TowerStats(
        "Пулемётная",
        6,
        150,
        4.0,
        (120, 200, 255),
        45,
        projectile_speed=200,
        projectile_radius=3,
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
        ground_only=True,
        upgrade_order=("damage", "range"),
    ),
    "зенит": TowerStats(
        "Зенит",
        5,
        150,
        5.5,
        (140, 200, 255),
        65,
        projectile_speed=220,
        projectile_radius=3,
        flying_only=True,
        upgrade_order=("rate", "damage", "range"),
        multi_shot=3,
        spread_deg=10.0,
    ),
    "даль": TowerStats(
        "Даль",
        20,
        260,
        0.7,
        (210, 200, 120),
        85,
        projectile_speed=190,
        projectile_radius=4,
        ground_only=True,
        upgrade_order=("range", "damage"),
    ),
    "замедляющая": TowerStats(
        "Замедляющая",
        2,
        120,
        1.8,
        (120, 255, 160),
        55,
        projectile_speed=170,
        projectile_radius=3,
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
        projectile_radius=4,
        splash_radius=40,
        ground_only=True,
        upgrade_order=("damage", "range"),
    ),
    "испепеление": TowerStats(
        "Испепеление",
        16,
        180,
        7.5,
        (20, 20, 20),
        160,
        projectile_speed=320,
        projectile_radius=3,
        upgrade_order=("damage", "rate"),
        warmup_time=1.0,
        weapon_class=2,
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
        self.warmup_timer = 0.0
        self.is_warming = False

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

    def update(self, dt: float, enemies: List[Enemy], base_position: Tuple[float, float]) -> List[Projectile]:
        projectiles: List[Projectile] = []
        if self.cooldown > 0:
            self.cooldown -= dt
        self.target = self.find_target(enemies, base_position)
        if not self.target:
            self.is_warming = False
            self.warmup_timer = 0.0
            return projectiles

        if self.base_stats.laser:
            self.target.apply_damage(self.total_damage() * dt)
            return projectiles

        if self.base_stats.warmup_time > 0 and not self.is_warming:
            self.is_warming = True
            self.warmup_timer = self.base_stats.warmup_time

        if self.is_warming:
            self.warmup_timer -= dt
            if self.warmup_timer > 0:
                return projectiles
            self.is_warming = False

        if self.cooldown <= 0:
            self.cooldown = 1.0 / self.total_rate()
            projectiles.extend(self.create_projectiles(self.target))
        return projectiles

    def apply_effects(self, enemy: Enemy) -> None:
        if self.base_stats.slow_duration > 0:
            enemy.apply_slow(self.base_stats.slow_factor, self.base_stats.slow_duration)

    def find_target(self, enemies: List[Enemy], base_position: Tuple[float, float]) -> Optional[Enemy]:
        closest: Optional[Enemy] = None
        closest_distance = float("inf")
        for enemy in enemies:
            if not enemy.is_alive():
                continue
            if self.base_stats.ground_only and enemy.stats.flying:
                continue
            if self.base_stats.flying_only and not enemy.stats.flying:
                continue
            if self.distance_to(enemy) <= self.total_range():
                distance_to_base = self.distance_to_point(enemy.center(), base_position)
                if distance_to_base < closest_distance:
                    closest_distance = distance_to_base
                    closest = enemy
        return closest

    def distance_to(self, enemy: Enemy) -> float:
        ex, ey = enemy.center()
        dx = ex - self.position[0]
        dy = ey - self.position[1]
        return (dx**2 + dy**2) ** 0.5

    def distance_to_point(self, point: Tuple[float, float], other: Tuple[float, float]) -> float:
        dx = point[0] - other[0]
        dy = point[1] - other[1]
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

    def create_projectiles(self, target: Enemy) -> List[Projectile]:
        tx, ty = target.center()
        dx = tx - self.position[0]
        dy = ty - self.position[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1.0
        direction = (dx / dist, dy / dist)
        projectiles: List[Projectile] = []
        shots = self.base_stats.multi_shot
        spread = math.radians(self.base_stats.spread_deg)
        angles = [0.0]
        if shots > 1:
            angles = [spread * (i - (shots - 1) / 2) for i in range(shots)]
        for angle in angles:
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            vx = direction[0] * cos_a - direction[1] * sin_a
            vy = direction[0] * sin_a + direction[1] * cos_a
            projectiles.append(
                Projectile(
                    position=[self.position[0], self.position[1]],
                    velocity=(vx * self.base_stats.projectile_speed, vy * self.base_stats.projectile_speed),
                    damage=self.total_damage(),
                    splash_radius=self.base_stats.splash_radius,
                    radius=self.base_stats.projectile_radius,
                )
            )
        return projectiles
