"""Projectile behavior for towers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Projectile:
    """Simple projectile that moves in a straight line."""

    position: list
    velocity: Tuple[float, float]
    damage: float
    splash_radius: float = 0.0
    alive: bool = True
    radius: int = 3
    can_hit_flying: bool = True
    can_hit_ground: bool = True

    def update(self, dt: float, bounds: Tuple[int, int]) -> None:
        if not self.alive:
            return
        self.position[0] += self.velocity[0] * dt
        self.position[1] += self.velocity[1] * dt
        if (
            self.position[0] < 0
            or self.position[1] < 0
            or self.position[0] > bounds[0]
            or self.position[1] > bounds[1]
        ):
            self.alive = False

    def center(self) -> Tuple[float, float]:
        return self.position[0], self.position[1]
