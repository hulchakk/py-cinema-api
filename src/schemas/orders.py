from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from database.models.orders import OrderStatusEnum


class OrderListResponseSchema(BaseModel):
    id: int
    status: OrderStatusEnum
    total_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
