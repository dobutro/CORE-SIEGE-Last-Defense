"""Entry point for the tower defense game."""
from __future__ import annotations

import sys

import pygame
from PySide6 import QtCore, QtWidgets

from core_siege.game import GameState
from core_siege.level import Level, build_levels
from core_siege.menu import GameOverMenu, MainMenu, MapSelectMenu, UpgradesMenu
from core_siege.ui import BottomPanel, GameWidget, TopBar


class GameScreen(QtWidgets.QWidget):
    """Container for the pygame scene and HUD."""

    game_over = QtCore.Signal()
    exit_to_menu = QtCore.Signal()

    def __init__(self, level: Level, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.game_state = GameState(level)
        self.scene = GameWidget(self.game_state)
        self.top_bar = TopBar(self.game_state)
        self.bottom_panel = BottomPanel(self.game_state)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.top_bar)
        layout.addWidget(self.scene, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(self.bottom_panel)

        self.scene.tower_selected.connect(self.bottom_panel.set_selected_tower)
        self.bottom_panel.tower_changed.connect(self.on_tower_changed)
        self.top_bar.pause_clicked.connect(self.game_state.toggle_pause)
        self.top_bar.wave_clicked.connect(self.game_state.start_wave)
        self.top_bar.exit_clicked.connect(self.exit_to_menu.emit)
        self.bottom_panel.upgrade_requested.connect(self.on_upgrade_requested)
        self.bottom_panel.sell_requested.connect(self.on_sell_requested)
        self.bottom_panel.module_selected.connect(self.on_module_selected)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(200)

    def tick(self) -> None:
        self.top_bar.refresh()
        self.bottom_panel.refresh()
        if self.game_state.game_over:
            self.game_over.emit()

    def on_tower_changed(self, key: str) -> None:
        self.game_state.selected_tower_key = key

    def on_upgrade_requested(self) -> None:
        tower = self.bottom_panel.selected_tower
        if tower:
            self.game_state.upgrade_tower(tower)

    def on_sell_requested(self) -> None:
        tower = self.bottom_panel.selected_tower
        if tower:
            self.game_state.sell_tower(tower)
            self.scene.set_selected_tower(None)
            self.bottom_panel.set_selected_tower(None)

    def on_module_selected(self) -> None:
        self.game_state.toggle_fire_module()

    def reset(self, level: Level) -> None:
        self.game_state = GameState(level)
        self.scene.game_state = self.game_state
        self.top_bar.game_state = self.game_state
        self.bottom_panel.game_state = self.game_state
        self.scene.setFixedSize(self.game_state.level.pixel_width, self.game_state.level.pixel_height)
        self.scene.surface = pygame.Surface((self.game_state.level.pixel_width, self.game_state.level.pixel_height))
        self.scene.set_selected_tower(None)
        self.bottom_panel.set_selected_tower(None)
        self.top_bar.refresh()
        self.bottom_panel.refresh()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CORE SIEGE: Last Defense")
        self.setStyleSheet(
            "QWidget { background-color: #2f2f2f; color: #e0e0e0; }"
            "QPushButton { background-color: #3d3d3d; color: #f0f0f0; padding: 6px; }"
            "QGroupBox { color: #e0e0e0; }"
        )
        self.levels = build_levels(cell_size=52)

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_menu = MainMenu()
        self.map_menu = MapSelectMenu(self.levels)
        self.upgrades_menu = UpgradesMenu()
        self.game_over_menu = GameOverMenu()
        self.game_screen: GameScreen | None = None

        self.stack.addWidget(self.main_menu)
        self.stack.addWidget(self.map_menu)
        self.stack.addWidget(self.upgrades_menu)
        self.stack.addWidget(self.game_over_menu)

        self.main_menu.play_clicked.connect(lambda: self.stack.setCurrentWidget(self.map_menu))
        self.main_menu.upgrades_clicked.connect(lambda: self.stack.setCurrentWidget(self.upgrades_menu))
        self.main_menu.exit_clicked.connect(self.close)
        self.map_menu.back_clicked.connect(lambda: self.stack.setCurrentWidget(self.main_menu))
        self.map_menu.map_selected.connect(self.start_game)
        self.upgrades_menu.back_clicked.connect(lambda: self.stack.setCurrentWidget(self.main_menu))
        self.game_over_menu.restart_clicked.connect(self.restart_game)
        self.game_over_menu.menu_clicked.connect(self.return_to_menu)

    def start_game(self, level: Level) -> None:
        if self.game_screen:
            self.stack.removeWidget(self.game_screen)
            self.game_screen.deleteLater()
        self.game_screen = GameScreen(level)
        self.game_screen.game_over.connect(lambda: self.stack.setCurrentWidget(self.game_over_menu))
        self.game_screen.exit_to_menu.connect(self.return_to_menu)
        self.stack.addWidget(self.game_screen)
        self.stack.setCurrentWidget(self.game_screen)

    def restart_game(self) -> None:
        if self.game_screen:
            self.game_screen.reset(self.game_screen.game_state.level)
            self.stack.setCurrentWidget(self.game_screen)

    def return_to_menu(self) -> None:
        self.stack.setCurrentWidget(self.main_menu)


def main() -> None:
    pygame.init()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
