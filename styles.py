# styles.py

DARK_STYLE = """
QMainWindow {
    background-color: #0f172a;
}

QToolBar {
    background-color: #020617;
    spacing: 6px;
    padding: 6px;
    border-bottom: 1px solid #1e293b;
}

QToolButton, QPushButton {
    background-color: #1e293b;
    color: #e2e8f0;
    border-radius: 6px;
    padding: 4px 10px;
    border: 1px solid #334155;
}
QToolButton:hover, QPushButton:hover {
    background-color: #334155;
}
QToolButton:pressed, QPushButton:pressed {
    background-color: #0f172a;
}

QLineEdit {
    background-color: #020617;
    color: #e2e8f0;
    border-radius: 8px;
    padding: 4px 8px;
    border: 1px solid #1e293b;
}

QStatusBar {
    background-color: #020617;
    color: #94a3b8;
}

QComboBox {
    background-color: #020617;
    color: #e2e8f0;
    border-radius: 6px;
    padding: 2px 8px;
    border: 1px solid #1e293b;
}

QDockWidget {
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}

QLabel {
    color: #e5e7eb;
}

QMenuBar {
    background-color: #020617;
    color: #e5e7eb;
}
QMenuBar::item:selected {
    background-color: #1e293b;
}

QMenu {
    background-color: #020617;
    color: #e5e7eb;
}
QMenu::item:selected {
    background-color: #1e293b;
}
"""

LIGHT_STYLE = """
QMainWindow {
    background-color: #f3f4f6;
}

QToolBar {
    background-color: #ffffff;
    spacing: 6px;
    padding: 6px;
    border-bottom: 1px solid #e5e7eb;
}

QToolButton, QPushButton {
    background-color: #e5e7eb;
    color: #111827;
    border-radius: 6px;
    padding: 4px 10px;
    border: 1px solid #d1d5db;
}
QToolButton:hover, QPushButton:hover {
    background-color: #d1d5db;
}
QToolButton:pressed, QPushButton:pressed {
    background-color: #9ca3af;
}

QLineEdit {
    background-color: #ffffff;
    color: #111827;
    border-radius: 8px;
    padding: 4px 8px;
    border: 1px solid #d1d5db;
}

QStatusBar {
    background-color: #ffffff;
    color: #4b5563;
}

QComboBox {
    background-color: #ffffff;
    color: #111827;
    border-radius: 6px;
    padding: 2px 8px;
    border: 1px solid #d1d5db;
}

QDockWidget {
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}

QLabel {
    color: #111827;
}

QMenuBar {
    background-color: #ffffff;
    color: #111827;
}
QMenuBar::item:selected {
    background-color: #e5e7eb;
}

QMenu {
    background-color: #ffffff;
    color: #111827;
}
QMenu::item:selected {
    background-color: #e5e7eb;
}
"""
