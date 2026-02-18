# main.py
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from browser_window import BrowserWindow

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon/warrior.png"))

    window = BrowserWindow()
    window.setWindowIcon(QIcon("icon/warrior.png"))
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
