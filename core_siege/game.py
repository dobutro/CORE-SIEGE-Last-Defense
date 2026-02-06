"""Game state and wave management."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .enemy import ENEMY_TYPES, Enemy
from .level import Level
from .projectile import Projectile
from .tower import TOWER_TYPES, Tower


@dataclass
class WaveConfig:
    enemies: List[str]


class GameState:
    """Manages the active game session."""

    def __init__(self, level: Level):
        self.level = level
        self.base_hp = 20
        self.money = 120
        self.wave_number = 0
        self.wave_in_progress = False
        self.paused = False
        self.enemies: List[Enemy] = []
        self.towers: List[Tower] = []
        self.projectiles: List[Projectile] = []
        self.pending_enemies: List[Enemy] = []
        self.spawn_timer = 0.0
        self.selected_tower_key = "пулемётная"
        self.game_over = False
        self.wave_cooldown = 0.0
        self.explosions: List[Tuple[float, float, float]] = []

        self.path_pixels = self.level.path_pixels()

    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def build_wave(self) -> WaveConfig:
        wave_size = 6 + self.wave_number * 2
        enemies: List[str] = []
        for i in range(wave_size):
            if self.wave_number >= 3 and i % 5 == 0:
                enemies.append("тяжёлый")
            elif self.wave_number >= 2 and i % 4 == 0:
                enemies.append("быстрый")
            else:
                enemies.append("обычный")
        if self.wave_number >= 4:
            enemies.append("летающий")
        if self.wave_number >= 6:
            enemies.append("хиллер")
        if self.wave_number >= 7:
            enemies.append("щитоносец")
        if self.wave_number >= 8:
            enemies.append("истребитель")
        return WaveConfig(enemies)

    def start_wave(self) -> None:
        if self.wave_in_progress or self.game_over:
            return
        self.wave_number += 1
        config = self.build_wave()
        self.pending_enemies = [Enemy(ENEMY_TYPES[name], self.path_pixels) for name in config.enemies]
        self.wave_in_progress = True
        self.spawn_timer = 0.0

    def update(self, dt: float) -> None:
        if self.paused or self.game_over:
            return

        self.spawn_timer -= dt
        if self.wave_in_progress and self.pending_enemies and self.spawn_timer <= 0:
            self.enemies.append(self.pending_enemies.pop(0))
            self.spawn_timer = 0.8

        for enemy in self.enemies:
            enemy.update(dt)

        base_pos = self.path_pixels[-1]
        for tower in self.towers:
            new_projectiles = tower.update(dt, self.enemies, base_pos)
            self.projectiles.extend(new_projectiles)

        bounds = (self.level.pixel_width, self.level.pixel_height)
        for projectile in list(self.projectiles):
            projectile.update(dt, bounds)
            if not projectile.alive:
                self.projectiles.remove(projectile)
                continue
            hit_enemy = self.find_collision(projectile)
            if hit_enemy:
                if projectile.splash_radius > 0:
                    self.explosions.append((hit_enemy.position[0], hit_enemy.position[1], 0.0))
                    for enemy in self.enemies:
                        if not self.projectile_can_hit(projectile, enemy):
                            continue
                        dist = ((enemy.position[0] - hit_enemy.position[0]) ** 2 + (enemy.position[1] - hit_enemy.position[1]) ** 2) ** 0.5
                        if dist <= projectile.splash_radius:
                            enemy.apply_damage(projectile.damage)
                else:
                    hit_enemy.apply_damage(projectile.damage)
                for tower in self.towers:
                    if tower.target == hit_enemy:
                        tower.apply_effects(hit_enemy)

        self.apply_healers()

        for enemy in list(self.enemies):
            if not enemy.is_alive():
                self.money += enemy.stats.reward
                self.enemies.remove(enemy)
            elif enemy.reached_end:
                self.base_hp -= 1
                self.enemies.remove(enemy)

        self.explosions = [(x, y, timer + dt) for x, y, timer in self.explosions if timer + dt <= 0.4]

        if self.base_hp <= 0:
            self.game_over = True

        if self.wave_in_progress and not self.pending_enemies and not self.enemies:
            self.wave_in_progress = False

    def place_tower(self, grid_x: int, grid_y: int) -> bool:
        if self.game_over:
            return False
        stats = TOWER_TYPES[self.selected_tower_key]
        if self.money < stats.cost:
            return False
        if self.is_on_path(grid_x, grid_y):
            return False
        if any(tower.position == self.grid_to_pixel(grid_x, grid_y) for tower in self.towers):
            return False
        self.money -= stats.cost
        tower = Tower(stats, self.grid_to_pixel(grid_x, grid_y))
        self.towers.append(tower)
        return True

    def upgrade_tower(self, tower: Tower) -> bool:
        cost = tower.upgrade_cost()
        if self.money < cost:
            return False
        if not tower.next_upgrade():
            return False
        self.money -= cost
        tower.upgrade()
        return True

    def sell_tower(self, tower: Tower) -> None:
        if tower in self.towers:
            self.money += tower.sell_value()
            self.towers.remove(tower)

    def find_collision(self, projectile: Projectile) -> Optional[Enemy]:
        px, py = projectile.center()
        for enemy in self.enemies:
            if not enemy.is_alive():
                continue
            if not self.projectile_can_hit(projectile, enemy):
                continue
            dist = ((enemy.position[0] - px) ** 2 + (enemy.position[1] - py) ** 2) ** 0.5
            if dist <= enemy.size() + projectile.radius:
                return enemy
        return None

    def projectile_can_hit(self, projectile: Projectile, enemy: Enemy) -> bool:
        if enemy.stats.flying and not projectile.can_hit_flying:
            return False
        if not enemy.stats.flying and not projectile.can_hit_ground:
            return False
        return True

    def apply_healers(self) -> None:
        for healer in self.enemies:
            if not healer.is_alive() or not healer.stats.healer:
                continue
            if not healer.can_heal():
                continue
            for ally in self.enemies:
                if ally.stats.flying or not ally.is_alive():
                    continue
                dist = ((ally.position[0] - healer.position[0]) ** 2 + (ally.position[1] - healer.position[1]) ** 2) ** 0.5
                if dist <= healer.stats.heal_radius:
                    ally.apply_heal(healer.stats.heal_amount)
            healer.reset_heal_timer()

    def grid_to_pixel(self, grid_x: int, grid_y: int) -> Tuple[int, int]:
        return (
            grid_x * self.level.cell_size + self.level.cell_size // 2,
            grid_y * self.level.cell_size + self.level.cell_size // 2,
        )

    def is_on_path(self, grid_x: int, grid_y: int) -> bool:
        return (grid_x, grid_y) in self.level.path

    def reset(self) -> None:
        self.__init__(self.level)
