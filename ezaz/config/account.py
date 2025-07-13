
from contextlib import suppress

from ..exception import SubscriptionConfigNotFound
from .subconfig import SubConfig
from .subscription import SubscriptionConfig


class AccountConfig(SubConfig):
    @classmethod
    def _DEFAULT_SUBSCRIPTION_KEY(cls):
        return 'default_subscription'

    @classmethod
    def _SUBSCRIPTION_KEY(cls, subscription):
        return f'subscription:{subscription}'

    @property
    def default_subscription(self):
        with suppress(KeyError):
            return self._config[self._DEFAULT_SUBSCRIPTION_KEY()]
        raise SubscriptionConfigNotFound

    @default_subscription.setter
    def default_subscription(self, subscription):
        if not subscription:
            del self.default_subscription
        else:
            self._config[self._DEFAULT_SUBSCRIPTION_KEY()] = subscription
            self._save()

    @default_subscription.deleter
    def default_subscription(self):
        with suppress(KeyError):
            del self._config[self._DEFAULT_SUBSCRIPTION_KEY()]
            self._save()

    def get_subscription(self, subscription):
        k = self._SUBSCRIPTION_KEY(subscription)
        return SubscriptionConfig(self, self._config.setdefault(k, {}))

    def del_subscription(self, subscription):
        k = self._SUBSCRIPTION_KEY(subscription)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    def get_default_subscription(self):
        return self.get_subscription(self.default_subscription)
