# main.py
import sys
import os

# gracefully handle missing GUI dependencies
try:
    from PyQt6.QtWidgets import QApplication  # type: ignore[import]
    from PyQt6.QtGui import QIcon  # type: ignore[import]
except ImportError as exc:
    sys.stderr.write(
        "\nERROR: PyQt6 (and the WebEngine module) are required to run Guardian Karna.\n"
        "Install them via `pip install PyQt6 PyQt6-WebEngine psutil` and then rerun.\n\n"
    )
    sys.exit(1)

from browser_window import BrowserWindow

def main():
    app = QApplication(sys.argv)
    # use icon if available, otherwise ignore silently
    icon_path = os.path.join("icon", "warrior.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        window = BrowserWindow()
        window.setWindowIcon(QIcon(icon_path))
    else:
        # missing icon directory is not fatal; log warning and proceed without icon
        sys.stderr.write(f"Warning: icon not found at {icon_path}\n")
        window = BrowserWindow()

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
