"""Projectile behavior for towers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .enemy import Enemy


@dataclass
class Projectile:
    """Simple projectile that moves toward a target."""

    position: list
    target: Enemy
    speed: float
    damage: float
    splash_radius: float = 0.0
    alive: bool = True

    def update(self, dt: float) -> None:
        if not self.alive or not self.target.is_alive():
            self.alive = False
            return
        tx, ty = self.target.center()
        dx = tx - self.position[0]
        dy = ty - self.position[1]
        dist = (dx**2 + dy**2) ** 0.5
        if dist < 1:
            self.alive = False
            return
        step = self.speed * dt
        if step >= dist:
            self.position[0], self.position[1] = tx, ty
            self.alive = False
        else:
            self.position[0] += dx / dist * step
            self.position[1] += dy / dist * step

    def hits_target(self) -> bool:
        return not self.alive

    def center(self) -> Tuple[float, float]:
        return self.position[0], self.position[1]
