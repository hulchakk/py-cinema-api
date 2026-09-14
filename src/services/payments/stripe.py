from decimal import Decimal
import stripe

from config.settings import settings
from services.payments.interfaces import PaymentInterface

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService(PaymentInterface):
    async def create_checkout_session(
        self,
        order_id: int,
        total_amount: Decimal,
        success_url: str,
        cancel_url: str,
    ) -> str:
        amount_in_cents = int(total_amount * 100)

        session = await stripe.checkout.Session.create_async(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Cinema Order #{order_id}",
                        },
                        "unit_amount": amount_in_cents,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            metadata={"order_id": str(order_id)},
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return str(session.url)
