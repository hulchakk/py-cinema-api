from abc import ABC, abstractmethod
from decimal import Decimal


class PaymentInterface(ABC):
    """
    Interface for Payment services.
    Defines method for creating checkout session.
    """

    @abstractmethod
    async def create_checkout_session(
        self, order_id: int, total_amount: Decimal, success_url: str, cancel_url: str
    ) -> str:
        """
        Create a new checkout session.

        :param order_id: Unique identifier of the order.
        :param total_amount: Total payment amount.
        :param success_url: URL to redirect the user after a successful payment.
        :param cancel_url: URL to redirect the user if they cancel the payment.
        :return: A URL string to redirect the client to the payment gateway.
        """
        pass
