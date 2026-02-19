import os
import sys
import pytest

# ensure project root is on sys.path so tests work regardless of how pytest
# is invoked; this mirrors what setting PYTHONPATH=. would do.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mode_manager import ModeManager, SecurityMode, SubscriptionTier
from auth import AuthManager, UserAccount, Provider
from log_manager import LogManager


def test_mode_manager_defaults():
    mm = ModeManager()
    assert mm.get_mode() == SecurityMode.BALANCED
    assert mm.get_subscription() == SubscriptionTier.FREE
    assert not mm.is_premium()


def test_mode_manager_subscription():
    mm = ModeManager()
    mm.set_subscription(SubscriptionTier.PREMIUM)
    assert mm.is_premium()


def test_mode_manager_allow_parallel():
    mm = ModeManager()
    # balanced free
    mm.set_subscription(SubscriptionTier.FREE)
    mm.set_mode(SecurityMode.BALANCED)
    assert mm.allow_parallel_scan("low")
    assert mm.allow_parallel_scan("medium")
    assert not mm.allow_parallel_scan("high")
    assert not mm.allow_parallel_scan("disaster")
    
    # balanced premium
    mm.set_subscription(SubscriptionTier.PREMIUM)
    assert mm.allow_parallel_scan("high")
    
    mm.set_mode(SecurityMode.ADVANCED_DEFENCE)
    # "low" is always allowed even in strictest mode
    assert mm.allow_parallel_scan("low")
    assert not mm.allow_parallel_scan("high")


def test_auth_manager():
    am = AuthManager()
    guest = am.get_current()
    assert guest.username == "Guest"
    assert guest.provider == Provider.GUEST
    assert guest.subscription == SubscriptionTier.FREE
    # add and switch
    user = UserAccount("alice", Provider.LOCAL, SubscriptionTier.PREMIUM)
    am.add_account(user)
    am.set_current(user)
    assert am.get_current().username == "alice"
    # AuthManager itself has no premium helper, just check subscription field
    assert am.get_current().subscription == SubscriptionTier.PREMIUM


def test_log_manager():
    lm = LogManager()
    assert lm.get_entries() == []
    lm.add_entry("http://example.com", "low", "low", SecurityMode.BALANCED, SubscriptionTier.FREE, "allowed")
    assert len(lm.get_entries()) == 1
    lm.clear()
    assert lm.get_entries() == []
