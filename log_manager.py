# log_manager.py
from dataclasses import dataclass, field
from typing import List
import time

from mode_manager import SecurityMode, SubscriptionTier


@dataclass
class ScanLogEntry:
    timestamp: float
    url: str
    pre_risk: str
    final_risk: str
    mode: SecurityMode
    subscription: SubscriptionTier
    action: str  # "allowed", "blocked", "safe_mode", etc.


@dataclass
class LogManager:
    entries: List[ScanLogEntry] = field(default_factory=list)

    def add_entry(
        self,
        url: str,
        pre_risk: str,
        final_risk: str,
        mode: SecurityMode,
        subscription: SubscriptionTier,
        action: str,
    ):
        self.entries.append(
            ScanLogEntry(
                timestamp=time.time(),
                url=url,
                pre_risk=pre_risk,
                final_risk=final_risk,
                mode=mode,
                subscription=subscription,
                action=action,
            )
        )

    def get_entries(self) -> List[ScanLogEntry]:
        return self.entries

    def clear(self):
        self.entries.clear()
