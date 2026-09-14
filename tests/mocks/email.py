from services.notifications.interfaces import EmailSenderInterface


class MockEmailSender(EmailSenderInterface):
    async def send_activation_email(self, email: str, activation_link: str) -> None:
        pass

    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        pass

    async def send_password_reset_email(self, email: str, reset_link: str) -> None:
        pass

    async def send_password_reset_complete_email(
        self, email: str, login_link: str
    ) -> None:
        pass

    async def send_order_confirmation_email(
        self, email: str, order_id: str, order_details: dict
    ) -> None:
        pass

    async def send_payment_receipt_email(
        self, email: str, payment_id: str, amount: float, currency: str = "USD"
    ) -> None:
        pass
