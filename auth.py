# auth.py
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout, QMessageBox
)

from mode_manager import SubscriptionTier


class Provider(Enum):
    LOCAL = "Local"
    GOOGLE = "Google"
    BRAVE = "Brave"
    GUEST = "Guest"


@dataclass
class UserAccount:
    username: str
    provider: Provider
    subscription: SubscriptionTier


class AuthManager:
    def __init__(self):
        self._accounts: Dict[str, UserAccount] = {}
        self._current: Optional[UserAccount] = None

        # default guest user
        guest = UserAccount("Guest", Provider.GUEST, SubscriptionTier.FREE)
        self._accounts[self._make_key(guest)] = guest
        self._current = guest

    def _make_key(self, acc: UserAccount) -> str:
        return f"{acc.provider.value}:{acc.username}"

    def add_account(self, acc: UserAccount):
        self._accounts[self._make_key(acc)] = acc

    def get_current(self) -> UserAccount:
        return self._current

    def set_current(self, acc: UserAccount):
        self._current = acc
        # ensure it is stored
        self._accounts[self._make_key(acc)] = acc

    def list_accounts(self):
        return list(self._accounts.values())


class LoginDialog(QDialog):
    """
    Simple login / account creation dialog.
    - Local account: choose username + subscription
    - External: pick Google / Brave / Guest (simulated)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login / Switch Account")
        self.selected_account: Optional[UserAccount] = None

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>Create Local Account</b>"))

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username (e.g., Darshan)")
        layout.addWidget(self.username_edit)

        self.sub_combo = QComboBox()
        self.sub_combo.addItem("Free")
        self.sub_combo.addItem("Premium")
        layout.addWidget(QLabel("Subscription:"))
        layout.addWidget(self.sub_combo)

        create_btn = QPushButton("Create / Login with Local Account")
        create_btn.clicked.connect(self._create_local)
        layout.addWidget(create_btn)

        layout.addSpacing(16)
        layout.addWidget(QLabel("<b>Or use external provider (simulated)</b>"))

        self.provider_combo = QComboBox()
        self.provider_combo.addItem("Google")
        self.provider_combo.addItem("Brave")
        self.provider_combo.addItem("Guest")
        layout.addWidget(self.provider_combo)

        ext_btn = QPushButton("Continue with Selected Provider")
        ext_btn.clicked.connect(self._use_external)
        layout.addWidget(ext_btn)

        btn_row = QHBoxLayout()
        close_btn = QPushButton("Cancel")
        close_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _create_local(self):
        name = self.username_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing name", "Please enter a username.")
            return

        sub_text = self.sub_combo.currentText()
        tier = SubscriptionTier.PREMIUM if sub_text == "Premium" else SubscriptionTier.FREE

        self.selected_account = UserAccount(
            username=name,
            provider=Provider.LOCAL,
            subscription=tier,
        )
        self.accept()

    def _use_external(self):
        provider_text = self.provider_combo.currentText()
        if provider_text == "Google":
            provider = Provider.GOOGLE
            username = "GoogleUser"
            tier = SubscriptionTier.PREMIUM  # you can change this
        elif provider_text == "Brave":
            provider = Provider.BRAVE
            username = "BraveUser"
            tier = SubscriptionTier.PREMIUM
        else:
            provider = Provider.GUEST
            username = "Guest"
            tier = SubscriptionTier.FREE

        self.selected_account = UserAccount(
            username=username,
            provider=provider,
            subscription=tier,
        )
        self.accept()
