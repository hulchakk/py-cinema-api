from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict

from database.models.payments import PaymentStatusEnum


class PaymentListResponseSchema(BaseModel):
    id: int
    order_id: int
    status: PaymentStatusEnum
    amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentItemResponseSchema(BaseModel):
    id: int
    movie_id: int
    movie_name: str
    price_at_payment: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentRetrieveResponseSchema(PaymentListResponseSchema):
    items: List[PaymentItemResponseSchema]
