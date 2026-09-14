import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from exceptions.email import BaseEmailError
from services.notifications.interfaces import EmailSenderInterface


class EmailSender(EmailSenderInterface):

    def __init__(
        self,
        hostname: str,
        port: int,
        email: str,
        password: str,
        use_tls: bool,
        template_dir: str,
        activation_email_template_name: str,
        activation_complete_email_template_name: str,
        password_email_template_name: str,
        password_complete_email_template_name: str,
        order_confirmation_email_template_name: str,
        payment_receipt_email_template_name: str,
    ):
        self._hostname = hostname
        self._port = port
        self._email = email
        self._password = password
        self._use_tls = use_tls
        self._activation_email_template_name = activation_email_template_name
        self._activation_complete_email_template_name = (
            activation_complete_email_template_name
        )
        self._password_email_template_name = password_email_template_name
        self._password_complete_email_template_name = (
            password_complete_email_template_name
        )
        self._order_confirmation_email_template_name = (
            order_confirmation_email_template_name
        )
        self._payment_receipt_email_template_name = payment_receipt_email_template_name

        self._env = Environment(loader=FileSystemLoader(template_dir))

    async def _send_email(
        self, recipient: str, subject: str, html_content: str
    ) -> None:
        """
        Asynchronously send an email with the given subject and HTML content.

        Args:
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            html_content (str): The HTML content of the email.

        Raises:
            BaseEmailError: If sending the email fails.
        """
        message = MIMEMultipart()
        message["From"] = self._email
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(html_content, "html"))

        try:
            smtp = aiosmtplib.SMTP(
                hostname=self._hostname, port=self._port, start_tls=self._use_tls
            )
            await smtp.connect()
            if self._use_tls:
                await smtp.starttls()
            await smtp.login(self._email, self._password)
            await smtp.sendmail(self._email, [recipient], message.as_string())
            await smtp.quit()
        except aiosmtplib.SMTPException as error:
            logging.error(f"Failed to send email to {recipient}: {error}")
            raise BaseEmailError(f"Failed to send email to {recipient}: {error}")

    async def send_activation_email(self, email: str, activation_link: str) -> None:
        """
        Send an account activation email asynchronously.

        Args:
            email (str): The recipient's email address.
            activation_link (str): The activation link to be included in the email.
        """
        template = self._env.get_template(self._activation_email_template_name)
        html_content = template.render(email=email, activation_link=activation_link)
        subject = "Account Activation"
        await self._send_email(email, subject, html_content)

    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        """
        Send an account activation completion email asynchronously.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to be included in the email.
        """
        template = self._env.get_template(self._activation_complete_email_template_name)
        html_content = template.render(email=email, login_link=login_link)
        subject = "Account Activated Successfully"
        await self._send_email(email, subject, html_content)

    async def send_password_reset_email(self, email: str, reset_link: str) -> None:
        """
        Send a password reset request email asynchronously.

        Args:
            email (str): The recipient's email address.
            reset_link (str): The reset link to be included in the email.
        """
        template = self._env.get_template(self._password_email_template_name)
        html_content = template.render(email=email, reset_link=reset_link)
        subject = "Password Reset Request"
        await self._send_email(email, subject, html_content)

    async def send_password_reset_complete_email(
        self, email: str, login_link: str
    ) -> None:
        """
        Send a password reset completion email asynchronously.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to be included in the email.
        """
        template = self._env.get_template(self._password_complete_email_template_name)
        html_content = template.render(email=email, login_link=login_link)
        subject = "Your Password Has Been Successfully Reset"
        await self._send_email(email, subject, html_content)

    async def send_order_confirmation_email(
        self, email: str, order_id: str, order_details: Dict[str, Any]
    ) -> None:
        """
        Send an order confirmation email asynchronously.

        Args:
            email (str): The recipient's email address.
            order_id (str): The unique identifier of the order.
            order_details (Dict[str, Any]): Details of the order (items, total_amount, etc.).
        """
        template = self._env.get_template(self._order_confirmation_email_template_name)
        html_content = template.render(
            email=email, order_id=order_id, order_details=order_details
        )
        subject = f"Order Confirmation #{order_id}"
        await self._send_email(email, subject, html_content)

    async def send_payment_receipt_email(
        self, email: str, payment_id: str, amount: float, currency: str = "USD"
    ) -> None:
        """
        Send a payment receipt email asynchronously.

        Args:
            email (str): The recipient's email address.
            payment_id (str): The payment transaction ID.
            amount (float): The total amount paid.
            currency (str): The currency of the payment.
        """
        template = self._env.get_template(self._payment_receipt_email_template_name)
        html_content = template.render(
            email=email, payment_id=payment_id, amount=amount, currency=currency
        )
        subject = f"Payment Receipt #{payment_id}"
        await self._send_email(email, subject, html_content)
