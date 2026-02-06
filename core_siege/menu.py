"""Menu screens for navigation."""
from __future__ import annotations

from typing import List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from .level import Level


class MainMenu(QtWidgets.QWidget):
    play_clicked = QtCore.Signal()
    upgrades_clicked = QtCore.Signal()
    exit_clicked = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.title = QtWidgets.QLabel("CORE SIEGE: Last Defense")
        self.title.setStyleSheet("font-size: 26px; font-weight: bold;")
        self.subtitle = QtWidgets.QLabel("Уровни • Изученные юниты • Настройки")
        self.subtitle.setStyleSheet("font-size: 14px; color: #cfcfcf;")

        play_button = QtWidgets.QPushButton("Играть")
        upgrades_button = QtWidgets.QPushButton("Улучшения")
        exit_button = QtWidgets.QPushButton("Выход")

        play_button.clicked.connect(self.play_clicked.emit)
        upgrades_button.clicked.connect(self.upgrades_clicked.emit)
        exit_button.clicked.connect(self.exit_clicked.emit)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.title, alignment=QtCore.Qt.AlignCenter)
        layout.addSpacing(8)
        layout.addWidget(self.subtitle, alignment=QtCore.Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(play_button)
        layout.addWidget(upgrades_button)
        layout.addWidget(exit_button)
        layout.addStretch()

        self.units: List[dict] = []
        self.spawn_menu_units()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(40)

    def spawn_menu_units(self) -> None:
        self.units = []
        width = max(1, self.width())
        height = max(1, self.height())
        colors = [(180, 220, 255), (200, 200, 200), (255, 220, 100)]
        for i in range(10):
            self.units.append(
                {
                    "x": (i * 120) % width,
                    "y": 80 + (i % 4) * 60,
                    "speed": 25 + i * 3,
                    "size": 10 + (i % 3) * 2,
                    "color": colors[i % len(colors)],
                }
            )

    def tick(self) -> None:
        width = max(1, self.width())
        for unit in self.units:
            unit["x"] += unit["speed"] * 0.04
            if unit["x"] > width + 40:
                unit["x"] = -40
        self.update()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.spawn_menu_units()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        for unit in self.units:
            painter.setBrush(QtGui.QColor(*unit["color"]))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(QtCore.QPointF(unit["x"], unit["y"]), unit["size"], unit["size"])


class MapSelectMenu(QtWidgets.QWidget):
    map_selected = QtCore.Signal(Level)
    back_clicked = QtCore.Signal()

    def __init__(self, levels: List[Level], parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        label = QtWidgets.QLabel("Выбор карты")
        label.setStyleSheet("font-size: 20px; font-weight: bold;")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(label, alignment=QtCore.Qt.AlignCenter)
        for level in levels:
            button = QtWidgets.QPushButton(level.name)
            button.clicked.connect(lambda _, lvl=level: self.map_selected.emit(lvl))
            layout.addWidget(button)

        back_button = QtWidgets.QPushButton("Назад")
        back_button.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_button)
        layout.addStretch()


class UpgradesMenu(QtWidgets.QWidget):
    back_clicked = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel("Улучшения (заглушка)")
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        description = QtWidgets.QLabel(
            "Здесь можно добавить мета-улучшения между боями: \n"
            "уровень ядра, бонусы к башням и бонусы к экономике."
        )
        description.setWordWrap(True)
        back_button = QtWidgets.QPushButton("Назад")
        back_button.clicked.connect(self.back_clicked.emit)
        layout.addStretch()
        layout.addWidget(label, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(description)
        layout.addWidget(back_button)
        layout.addStretch()


class GameOverMenu(QtWidgets.QWidget):
    restart_clicked = QtCore.Signal()
    menu_clicked = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("Поражение")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        restart_button = QtWidgets.QPushButton("Перезапуск")
        menu_button = QtWidgets.QPushButton("В меню")
        restart_button.clicked.connect(self.restart_clicked.emit)
        menu_button.clicked.connect(self.menu_clicked.emit)
        layout.addStretch()
        layout.addWidget(title, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(restart_button)
        layout.addWidget(menu_button)
        layout.addStretch()
