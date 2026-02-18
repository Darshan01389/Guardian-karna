# performance_monitor.py
from collections import deque
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import psutil

class PerformanceMonitor(QObject):
    stats_updated = pyqtSignal(float, float, float)  # cpu, mem, net_rate

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_stats)
        self.interval_ms = 1000
        self.prev_net_bytes = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        self.timer.start(self.interval_ms)

    def _update_stats(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent

        net = psutil.net_io_counters()
        total_bytes = net.bytes_sent + net.bytes_recv
        delta = total_bytes - self.prev_net_bytes
        self.prev_net_bytes = total_bytes
        # bytes per second approx
        net_rate_kb = delta / 1024.0

        self.stats_updated.emit(cpu, mem, net_rate_kb)
