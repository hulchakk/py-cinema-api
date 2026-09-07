from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict

from database.models.orders import OrderStatusEnum


class OrderListResponseSchema(BaseModel):
    id: int
    status: OrderStatusEnum
    total_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderItemResponseSchema(BaseModel):
    id: int
    movie_id: int
    movie_name: str
    price_at_order: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderRetrieveResponseSchema(OrderListResponseSchema):
    items: List[OrderItemResponseSchema]
