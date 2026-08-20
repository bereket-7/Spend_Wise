"""Unit tests for subscription manager helpers"""
from utils.subscription_manager import SubscriptionManager


class TestSubscriptionManager:
    def setup_method(self):
        self.mgr = SubscriptionManager()

    def test_get_alternative_services(self):
        alts = self.mgr.get_alternative_services('netflix')
        assert isinstance(alts, list)

    def test_get_alternative_services_unknown(self):
        alts = self.mgr.get_alternative_services('unknown_service_xyz')
        assert isinstance(alts, list)
