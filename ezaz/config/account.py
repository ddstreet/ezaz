
from contextlib import suppress

from ..exception import SubscriptionConfigNotFound
from .subconfig import SubConfig
from .subscription import SubscriptionConfig


class AccountConfig(SubConfig):
    @classmethod
    def _CURRENT_SUBSCRIPTION_KEY(cls):
        return 'current_subscription'

    @classmethod
    def _SUBSCRIPTION_KEY(cls, subscription):
        return f'subscription:{subscription}'

    @property
    def current_subscription(self):
        with suppress(KeyError):
            return self._config[self._CURRENT_SUBSCRIPTION_KEY()]
        raise SubscriptionConfigNotFound

    @current_subscription.setter
    def current_subscription(self, subscription):
        if not subscription:
            del self.current_subscription
        else:
            self._config[self._CURRENT_SUBSCRIPTION_KEY()] = subscription
            self._save()

    @current_subscription.deleter
    def current_subscription(self):
        with suppress(KeyError):
            del self._config[self._CURRENT_SUBSCRIPTION_KEY()]
            self._save()

    def get_subscription(self, subscription):
        k = self._SUBSCRIPTION_KEY(subscription)
        return SubscriptionConfig(self, self._config.setdefault(k, {}))

    def del_subscription(self, subscription):
        k = self._SUBSCRIPTION_KEY(subscription)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    def get_current_subscription(self):
        return self.get_subscription(self.current_subscription)
