# security_engine.py
import random
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class SecurityEngine(QObject):
    pre_scan_completed = pyqtSignal(str, str)  # url, risk_level
    deep_scan_completed = pyqtSignal(str, str) # url, final_risk_level

    def __init__(self, parent=None):
        super().__init__(parent)

    def classify_risk(self, url: str) -> str:
        """
        Very simple mock risk logic.
        You can replace with real rules / APIs later.
        """
        url_lower = url.lower()
        if url_lower.startswith("http://"):
            base = "high"
        elif "login" in url_lower or "bank" in url_lower:
            base = "high"
        elif "google.com" in url_lower or "chatgpt.com" in url_lower:
            base = "low"
        else:
            base = random.choice(["low", "medium", "high"])

        # small chance of disaster
        if base == "high" and random.random() < 0.3:
            return "disaster"
        return base

    def start_pre_scan(self, url: str):
        # simulate quick pre-scan
        risk_level = self.classify_risk(url)
        # we can simulate small delay
        QTimer.singleShot(500, lambda: self.pre_scan_completed.emit(url, risk_level))

    def start_deep_scan(self, url: str, initial_risk: str):
        """
        Simulated deep scan in 'sandbox'.
        Longer delay, might lower risk slightly or confirm disaster.
        """
        def complete():
            # if disaster or high, chance to stay same or lower to high/medium
            if initial_risk == "disaster":
                final = random.choice(["disaster", "high"])
            elif initial_risk == "high":
                final = random.choice(["high", "medium"])
            else:
                final = initial_risk
            self.deep_scan_completed.emit(url, final)

        # 3–5 seconds simulated deep scan
        delay_ms = random.randint(3000, 5000)
        QTimer.singleShot(delay_ms, complete)
