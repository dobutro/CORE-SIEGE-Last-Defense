"""PySide6 widgets for the game scene and HUD."""
from __future__ import annotations

from typing import Optional

import pygame
from PySide6 import QtCore, QtGui, QtWidgets

from .game import GameState
from .tower import TOWER_TYPES, Tower


class GameWidget(QtWidgets.QWidget):
    """Widget that renders the pygame scene."""

    tower_selected = QtCore.Signal(Tower)

    def __init__(self, game_state: GameState, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.game_state = game_state
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
            pygame.draw.circle(self.surface, tower.base_stats.color, tower.position, 15)
            pygame.draw.circle(self.surface, (20, 20, 30), tower.position, 15, 2)

    def draw_enemies(self) -> None:
        for enemy in self.game_state.enemies:
            color = enemy.draw_color()
            size = enemy.size()
            pygame.draw.circle(self.surface, color, (int(enemy.position[0]), int(enemy.position[1])), size)
            hp_ratio = max(enemy.hp / enemy.stats.max_hp, 0)
            bar_width = size * 2
            bar_x = int(enemy.position[0] - size)
            bar_y = int(enemy.position[1] - size - 8)
            pygame.draw.rect(self.surface, (50, 50, 50), (bar_x, bar_y, bar_width, 4))
            pygame.draw.rect(self.surface, (80, 220, 120), (bar_x, bar_y, int(bar_width * hp_ratio), 4))

    def draw_projectiles(self) -> None:
        for projectile in self.game_state.projectiles:
            pygame.draw.circle(self.surface, (255, 200, 120), (int(projectile.position[0]), int(projectile.position[1])), 3)

    def draw_effects(self) -> None:
        for enemy in self.game_state.enemies:
            if enemy.stats.flying:
                continue
            if enemy.slow_timer > 0:
                pygame.draw.circle(self.surface, (120, 200, 255), (int(enemy.position[0]), int(enemy.position[1])), 18, 2)
        for x, y, timer in self.game_state.explosions:
            radius = int(10 + timer * 60)
            pygame.draw.circle(self.surface, (255, 180, 120), (int(x), int(y)), radius, 2)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() != QtCore.Qt.LeftButton:
            return
        grid_x = int(event.position().x() // self.game_state.level.cell_size)
        grid_y = int(event.position().y() // self.game_state.level.cell_size)
        if not self.game_state.place_tower(grid_x, grid_y):
            tower = self.find_tower(grid_x, grid_y)
            if tower:
                self.tower_selected.emit(tower)

    def find_tower(self, grid_x: int, grid_y: int) -> Optional[Tower]:
        pos = self.game_state.grid_to_pixel(grid_x, grid_y)
        for tower in self.game_state.towers:
            if tower.position == pos:
                return tower
        return None


class GameHud(QtWidgets.QWidget):
    """HUD with buttons and info labels."""

    tower_changed = QtCore.Signal(str)
    pause_clicked = QtCore.Signal()
    wave_clicked = QtCore.Signal()
    exit_clicked = QtCore.Signal()
    upgrade_requested = QtCore.Signal(str)

    def __init__(self, game_state: GameState, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.game_state = game_state
        self.selected_tower: Optional[Tower] = None

        self.money_label = QtWidgets.QLabel()
        self.hp_label = QtWidgets.QLabel()
        self.wave_label = QtWidgets.QLabel()

        self.tower_buttons = {}
        tower_box = QtWidgets.QGroupBox("Башни")
        tower_layout = QtWidgets.QVBoxLayout()
        for key, stats in TOWER_TYPES.items():
            button = QtWidgets.QPushButton(f"{stats.name} ({stats.cost})")
            button.clicked.connect(lambda _, k=key: self.tower_changed.emit(k))
            tower_layout.addWidget(button)
            self.tower_buttons[key] = button
        tower_box.setLayout(tower_layout)

        self.pause_button = QtWidgets.QPushButton("Пауза")
        self.pause_button.clicked.connect(self.pause_clicked.emit)
        self.wave_button = QtWidgets.QPushButton("Следующая волна")
        self.wave_button.clicked.connect(self.wave_clicked.emit)
        self.exit_button = QtWidgets.QPushButton("В меню")
        self.exit_button.clicked.connect(self.exit_clicked.emit)

        upgrade_box = QtWidgets.QGroupBox("Улучшения")
        upgrade_layout = QtWidgets.QVBoxLayout()
        self.upgrade_damage = QtWidgets.QPushButton("Урон")
        self.upgrade_rate = QtWidgets.QPushButton("Скорость")
        self.upgrade_range = QtWidgets.QPushButton("Радиус")
        self.upgrade_damage.clicked.connect(lambda: self.upgrade_requested.emit("damage"))
        self.upgrade_rate.clicked.connect(lambda: self.upgrade_requested.emit("rate"))
        self.upgrade_range.clicked.connect(lambda: self.upgrade_requested.emit("range"))
        upgrade_layout.addWidget(self.upgrade_damage)
        upgrade_layout.addWidget(self.upgrade_rate)
        upgrade_layout.addWidget(self.upgrade_range)
        upgrade_box.setLayout(upgrade_layout)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.money_label)
        layout.addWidget(self.hp_label)
        layout.addWidget(self.wave_label)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.wave_button)
        layout.addWidget(self.exit_button)
        layout.addWidget(tower_box)
        layout.addWidget(upgrade_box)
        layout.addStretch()
        self.setFixedWidth(220)
        self.update_labels()

    def update_labels(self) -> None:
        self.money_label.setText(f"Кредиты: {self.game_state.money}")
        self.hp_label.setText(f"Ядро: {self.game_state.base_hp} HP")
        self.wave_label.setText(f"Волна: {self.game_state.wave_number}")

    def set_selected_tower(self, tower: Optional[Tower]) -> None:
        self.selected_tower = tower

    def refresh(self) -> None:
        self.update_labels()
        self.wave_button.setEnabled(not self.game_state.wave_in_progress)
        self.pause_button.setText("Продолжить" if self.game_state.paused else "Пауза")
