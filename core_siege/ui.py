"""PySide6 widgets for the game scene and HUD."""
from __future__ import annotations

from typing import Optional

import pygame
from PySide6 import QtCore, QtGui, QtWidgets
import math

from .game import GameState
from .tower import TOWER_TYPES, Tower


class GameWidget(QtWidgets.QWidget):
    """Widget that renders the pygame scene."""

    tower_selected = QtCore.Signal(object)

    def __init__(self, game_state: GameState, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.game_state = game_state
        self.selected_tower: Optional[Tower] = None
        self.setFixedSize(game_state.level.pixel_width, game_state.level.pixel_height)
        self.surface = pygame.Surface((game_state.level.pixel_width, game_state.level.pixel_height))
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        self.last_time = QtCore.QElapsedTimer()
        self.last_time.start()

    def tick(self) -> None:
        dt = self.last_time.restart() / 1000.0
        self.game_state.update(dt)
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        self.draw_scene()
        image = pygame.image.tostring(self.surface, "RGB")
        qimage = QtGui.QImage(
            image,
            self.surface.get_width(),
            self.surface.get_height(),
            QtGui.QImage.Format_RGB888,
        )
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, qimage)

    def draw_scene(self) -> None:
        self.surface.fill((40, 40, 40))
        self.draw_grid()
        self.draw_path()
        self.draw_base()
        self.draw_towers()
        self.draw_enemies()
        self.draw_projectiles()
        self.draw_effects()

    def draw_grid(self) -> None:
        cell = self.game_state.level.cell_size
        color = (55, 55, 55)
        for x in range(self.game_state.level.grid_width + 1):
            pygame.draw.line(self.surface, color, (x * cell, 0), (x * cell, self.game_state.level.pixel_height))
        for y in range(self.game_state.level.grid_height + 1):
            pygame.draw.line(self.surface, color, (0, y * cell), (self.game_state.level.pixel_width, y * cell))

    def draw_path(self) -> None:
        if len(self.game_state.level.path) < 2:
            return
        points = [
            (
                x * self.game_state.level.cell_size + self.game_state.level.cell_size // 2,
                y * self.game_state.level.cell_size + self.game_state.level.cell_size // 2,
            )
            for x, y in self.game_state.level.path
        ]
        pygame.draw.lines(self.surface, (75, 75, 85), False, points, 30)

    def draw_base(self) -> None:
        end = self.game_state.level.path[-1]
        pos = (
            end[0] * self.game_state.level.cell_size + self.game_state.level.cell_size // 2,
            end[1] * self.game_state.level.cell_size + self.game_state.level.cell_size // 2,
        )
        pygame.draw.circle(self.surface, (90, 255, 200), pos, 20)
        pygame.draw.circle(self.surface, (40, 140, 120), pos, 14)

    def draw_towers(self) -> None:
        for tower in self.game_state.towers:
            self.draw_tower_shape(tower)
            if tower == self.selected_tower:
                pygame.draw.circle(self.surface, (255, 255, 255), tower.position, 20, 2)
        if self.game_state.fire_module_selected:
            for tower in self.game_state.towers:
                if self.game_state.can_apply_fire_module(tower):
                    pygame.draw.circle(self.surface, (100, 255, 120), tower.position, 20, 2)

    def draw_enemies(self) -> None:
        for enemy in self.game_state.enemies:
            color = enemy.draw_color()
            size = enemy.size()
            pygame.draw.circle(self.surface, color, (int(enemy.position[0]), int(enemy.position[1])), size)
            if enemy.shield_hp > 0:
                pygame.draw.circle(
                    self.surface,
                    (120, 180, 255),
                    (int(enemy.position[0]), int(enemy.position[1])),
                    size + 4,
                    2,
                )
            if enemy.took_damage:
                hp_ratio = max(enemy.hp / enemy.stats.max_hp, 0)
                bar_width = size * 2
                bar_x = int(enemy.position[0] - size)
                bar_y = int(enemy.position[1] - size - 8)
                pygame.draw.rect(self.surface, (50, 50, 50), (bar_x, bar_y, bar_width, 4))
                pygame.draw.rect(self.surface, (80, 220, 120), (bar_x, bar_y, int(bar_width * hp_ratio), 4))
                if enemy.stats.shield_hp > 0:
                    shield_ratio = max(enemy.shield_hp / enemy.stats.shield_hp, 0)
                    pygame.draw.rect(
                        self.surface,
                        (80, 140, 220),
                        (bar_x, bar_y - 5, int(bar_width * shield_ratio), 3),
                    )

    def draw_projectiles(self) -> None:
        for projectile in self.game_state.projectiles:
            pygame.draw.circle(
                self.surface,
                (255, 200, 120),
                (int(projectile.position[0]), int(projectile.position[1])),
                projectile.radius,
            )

    def draw_effects(self) -> None:
        if self.selected_tower:
            pygame.draw.circle(
                self.surface,
                (180, 180, 180),
                (int(self.selected_tower.position[0]), int(self.selected_tower.position[1])),
                int(self.selected_tower.total_range()),
                1,
            )
        for tower in self.game_state.towers:
            if tower.base_stats.laser and tower.target and tower.target.is_alive():
                pygame.draw.line(
                    self.surface,
                    (255, 120, 200),
                    tower.position,
                    (int(tower.target.position[0]), int(tower.target.position[1])),
                    3,
                )
        for enemy in self.game_state.enemies:
            if enemy.stats.flying:
                continue
            if enemy.slow_timer > 0:
                pygame.draw.circle(self.surface, (120, 200, 255), (int(enemy.position[0]), int(enemy.position[1])), 18, 2)
        for x, y, timer in self.game_state.explosions:
            radius = int(10 + timer * 60)
            pygame.draw.circle(self.surface, (255, 180, 120), (int(x), int(y)), radius, 2)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        grid_x = int(event.position().x() // self.game_state.level.cell_size)
        grid_y = int(event.position().y() // self.game_state.level.cell_size)
        if event.button() == QtCore.Qt.LeftButton and self.game_state.fire_module_selected:
            tower = self.find_tower(grid_x, grid_y)
            if tower and self.game_state.apply_fire_module(tower):
                self.game_state.fire_module_selected = False
            return
        if event.button() == QtCore.Qt.LeftButton:
            if self.game_state.place_tower(grid_x, grid_y):
                self.set_selected_tower(None)
                self.tower_selected.emit(None)
        elif event.button() == QtCore.Qt.RightButton:
            tower = self.find_tower(grid_x, grid_y)
            self.set_selected_tower(tower)
            self.tower_selected.emit(tower)

    def find_tower(self, grid_x: int, grid_y: int) -> Optional[Tower]:
        pos = self.game_state.grid_to_pixel(grid_x, grid_y)
        for tower in self.game_state.towers:
            if tower.position == pos:
                return tower
        return None

    def set_selected_tower(self, tower: Optional[Tower]) -> None:
        self.selected_tower = tower

    def draw_tower_shape(self, tower: Tower) -> None:
        x, y = tower.position
        radius = 15
        color = tower.base_stats.color
        outline = (20, 20, 30)
        self.draw_class_one_shape(tower, (int(x), int(y)), radius, color, outline)
        if tower.base_stats.name == "Двойная":
            self.draw_tower_barrel(tower, (int(x), int(y)), radius, offset=4)
            self.draw_tower_barrel(tower, (int(x), int(y)), radius, offset=-4)
        else:
            self.draw_tower_barrel(tower, (int(x), int(y)), radius)
        if tower.base_stats.name == "Испепеление":
            square_color = (140, 20, 20) if tower.is_warming else (70, 70, 70)
            inner = pygame.Rect(0, 0, radius, radius)
            inner.center = (int(x), int(y))
            pygame.draw.rect(self.surface, square_color, inner)

    def draw_class_one_shape(
        self,
        tower: Tower,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int],
        outline: tuple[int, int, int],
    ) -> None:
        if tower.base_stats.ground_only:
            pygame.draw.circle(self.surface, color, center, radius)
            pygame.draw.circle(self.surface, outline, center, radius, 2)
        elif tower.base_stats.flying_only:
            rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            rect.center = center
            pygame.draw.rect(self.surface, color, rect)
            pygame.draw.rect(self.surface, outline, rect, 2)
        else:
            points = [
                (center[0], center[1] - radius),
                (center[0] + radius, center[1]),
                (center[0], center[1] + radius),
                (center[0] - radius, center[1]),
            ]
            pygame.draw.polygon(self.surface, color, points)
            pygame.draw.polygon(self.surface, outline, points, 2)

    def draw_tower_barrel(self, tower: Tower, center: tuple[int, int], radius: int, offset: int = 0) -> None:
        length = radius + 6
        perp_x = -math.sin(tower.angle) * offset
        perp_y = math.cos(tower.angle) * offset
        start_x = center[0] + int(perp_x)
        start_y = center[1] + int(perp_y)
        end_x = start_x + int(math.cos(tower.angle) * length)
        end_y = start_y + int(math.sin(tower.angle) * length)
        pygame.draw.line(self.surface, (230, 230, 230), (start_x, start_y), (end_x, end_y), 3)


class TopBar(QtWidgets.QWidget):
    """Top bar with status and main controls."""

    pause_clicked = QtCore.Signal()
    wave_clicked = QtCore.Signal()
    exit_clicked = QtCore.Signal()

    def __init__(self, game_state: GameState, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.game_state = game_state

        self.money_label = QtWidgets.QLabel()
        self.wave_label = QtWidgets.QLabel()
        self.level_label = QtWidgets.QLabel(game_state.level.name)
        self.level_label.setStyleSheet("font-weight: bold;")

        self.pause_button = QtWidgets.QPushButton("Пауза")
        self.pause_button.clicked.connect(self.pause_clicked.emit)
        self.wave_button = QtWidgets.QPushButton("Следующая волна")
        self.wave_button.clicked.connect(self.wave_clicked.emit)
        self.exit_button = QtWidgets.QPushButton("В меню")
        self.exit_button.clicked.connect(self.exit_clicked.emit)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.money_label)
        layout.addWidget(self.wave_label)
        layout.addStretch()
        layout.addWidget(self.level_label)
        layout.addStretch()
        layout.addWidget(self.pause_button)
        layout.addWidget(self.wave_button)
        layout.addWidget(self.exit_button)
        self.setFixedHeight(50)
        self.refresh()

    def refresh(self) -> None:
        self.money_label.setText(f"Кредиты: {self.game_state.money}")
        self.wave_label.setText(f"Волна: {self.game_state.wave_number}")
        self.level_label.setText(self.game_state.level.name)
        self.wave_button.setEnabled(not self.game_state.wave_in_progress)
        self.pause_button.setText("Продолжить" if self.game_state.paused else "Пауза")


class BottomPanel(QtWidgets.QWidget):
    """Bottom panel with tabs."""

    tower_changed = QtCore.Signal(str)
    upgrade_requested = QtCore.Signal()
    sell_requested = QtCore.Signal()
    module_selected = QtCore.Signal()
    module_applied = QtCore.Signal()

    def __init__(self, game_state: GameState, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.game_state = game_state
        self.selected_tower: Optional[Tower] = None

        self.tabs = QtWidgets.QTabWidget()
        self.towers_tab = QtWidgets.QWidget()
        self.modules_tab = QtWidgets.QWidget()
        self.selected_tab = QtWidgets.QWidget()

        self.tabs.addTab(self.towers_tab, "Башни")
        self.tabs.addTab(self.modules_tab, "Модули")
        self.tabs.addTab(self.selected_tab, "Башня")

        self.tabs.setTabEnabled(2, False)

        towers_layout = QtWidgets.QHBoxLayout(self.towers_tab)
        for key, stats in TOWER_TYPES.items():
            button = QtWidgets.QPushButton(f"{stats.name} ({stats.cost})")
            button.clicked.connect(lambda _, k=key: self.tower_changed.emit(k))
            if stats.weapon_class == 2:
                button.setStyleSheet("border: 2px solid #f2d34a;")
            towers_layout.addWidget(button)

        modules_layout = QtWidgets.QVBoxLayout(self.modules_tab)
        self.fire_module_button = QtWidgets.QPushButton(f"Огненный модуль ({self.game_state.fire_module_cost})")
        self.fire_module_button.clicked.connect(self.module_selected.emit)
        modules_layout.addWidget(self.fire_module_button)
        modules_layout.addStretch()

        selected_layout = QtWidgets.QVBoxLayout(self.selected_tab)
        self.selected_label = QtWidgets.QLabel("Башня: не выбрана")
        self.stats_label = QtWidgets.QLabel("Характеристики: -")
        self.upgrade_info = QtWidgets.QLabel("Нет данных")
        self.upgrade_button = QtWidgets.QPushButton("Улучшить")
        self.upgrade_button.clicked.connect(self.upgrade_requested.emit)
        self.sell_button = QtWidgets.QPushButton("Разобрать")
        self.sell_button.clicked.connect(self.sell_requested.emit)
        selected_layout.addWidget(self.selected_label)
        selected_layout.addWidget(self.stats_label)
        selected_layout.addWidget(self.upgrade_info)
        selected_layout.addWidget(self.upgrade_button)
        selected_layout.addWidget(self.sell_button)
        selected_layout.addStretch()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tabs)
        self.setFixedHeight(220)
        self.refresh()

    def set_selected_tower(self, tower: Optional[Tower]) -> None:
        self.selected_tower = tower
        if tower:
            self.tabs.setTabEnabled(2, True)
            self.tabs.setCurrentWidget(self.selected_tab)
        else:
            self.tabs.setTabEnabled(2, False)
            self.tabs.setCurrentWidget(self.towers_tab)
        self.refresh()

    def refresh(self) -> None:
        has_tower = self.selected_tower is not None
        if has_tower:
            tower = self.selected_tower
            self.selected_label.setText(f"Башня: {tower.base_stats.name} (ур. {tower.level})")
            self.stats_label.setText(
                f"Урон: {tower.total_damage():.1f} | Скорость: {tower.total_rate():.1f} | Радиус: {tower.total_range():.0f}"
            )
            self.sell_button.setText(f"Разобрать (+{tower.sell_value()})")
            next_upgrade = tower.next_upgrade()
            if next_upgrade:
                upgrade_label = {"damage": "Урон", "rate": "Скорость", "range": "Радиус"}.get(next_upgrade, next_upgrade)
                self.upgrade_info.setText(f"Следующее улучшение: {upgrade_label} (+{tower.upgrade_cost()})")
                self.upgrade_button.setEnabled(True)
            else:
                self.upgrade_info.setText("Все улучшения получены")
                self.upgrade_button.setEnabled(False)
        else:
            self.selected_label.setText("Башня: не выбрана")
            self.stats_label.setText("Характеристики: -")
            self.upgrade_info.setText("Выберите башню")
            self.upgrade_button.setEnabled(False)
            self.sell_button.setText("Разобрать")
        self.sell_button.setEnabled(has_tower)
