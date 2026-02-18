# mode_manager.py
from enum import Enum, auto

class SecurityMode(Enum):
    BALANCED = auto()
    MODERATE = auto()
    ADVANCED_DEFENCE = auto()

class SubscriptionTier(Enum):
    FREE = auto()
    PREMIUM = auto()

class ModeManager:
    def __init__(self):
        self._mode = SecurityMode.BALANCED
        self._subscription = SubscriptionTier.FREE

    def set_mode(self, mode: SecurityMode):
        self._mode = mode

    def get_mode(self) -> SecurityMode:
        return self._mode

    def set_subscription(self, tier: SubscriptionTier):
        self._subscription = tier

    def get_subscription(self) -> SubscriptionTier:
        return self._subscription

    def is_premium(self) -> bool:
        return self._subscription == SubscriptionTier.PREMIUM

    # Decision logic based on mode + subscription
    def allow_parallel_scan(self, risk_level: str) -> bool:
        """
        risk_level: 'low', 'medium', 'high', 'disaster'
        """
        mode = self._mode
        premium = self.is_premium()

        if risk_level == "low":
            return True  # always fine

        if mode == SecurityMode.ADVANCED_DEFENCE:
            # strictest mode, no parallel risky browsing
            return False

        if mode == SecurityMode.MODERATE:
            # prefers continuity
            return True if premium else (risk_level in ("medium",))

        if mode == SecurityMode.BALANCED:
            if premium:
                return risk_level in ("medium", "high")
            else:
                return risk_level == "medium"

        return False
