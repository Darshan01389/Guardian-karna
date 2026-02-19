# browser_window.py
from collections import deque
from typing import Deque
import os
import time
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, QUrl, QEvent, QTimer  # type: ignore[import]
from PyQt6.QtGui import QAction, QPainter, QPen, QFont  # type: ignore[import]
from PyQt6.QtWidgets import (  # type: ignore[import]
    QMainWindow, QToolBar, QLineEdit, QToolButton,
    QDockWidget, QWidget, QVBoxLayout, QLabel, QComboBox,
    QStatusBar, QMessageBox, QMenu, QMenuBar,
    QPushButton, QHBoxLayout, QListWidget, QListWidgetItem,
    QDialog, QStackedWidget, QFileDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore[import]
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest  # type: ignore[import]

from mode_manager import ModeManager, SecurityMode, SubscriptionTier
from security_engine import SecurityEngine
from performance_monitor import PerformanceMonitor
from games import GameStatsManager, ClickGameDialog, GameStatsDialog
from styles import DARK_STYLE, LIGHT_STYLE
from auth import AuthManager
from log_manager import LogManager

# ------------------- Custom Chart Widgets -------------------

class DonutChartWidget(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.value = 0.0
        self.label = label
        self.theme = "dark"
        self.setMinimumSize(100, 100)  # slimmer column

    def set_value(self, val: float):
        self.value = max(0.0, min(100.0, val))
        self.update()

    def set_theme(self, theme: str):
        self.theme = theme
        self.update()

    def paintEvent(self, event):
        size = min(self.width(), self.height())
        margin = 10
        radius = (size - 2 * margin) / 2
        center_x = self.width() / 2
        center_y = self.height() / 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.theme == "dark":
            bg_circle = Qt.GlobalColor.darkGray
            arc_color = Qt.GlobalColor.cyan
            text_color = Qt.GlobalColor.white
        else:
            bg_circle = Qt.GlobalColor.lightGray
            arc_color = Qt.GlobalColor.darkBlue
            text_color = Qt.GlobalColor.black

        pen = QPen()
        pen.setWidth(10)
        pen.setColor(bg_circle)
        painter.setPen(pen)
        painter.drawEllipse(
            int(center_x - radius),
            int(center_y - radius),
            int(2 * radius),
            int(2 * radius),
        )

        pen.setColor(arc_color)
        painter.setPen(pen)
        span_angle = int(360 * self.value / 100.0)
        painter.drawArc(
            int(center_x - radius),
            int(center_y - radius),
            int(2 * radius),
            int(2 * radius),
            90 * 16,
            -span_angle * 16,
        )

        painter.setPen(text_color)
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        text = f"{self.label}\n{self.value:.1f}%"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)


class LineChartWidget(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.label = label
        self.values: Deque[float] = deque(maxlen=25)
        self.theme = "dark"
        self.setMinimumHeight(80)

    def add_value(self, v: float):
        self.values.append(v)
        self.update()

    def set_theme(self, theme: str):
        self.theme = theme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        margin = 8
        left = rect.left() + margin
        right = rect.right() - margin
        top = rect.top() + margin
        bottom = rect.bottom() - margin - 16

        if self.theme == "dark":
            bg = Qt.GlobalColor.black
            frame = Qt.GlobalColor.darkGray
            line = Qt.GlobalColor.cyan
            text = Qt.GlobalColor.white
        else:
            bg = Qt.GlobalColor.white
            frame = Qt.GlobalColor.lightGray
            line = Qt.GlobalColor.darkBlue
            text = Qt.GlobalColor.black

        painter.fillRect(rect, bg)

        pen = QPen(frame)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(left, top, right - left, bottom - top)

        if len(self.values) > 1:
            max_val = max(self.values) or 1
            span_x = max(1, len(self.values) - 1)
            points = []
            for i, v in enumerate(self.values):
                x = left + (right - left) * (i / span_x)
                y = bottom - (bottom - top) * (v / max_val)
                points.append((x, y))

            pen = QPen(line)
            pen.setWidth(2)
            painter.setPen(pen)

            prev = points[0]
            for pt in points[1:]:
                painter.drawLine(int(prev[0]), int(prev[1]), int(pt[0]), int(pt[1]))
                prev = pt

        painter.setPen(text)
        font = QFont()
        font.setPointSize(7)
        painter.setFont(font)
        painter.drawText(
            rect.adjusted(margin, bottom + 2, -margin, 0),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            f"{self.label} (KB/s)"
        )

# ------------------- SECURITY LOG VIEWER (popup) -------------------

class LogViewerDialog(QDialog):
    def __init__(self, log_manager: LogManager, parent=None):
        super().__init__(parent)
        self.log_manager = log_manager
        self.setWindowTitle("Security Scan Logs")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Security Scan History</b>"))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self._populate()

        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(clear_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _populate(self):
        self.list_widget.clear()
        for entry in self.log_manager.get_entries():
            t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry.timestamp))
            text = (
                f"[{t}] {entry.url}\n"
                f"  Pre: {entry.pre_risk.upper()} | Final: {entry.final_risk.upper()} | "
                f"Mode: {entry.mode.name} | Sub: {entry.subscription.name} | Action: {entry.action}"
            )
            self.list_widget.addItem(QListWidgetItem(text))

    def _clear(self):
        self.log_manager.clear()
        self._populate()

# ------------------- MAIN BROWSER WINDOW -------------------

class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Guardian Karna Browser")
        self.resize(1280, 800)

        self.mode_manager = ModeManager()
        self.security_engine = SecurityEngine(self)
        self.perf_monitor = PerformanceMonitor(self)
        self.game_stats = GameStatsManager()
        self.auth_manager = AuthManager()
        self.log_manager = LogManager()

        self._current_url_being_scanned = None
        self._current_risk = None
        self._deep_scan_running = False
        self.current_theme = "dark"
        self._is_home = False

        # recent tabs
        self.recent_urls = []

        self._setup_ui()
        self._connect_signals()
        self.apply_theme()
        self._refresh_account_ui()

        self.load_home()

    # ------------------- THEME -------------------

    def apply_theme(self):
        if self.current_theme == "dark":
            self.setStyleSheet(DARK_STYLE)

            # community chat styling
            self.community_messages.setStyleSheet("""
                QListWidget {
                    background: #020617;
                    color: #e5e7eb;
                    border: none;
                }
                QListWidget::item {
                    padding: 6px 10px;
                    margin: 4px 6px;
                    border-radius: 10px;
                }
            """)

            # protection panel styling
            self.protection_list.setStyleSheet("""
                QListWidget {
                    background: #020617;
                    color: #e5e7eb;
                    border: none;
                }
            """)
            self.protection_anim_label.setStyleSheet("color: #e5e7eb;")

        else:
            self.setStyleSheet(LIGHT_STYLE)

            # light mode community chat
            self.community_messages.setStyleSheet("""
                QListWidget {
                    background: #f4f4f5;
                    color: #020617;
                    border: none;
                }
                QListWidget::item {
                    padding: 6px 10px;
                    margin: 4px 6px;
                    border-radius: 10px;
                }
            """)

            # light mode protection
            self.protection_list.setStyleSheet("""
                QListWidget {
                    background: #f4f4f5;
                    color: #020617;
                    border: none;
                }
            """)
            self.protection_anim_label.setStyleSheet("color: #020617;")

        # performance widgets
        self.cpu_donut.set_theme(self.current_theme)
        self.mem_donut.set_theme(self.current_theme)
        self.net_line.set_theme(self.current_theme)

        # rebuild home if visible
        if self._is_home:
            self.web_view.setHtml(self._build_home_html())

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.theme_button.setText("🌙" if self.current_theme == "dark" else "☀")
        self.apply_theme()

    # ------------------- HOME PAGE -------------------

    def _build_home_html(self):
        if self.current_theme == "dark":
            bg = "#020617"
            card = "#0f172a"
            text = "#e5e7eb"
            accent = "#38bdf8"
            subtle = "#64748b"
            preview_bg1 = "#1d4ed8"
            preview_bg2 = "#22d3ee"
        else:
            bg = "#f4f4f5"
            card = "#ffffff"
            text = "#020617"
            accent = "#2563eb"
            subtle = "#4b5563"
            preview_bg1 = "#2dd4bf"
            preview_bg2 = "#6366f1"

        # preview tiles from recent URLs
        preview_strip = ""
        if self.recent_urls:
            tiles = ""
            for u in self.recent_urls[:6]:
                parsed = urlparse(u)
                host = parsed.netloc or u
                initial = host[0].upper() if host else "?"
                short = host if len(host) <= 20 else host[:17] + "..."
                tiles += f"""
                <a href="{u}" style="text-decoration:none;">
                    <div class="preview-tile">
                        <div class="preview-icon">{initial}</div>
                        <div class="preview-host">{short}</div>
                    </div>
                </a>
                """
            preview_strip = f"""
            <div class="preview-strip-title">Last opened sites</div>
            <div class="preview-strip">{tiles}</div>
            """

        # recent tabs
        recent_section = ""
        if self.recent_urls:
            items = ""
            for u in self.recent_urls[:5]:
                short = u if len(u) <= 60 else u[:57] + "..."
                items += f"<li><a href='{u}'>{short}</a></li>"
            recent_section = f"""
            <div class="card">
                <h3>Recent tabs</h3>
                <ul>{items}</ul>
            </div>
            """

        # protection events
        logs_section = ""
        entries = self.log_manager.get_entries()
        if entries:
            items = ""
            for entry in entries[-5:][::-1]:
                t = time.strftime("%H:%M:%S", time.localtime(entry.timestamp))
                short = entry.url if len(entry.url) <= 50 else entry.url[:47] + "..."
                items += (
                    f"<li><span>{t}</span> – "
                    f"<b>{entry.action.upper()}</b> "
                    f"({entry.final_risk.upper()}) – {short}</li>"
                )
            logs_section = f"""
            <div class="card">
                <h3>Recent protection events</h3>
                <ul>{items}</ul>
            </div>
            """

        extra_grid = ""
        if recent_section or logs_section:
            extra_grid = f"""
            <div class="grid extra">
                {recent_section}
                {logs_section}
            </div>
            """

        html = f"""
        <html>
        <head>
        <meta charset="utf-8" />
        <title>Guardian Karna Home</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: {bg};
                color: {text};
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}
            .wrapper {{
                max-width: 960px;
                margin: 40px auto;
                padding: 16px;
            }}
            .hero {{
                background: {card};
                border-radius: 18px;
                padding: 32px;
                box-shadow: 0 20px 40px rgba(15,23,42,0.3);
            }}
            .title {{
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            .subtitle {{
                font-size: 14px;
                color: {subtle};
                margin-bottom: 24px;
            }}
            .pill {{
                display:inline-block;
                padding:4px 10px;
                border-radius:999px;
                background:rgba(56,189,248,0.12);
                color:{accent};
                font-size:11px;
                text-transform:uppercase;
                letter-spacing:0.08em;
                margin-bottom:10px;
            }}
            .quick-links a {{
                display:inline-block;
                padding:8px 14px;
                border-radius:999px;
                border:1px solid rgba(148,163,184,0.4);
                margin-right:8px;
                margin-top:8px;
                text-decoration:none;
                font-size:12px;
                color:{accent};
            }}
            .preview-strip-title {{
                margin-top: 18px;
                font-size: 13px;
                font-weight: 600;
                color: {subtle};
            }}
            .preview-strip {{
                display:flex;
                gap:8px;
                margin-top:8px;
                flex-wrap:wrap;
            }}
            .preview-tile {{
                width: 120px;
                border-radius: 14px;
                background: {card};
                border: 1px solid rgba(148,163,184,0.35);
                padding: 6px;
                display:flex;
                align-items:center;
                gap:8px;
            }}
            .preview-icon {{
                width: 32px;
                height: 32px;
                border-radius: 999px;
                background: linear-gradient(135deg, {preview_bg1}, {preview_bg2});
                display:flex;
                align-items:center;
                justify-content:center;
                color:white;
                font-weight:700;
            }}
            .preview-host {{
                font-size: 11px;
                color: {text};
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 16px;
                margin-top: 24px;
            }}
            .card {{
                background: {card};
                border-radius: 14px;
                padding: 18px;
                border: 1px solid rgba(148,163,184,0.35);
            }}
            .card h3 {{
                margin: 0 0 6px;
                font-size: 15px;
            }}
            .card ul {{
                padding-left: 18px;
                margin: 4px 0 0 0;
                font-size: 12px;
                color: {subtle};
            }}
            .extra {{
                margin-top: 32px;
            }}
        </style>
        </head>
        <body>
        <div class="wrapper">
            <div class="hero">
                <div class="pill">Guardian Karna Browser</div>
                <div class="title">Safe. Smart. Distraction-free browsing.</div>
                <div class="subtitle">
                    Guardian Karna stands guard like a warrior at the edge of a cliff – scanning every site
                    before it reaches you. Start from the address bar above, or jump into a trusted site.
                </div>
                <div class="quick-links">
                    <a href="https://www.google.com">Google</a>
                    <a href="https://chatgpt.com">ChatGPT</a>
                    <a href="https://www.wikipedia.org">Wikipedia</a>
                </div>
                {preview_strip}
            </div>

            {extra_grid}
        </div>
        </body>
        </html>
        """
        return html

    def load_home(self):
        self._is_home = True
        self._current_url_being_scanned = None
        self.scan_status_label.setText("Home")
        self.safe_mode_label.setText("HOME")
        self.url_bar.clear()
        self.web_view.setHtml(self._build_home_html())

    # ------------------- UI SETUP -------------------

    def _setup_ui(self):
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)

        # connect downloads
        profile = self.web_view.page().profile()
        profile.downloadRequested.connect(self._on_download_requested)

        # top toolbar
        toolbar = QToolBar("Navigation")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        back_btn = QToolButton()
        back_btn.setText("←")
        back_btn.clicked.connect(self.web_view.back)
        toolbar.addWidget(back_btn)

        fwd_btn = QToolButton()
        fwd_btn.setText("→")
        fwd_btn.clicked.connect(self.web_view.forward)
        toolbar.addWidget(fwd_btn)

        reload_btn = QToolButton()
        reload_btn.setText("⟳")
        reload_btn.clicked.connect(self.web_view.reload)
        toolbar.addWidget(reload_btn)

        home_btn = QToolButton()
        home_btn.setText("🏠")
        home_btn.clicked.connect(self.load_home)
        toolbar.addWidget(home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.setMinimumWidth(400)
        self.url_bar.setPlaceholderText("Enter URL or search…")
        self.url_bar.setClearButtonEnabled(True)
        self.url_bar.returnPressed.connect(self.load_url)
        toolbar.addWidget(self.url_bar)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Balanced", "Moderate", "Advanced Defence"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        toolbar.addWidget(self.mode_combo)

        self.theme_button = QToolButton()
        self.theme_button.setText("🌙")
        self.theme_button.clicked.connect(self.toggle_theme)
        toolbar.addWidget(self.theme_button)

        self.settings_button = QToolButton()
        self.settings_button.setText("⚙")
        self.settings_button.clicked.connect(self._show_settings_panel)
        toolbar.addWidget(self.settings_button)

        self.sub_button = QToolButton()
        self.sub_button.clicked.connect(self._show_subscription_panel)
        toolbar.addWidget(self.sub_button)

        self.scan_status_label = QLabel("Ready")
        toolbar.addWidget(self.scan_status_label)

        # recent toolbar
        self.recent_toolbar = QToolBar("Recent")
        self.recent_toolbar.setMovable(False)
        self.addToolBar(self.recent_toolbar)
        self._refresh_recent_toolbar()

        # status bar
        status = QStatusBar()
        self.setStatusBar(status)

        self.safe_mode_label = QLabel("")
        self.statusBar().addPermanentWidget(self.safe_mode_label)

        self.account_label = QLabel("")
        self.statusBar().addPermanentWidget(self.account_label)

        # -------- menu bar --------
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)

        view_menu = QMenu("View")
        menu_bar.addMenu(view_menu)

        self.perf_toggle = QAction("Toggle Performance Panel", self, checkable=True)
        self.perf_toggle.setChecked(True)
        self.perf_toggle.triggered.connect(self._toggle_perf_panel)
        view_menu.addAction(self.perf_toggle)

        games_menu = QMenu("Games")
        menu_bar.addMenu(games_menu)

        game_action = QAction("Play Click Frenzy")
        game_action.triggered.connect(self._open_game)
        games_menu.addAction(game_action)

        stats_action = QAction("View Game Stats")
        stats_action.triggered.connect(self._open_game_stats)
        games_menu.addAction(stats_action)

        profile_menu = QMenu("Profile")
        menu_bar.addMenu(profile_menu)

        login_action = QAction("Login / Switch Account")
        login_action.triggered.connect(self._show_login_panel)
        profile_menu.addAction(login_action)

        subs_action = QAction("Subscription Plans")
        subs_action.triggered.connect(self._show_subscription_panel)
        profile_menu.addAction(subs_action)

        logs_menu = QMenu("Logs & Security")
        menu_bar.addMenu(logs_menu)

        view_logs_action = QAction("View Security Logs")
        view_logs_action.triggered.connect(self._open_logs_viewer)
        logs_menu.addAction(view_logs_action)

        help_menu = QMenu("Help")
        menu_bar.addMenu(help_menu)

        about_action = QAction("About Guardian Karna")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # -------- community dock (left) --------
        self.community_dock = QDockWidget("", self)
        self.community_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        community_widget = QWidget()
        comm_layout = QHBoxLayout(community_widget)
        comm_layout.setContentsMargins(4, 4, 4, 4)

        self.community_inner = QWidget()
        inner_layout = QVBoxLayout(self.community_inner)

        header_row = QHBoxLayout()
        header_label = QLabel("<b>Guardian Karna Community</b>")
        header_row.addWidget(header_label)
        header_row.addStretch(1)
        inner_layout.addLayout(header_row)

        self.community_user_label = QLabel("You are: (Guest)")
        inner_layout.addWidget(self.community_user_label)

        self.community_messages = QListWidget()
        inner_layout.addWidget(self.community_messages)

        # chat bar
        chat_row = QHBoxLayout()
        self.community_input = QLineEdit()
        self.community_input.setPlaceholderText("Type a message…")
        self.community_input.returnPressed.connect(self._send_community_message)
        chat_row.addWidget(self.community_input)

        self.community_send_btn = QToolButton()
        self.community_send_btn.setText("🚀")
        self.community_send_btn.clicked.connect(self._send_community_message)
        chat_row.addWidget(self.community_send_btn)

        inner_layout.addLayout(chat_row)

        comm_layout.addWidget(self.community_inner)

        self.community_toggle_btn = QToolButton()
        self.community_toggle_btn.setText("◀")
        self.community_toggle_btn.clicked.connect(self._toggle_community)
        comm_layout.addWidget(self.community_toggle_btn)

        self.community_dock.setWidget(community_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.community_dock)
        self.community_collapsed = False
        self.community_dock.setMinimumWidth(260)

        # -------- performance dock (right) with flip --------
        self.perf_dock = QDockWidget("System / Protection", self)
        self.perf_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.perf_dock.setMinimumWidth(240)
        self.perf_dock.setMaximumWidth(280)

        perf_root = QWidget()
        perf_root_layout = QVBoxLayout(perf_root)
        perf_root_layout.setContentsMargins(8, 8, 8, 8)

        self.perf_stack = QStackedWidget()

        # front: performance view
        front = QWidget()
        front_layout = QVBoxLayout(front)
        self.cpu_donut = DonutChartWidget("CPU")
        self.mem_donut = DonutChartWidget("Memory")
        self.net_line = LineChartWidget("Network")
        front_layout.addWidget(self.cpu_donut)
        front_layout.addWidget(self.mem_donut)
        front_layout.addWidget(self.net_line)
        self.perf_stack.addWidget(front)

        # back: protection view
        back = QWidget()
        back_layout = QVBoxLayout(back)

        self.protection_anim_label = QLabel(
            "Background protection idle – waiting for sites..."
        )
        self.protection_anim_label.setWordWrap(True)
        back_layout.addWidget(self.protection_anim_label)

        self.protection_list = QListWidget()
        back_layout.addWidget(self.protection_list)
        self.perf_stack.addWidget(back)

        perf_root_layout.addWidget(self.perf_stack)

        self.perf_dock.setWidget(perf_root)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.perf_dock)

        # click to flip with delay
        perf_root.installEventFilter(self)
        self.perf_stack.installEventFilter(self)

        # -------- side dock for settings / subscription / login --------
        self.side_dock = QDockWidget("Panel", self)
        self.side_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.side_dock.hide()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.side_dock)
        self.tabifyDockWidget(self.perf_dock, self.side_dock)
        self.perf_dock.raise_()

    # ------------------- EVENT FILTER (for perf flip) -------------------

    def eventFilter(self, obj, event):
        if obj in (self.perf_dock.widget(), self.perf_stack) and event.type() == QEvent.Type.MouseButtonPress:
            QTimer.singleShot(50, self._flip_perf_view)
            return False
        return super().eventFilter(obj, event)

    # ------------------- SIGNALS -------------------

    def _connect_signals(self):
        self.security_engine.pre_scan_completed.connect(self._on_pre_scan_done)
        self.security_engine.deep_scan_completed.connect(self._on_deep_scan_done)
        self.perf_monitor.stats_updated.connect(self._on_perf_stats)
        self.web_view.urlChanged.connect(self._on_webview_url_changed)

    # ------------------- DOWNLOAD HANDLING -------------------

    def _on_download_requested(self, download: QWebEngineDownloadRequest):
        """
        Handle file downloads:
        - Show a 'scan' info box
        - Ask user where to save
        - Then accept the download
        """
        url = download.url().toString()
        file_name = download.downloadFileName() or "downloaded_file"

        # Simulated scan
        QMessageBox.information(
            self,
            "Guardian Scan",
            f"Guardian Karna will scan this download before saving:\n\n{file_name}\n\nSource: {url}",
        )

        # Ask save location
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Downloaded File",
            file_name
        )
        if not save_path:
            download.cancel()
            self.statusBar().showMessage("Download cancelled.", 3000)
            return

        # Set directory and file name
        # QWebEngineDownloadRequest expects directory + file name separately
        # We'll split them from save_path
        directory, fname = os.path.split(save_path)
        if directory:
            download.setDownloadDirectory(directory)
        if fname:
            download.setDownloadFileName(fname)

        download.accept()
        self.statusBar().showMessage(f"Downloading: {fname}", 5000)

    # ------------------- ACCOUNT / SIDE PANELS -------------------

    def _refresh_account_ui(self):
        acc = self.auth_manager.get_current()
        tier = "Premium" if acc.subscription == SubscriptionTier.PREMIUM else "Free"
        self.sub_button.setText(tier)
        self.account_label.setText(f"User: {acc.username}")
        self.mode_manager.set_subscription(acc.subscription)
        self.community_user_label.setText(f"You are: {acc.username}")

    def _close_side_panel(self):
        self.side_dock.hide()

    def _make_side_header(self, title: str):
        header_widget = QWidget()
        hl = QHBoxLayout(header_widget)
        hl.setContentsMargins(0, 0, 0, 0)
        back_btn = QToolButton()
        back_btn.setText("←")
        back_btn.clicked.connect(self._close_side_panel)
        hl.addWidget(back_btn)
        hl.addWidget(QLabel(f"<b>{title}</b>"))
        hl.addStretch(1)
        return header_widget

    def _show_settings_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        layout.addWidget(self._make_side_header("Settings"))

        acc = self.auth_manager.get_current()
        layout.addWidget(QLabel("<b>Account</b>"))
        layout.addWidget(QLabel(f"User: {acc.username}"))
        layout.addWidget(QLabel(f"Subscription: {'Premium' if acc.subscription == SubscriptionTier.PREMIUM else 'Free'}"))
        layout.addSpacing(8)

        layout.addWidget(QLabel("<b>Browser</b>"))
        layout.addWidget(QLabel(f"Mode: {self.mode_manager.get_mode().name}"))
        layout.addWidget(QLabel(f"Theme: {self.current_theme.title()}"))
        layout.addSpacing(8)

        btn_login = QPushButton("Login / Register")
        btn_login.clicked.connect(self._show_login_panel)
        layout.addWidget(btn_login)

        btn_sub = QPushButton("Open Subscription Plans")
        btn_sub.clicked.connect(self._show_subscription_panel)
        layout.addWidget(btn_sub)

        btn_logs = QPushButton("View Security Logs (Popup)")
        btn_logs.clicked.connect(self._open_logs_viewer)
        layout.addWidget(btn_logs)

        btn_about = QPushButton("About Guardian Karna")
        btn_about.clicked.connect(self._show_about)
        layout.addWidget(btn_about)

        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("QPushButton { background:#dc2626; color:white; border-radius:6px; padding:4px 10px; }")
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)

        layout.addStretch(1)

        self.side_dock.setWindowTitle("Settings")
        self.side_dock.setWidget(panel)
        self.side_dock.show()
        self.side_dock.raise_()

    def _logout(self):
        acc = self.auth_manager.get_current()
        acc.username = "Guest"
        acc.subscription = SubscriptionTier.FREE
        self._refresh_account_ui()

    def _show_subscription_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        layout.addWidget(self._make_side_header("Subscription"))

        layout.addWidget(QLabel("<b>Subscription Plans</b>"))

        free_card = QWidget()
        fl = QVBoxLayout(free_card)
        fl.addWidget(QLabel("🆓 Free Plan"))
        fl.addWidget(QLabel("- Basic protection"))
        fl.addWidget(QLabel("- Deep scan blocks page until finished"))
        fl.addWidget(QLabel("- Suitable for casual browsing"))
        layout.addWidget(free_card)

        premium_card = QWidget()
        pl = QVBoxLayout(premium_card)
        pl.addWidget(QLabel("⭐ Premium Plan"))
        pl.addWidget(QLabel("- Background deep scans with Safe Mode"))
        pl.addWidget(QLabel("- Fewer interruptions, smoother workflow"))
        pl.addWidget(QLabel("- Recommended for regular / professional users"))
        layout.addWidget(premium_card)

        btn_row = QHBoxLayout()
        free_btn = QPushButton("Use Free")
        free_btn.clicked.connect(self._set_free)
        btn_row.addWidget(free_btn)

        prem_btn = QPushButton("Upgrade to Premium")
        prem_btn.clicked.connect(self._set_premium)
        btn_row.addWidget(prem_btn)
        layout.addLayout(btn_row)

        layout.addStretch(1)

        self.side_dock.setWindowTitle("Subscription")
        self.side_dock.setWidget(panel)
        self.side_dock.show()
        self.side_dock.raise_()

    def _set_free(self):
        acc = self.auth_manager.get_current()
        acc.subscription = SubscriptionTier.FREE
        self._refresh_account_ui()

    def _set_premium(self):
        acc = self.auth_manager.get_current()
        acc.subscription = SubscriptionTier.PREMIUM
        self._refresh_account_ui()

    def _show_login_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        layout.addWidget(self._make_side_header("Account"))

        acc = self.auth_manager.get_current()
        layout.addWidget(QLabel("<b>Login / Register</b>"))
        layout.addWidget(QLabel("Set the name you want to use in Guardian Karna."))

        username_edit = QLineEdit()
        username_edit.setText(acc.username)
        layout.addWidget(QLabel("Account name"))
        layout.addWidget(username_edit)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")

        def save():
            acc.username = username_edit.text().strip() or "Guest"
            self._refresh_account_ui()

        save_btn.clicked.connect(save)
        btn_row.addWidget(save_btn)

        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("QPushButton { background:#dc2626; color:white; border-radius:6px; padding:4px 10px; }")
        logout_btn.clicked.connect(self._logout)
        btn_row.addWidget(logout_btn)

        layout.addLayout(btn_row)
        layout.addStretch(1)

        self.side_dock.setWindowTitle("Account")
        self.side_dock.setWidget(panel)
        self.side_dock.show()
        self.side_dock.raise_()

    # ------------------- COMMUNITY & PERFORMANCE -------------------

    def _toggle_community(self):
        if self.community_collapsed:
            self.community_inner.show()
            self.community_dock.setMinimumWidth(260)
            self.community_toggle_btn.setText("◀")
            self.community_collapsed = False
        else:
            self.community_inner.hide()
            self.community_dock.setMinimumWidth(40)
            self.community_toggle_btn.setText("▶")
            self.community_collapsed = True

    def _send_community_message(self):
        text = self.community_input.text().strip()
        if not text:
            return
        user = self.auth_manager.get_current().username or "Guest"
        display = f"{user}: {text}"

        item = QListWidgetItem(display)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
        item.setBackground(Qt.GlobalColor.darkGreen)
        item.setForeground(Qt.GlobalColor.white)

        self.community_messages.addItem(item)
        self.community_messages.scrollToBottom()
        self.community_input.clear()

    def _flip_perf_view(self):
        idx = self.perf_stack.currentIndex()
        if idx == 0:
            self.perf_stack.setCurrentIndex(1)
            self._refresh_protection_view()
        else:
            self.perf_stack.setCurrentIndex(0)

    def _refresh_protection_view(self):
        entries = self.log_manager.get_entries()
        if not entries:
            self.protection_anim_label.setText(
                "Background protection idle – waiting for sites..."
            )
        else:
            last = entries[-1]
            if last.final_risk in ("high", "disaster"):
                self.protection_anim_label.setText(
                    "Background protection:\n"
                    "1️⃣ Fetching content from server\n"
                    "2️⃣ Passing through twin defence firewalls\n"
                    "3️⃣ Removing dangerous scripts & hidden payloads\n"
                    "4️⃣ Delivering only safe parts to your browser"
                )
            else:
                self.protection_anim_label.setText(
                    "Background protection:\n"
                    "Monitoring traffic and checking headers, cookies and redirects.\n"
                    "Low-risk content flows through the shield."
                )

        self.protection_list.clear()
        for entry in entries[-20:][::-1]:
            t = time.strftime("%H:%M:%S", time.localtime(entry.timestamp))
            short = entry.url if len(entry.url) <= 40 else entry.url[:37] + "..."
            text = f"[{t}] {entry.action.upper()} ({entry.final_risk}) – {short}"
            self.protection_list.addItem(QListWidgetItem(text))

    # ------------------- VIEW / MODE / PERF -------------------

    def _on_mode_changed(self, index: int):
        if index == 0:
            self.mode_manager.set_mode(SecurityMode.BALANCED)
        elif index == 1:
            self.mode_manager.set_mode(SecurityMode.MODERATE)
        else:
            self.mode_manager.set_mode(SecurityMode.ADVANCED_DEFENCE)
        self.statusBar().showMessage("Mode updated", 2000)

    def _toggle_perf_panel(self, checked: bool):
        self.perf_dock.setVisible(checked)

    def _on_perf_stats(self, cpu: float, mem: float, net_rate: float):
        self.cpu_donut.set_value(cpu)
        self.mem_donut.set_value(mem)
        self.net_line.add_value(net_rate)

    # ------------------- GAMES / LOGS / ABOUT -------------------

    def _open_game(self):
        dlg = ClickGameDialog(self.game_stats, self)
        dlg.exec()

    def _open_game_stats(self):
        dlg = GameStatsDialog(self.game_stats, self)
        dlg.exec()

    def _open_logs_viewer(self):
        dlg = LogViewerDialog(self.log_manager, self)
        dlg.exec()

    def _show_about(self):
        QMessageBox.information(
            self,
            "About Guardian Karna",
            "Guardian Karna Browser\n\n"
            "• Risk-based pre-scan and deep scan\n"
            "• Balanced / Moderate / Advanced Defence modes\n"
            "• Performance & background protection flip panel\n"
            "• Community side chat and recent previews\n"
            "• Accounts with Free / Premium modes\n"
            "• Download scanning with Save dialog\n"
        )

    # ------------------- RECENT TABS -------------------

    def _add_to_recent(self, url: str):
        if not url:
            return
        if url in self.recent_urls:
            self.recent_urls.remove(url)
        self.recent_urls.insert(0, url)
        if len(self.recent_urls) > 8:
            self.recent_urls = self.recent_urls[:8]
        self._refresh_recent_toolbar()

    def _refresh_recent_toolbar(self):
        self.recent_toolbar.clear()
        if not self.recent_urls:
            self.recent_toolbar.addWidget(QLabel("Recent: (empty)"))
            return
        self.recent_toolbar.addWidget(QLabel("Recent: "))
        for url in self.recent_urls:
            btn = QToolButton()
            short = url if len(url) <= 30 else url[:27] + "..."
            btn.setText(short)
            btn.setToolTip(url)
            btn.clicked.connect(lambda checked=False, u=url: self._open_recent(u))
            self.recent_toolbar.addWidget(btn)

    def _open_recent(self, url: str):
        self.url_bar.setText(url)
        self.load_url()

    # ------------------- URL FLOW -------------------

    def _on_webview_url_changed(self, qurl: QUrl):
        if not self._is_home:
            self.url_bar.setText(qurl.toString())

    def load_url(self):
        raw = self.url_bar.text().strip()
        if not raw:
            return

        self._is_home = False

        # handle search vs direct URL
        if not raw.startswith("http://") and not raw.startswith("https://"):
            if "." in raw:
                # looks like site
                raw = "https://" + raw
            else:
                # plain search text -> Google
                encoded = raw.replace(" ", "+")
                raw = "https://www.google.com/search?q=" + encoded

        url = QUrl(raw)
        if not url.isValid():
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL.")
            return

        self._current_url_being_scanned = url.toString()
        self._current_risk = None
        self._deep_scan_running = False
        self.safe_mode_label.setText("")
        self.scan_status_label.setText("Pre-scan running...")

        self.security_engine.start_pre_scan(self._current_url_being_scanned)

    def _on_pre_scan_done(self, url: str, risk: str):
        if url != self._current_url_being_scanned:
            return

        self._current_risk = risk
        self.scan_status_label.setText(f"Pre-scan: {risk.upper()}")

        if risk == "low":
            self._load_page_normal(url)
            self._log_event(url, risk, risk, "allowed")
            return

        allow_parallel = self.mode_manager.allow_parallel_scan(risk)
        if allow_parallel:
            self._load_page_safe(url)
            self._start_deep_scan(url, risk, show_game=False)
        else:
            self._block_and_game(url, risk)

    def _start_deep_scan(self, url: str, risk: str, show_game: bool):
        self._deep_scan_running = True
        self.scan_status_label.setText("Deep scan running...")
        if show_game:
            self._open_game()
        self.security_engine.start_deep_scan(url, risk)

    def _on_deep_scan_done(self, url: str, final_risk: str):
        try:
            if url != self._current_url_being_scanned:
                return

            self._deep_scan_running = False
            # record the final risk as the current risk for future logs
            self._current_risk = final_risk
            self.scan_status_label.setText(f"Deep scan: {final_risk.upper()}")

            action = "allowed"
            if final_risk == "disaster":
                action = "blocked"
                QMessageBox.critical(
                    self,
                    "Blocked",
                    "This site is classified as DISASTER level.\nAccess blocked for safety."
                )
                self.web_view.setHtml(
                    "<html><body style='background:#111827;color:#f97373;"
                    "font-family:sans-serif;text-align:center;padding-top:100px;'>"
                    "<h2>Access Blocked</h2>"
                    "<p>This website is extremely dangerous.</p>"
                    "</body></html>"
                )
            elif self.safe_mode_label.text():
                # page was loaded in safe mode earlier
                action = "safe_mode"

            self._log_event(url, self._current_risk or "unknown", final_risk, action)
        except Exception as e:
            self.statusBar().showMessage(f"Deep-scan error: {e}", 5000)

    # ------------------- LOGGING & PAGE LOAD -------------------

    def _log_event(self, url: str, pre: str, final: str, action: str):
        self.log_manager.add_entry(
            url=url,
            pre_risk=pre,
            final_risk=final,
            mode=self.mode_manager.get_mode(),
            subscription=self.mode_manager.get_subscription(),
            action=action,
        )
        if self.perf_stack.currentIndex() == 1:
            self._refresh_protection_view()

    def _load_page_normal(self, url: str):
        self.safe_mode_label.setText("")
        self.web_view.setUrl(QUrl(url))
        self.statusBar().showMessage("Page loaded normally.", 2000)
        self._add_to_recent(url)

    def _load_page_safe(self, url: str):
        self.safe_mode_label.setText("SAFE MODE: Some features restricted.")
        self.web_view.setUrl(QUrl(url))
        self.statusBar().showMessage("Page loaded in Safe Mode.", 3000)
        self._add_to_recent(url)

    def _block_and_game(self, url: str, risk: str):
        msg = QMessageBox(self)
        msg.setWindowTitle("Deep Scan Required")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(
            f"This site is {risk.upper()} risk.\n\n"
            "Deep scan is required before opening.\n"
            "You can play a mini-game while waiting."
        )
        start_btn = msg.addButton("Start Scan + Game", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        if msg.clickedButton() == start_btn:
            self.web_view.setHtml(
                "<html><body style='background:#020617;color:#e5e7eb;"
                "font-family:sans-serif;text-align:center;padding-top:100px;'>"
                "<h2>Scanning in progress...</h2>"
                "<p>Please wait while Guardian Karna scans this site.</p>"
                "</body></html>"
            )
            self._start_deep_scan(url, risk, show_game=True)
        else:
            self.scan_status_label.setText("Scan cancelled.")
            self._log_event(url, risk, risk, "cancelled")
