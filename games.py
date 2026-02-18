# games.py
from dataclasses import dataclass, field
from typing import List
import time

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QHBoxLayout
)


@dataclass
class GameRecord:
    game_name: str
    score: int
    timestamp: float


@dataclass
class GameStatsManager:
    records: List[GameRecord] = field(default_factory=list)

    def add_record(self, game_name: str, score: int):
        self.records.append(GameRecord(game_name, score, time.time()))

    def get_records(self) -> List[GameRecord]:
        return self.records

    def clear(self):
        self.records.clear()


class ClickGameDialog(QDialog):
    """
    Very simple mini-game:
    - User clicks as many times as possible.
    """
    def __init__(self, stats_manager: GameStatsManager, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        self.setWindowTitle("Mini Game - Click Frenzy")
        self.click_count = 0

        layout = QVBoxLayout(self)

        self.info_label = QLabel("Click the button as many times as you can.\nPress Finish when done.")
        layout.addWidget(self.info_label)

        self.click_button = QPushButton("Click me!")
        self.click_button.clicked.connect(self._on_click)
        layout.addWidget(self.click_button)

        self.count_label = QLabel("Clicks: 0")
        layout.addWidget(self.count_label)

        btn_row = QHBoxLayout()
        self.finish_button = QPushButton("Finish")
        self.finish_button.clicked.connect(self._finish)
        btn_row.addWidget(self.finish_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        btn_row.addWidget(self.close_button)

        layout.addLayout(btn_row)

    def _on_click(self):
        self.click_count += 1
        self.count_label.setText(f"Clicks: {self.click_count}")

    def _finish(self):
        self.stats_manager.add_record("Click Frenzy", self.click_count)
        self.info_label.setText(f"Game over! Final Score: {self.click_count}")
        self.click_button.setEnabled(False)
        self.finish_button.setEnabled(False)


class GameStatsDialog(QDialog):
    """
    Shows list of past game records.
    """
    def __init__(self, stats_manager: GameStatsManager, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        self.setWindowTitle("Game Statistics")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>Game History</b>"))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self._populate()

        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(clear_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _populate(self):
        self.list_widget.clear()
        for rec in self.stats_manager.get_records():
            t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rec.timestamp))
            text = f"[{t}] {rec.game_name} - Score: {rec.score}"
            self.list_widget.addItem(QListWidgetItem(text))

    def _clear(self):
        self.stats_manager.clear()
        self._populate()
