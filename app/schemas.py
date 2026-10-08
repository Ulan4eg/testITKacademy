import enum
import uuid
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer

# В JSON баланс отдаётся числом (как в примере из задания).
# Numeric(15, 2) целиком помещается в float без потери точности.
MoneyOut = Annotated[Decimal, PlainSerializer(float, return_type=float)]


class OperationType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationRequest(BaseModel):
    operation_type: OperationType
    amount: Decimal = Field(gt=0, max_digits=15, decimal_places=2)


class WalletResponse(BaseModel):
    wallet_id: uuid.UUID
    balance: MoneyOut
