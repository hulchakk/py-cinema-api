from abc import ABC, abstractmethod
from typing import Any, Dict, List


class EmailSenderInterface(ABC):

    @abstractmethod
    async def send_activation_email(self, email: str, activation_link: str) -> None:
        """
        Asynchronously send an account activation email.

        Args:
            email (str): The recipient's email address.
            activation_link (str): The activation link to include in the email.
        """
        pass

    @abstractmethod
    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        """
        Asynchronously send an email confirming that the account has been activated.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to include in the email.
        """
        pass

    @abstractmethod
    async def send_password_reset_email(self, email: str, reset_link: str) -> None:
        """
        Asynchronously send a password reset request email.

        Args:
            email (str): The recipient's email address.
            reset_link (str): The password reset link to include in the email.
        """
        pass

    @abstractmethod
    async def send_password_reset_complete_email(
        self, email: str, login_link: str
    ) -> None:
        """
        Asynchronously send an email confirming that the password has been reset.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to include in the email.
        """
        pass

    @abstractmethod
    async def send_order_confirmation_email(
        self, email: str, order_id: str, order_details: Dict[str, Any]
    ) -> None:
        """
        Asynchronously send an order confirmation email after a successful purchase.

        Args:
            email (str): The recipient's email address.
            order_id (str): The unique identifier of the order.
            order_details (Dict[str, Any]): Details of the order (items, total_amount, etc.).
        """
        pass

    @abstractmethod
    async def send_payment_receipt_email(
        self, email: str, payment_id: str, amount: float, currency: str = "USD"
    ) -> None:
        """
        Asynchronously send a payment confirmation/receipt email.

        Args:
            email (str): The recipient's email address.
            payment_id (str): The payment transaction ID (e.g. Stripe charge ID).
            amount (float): The total amount paid.
            currency (str): The currency of the payment. Defaults to 'USD'.
        """
        pass
