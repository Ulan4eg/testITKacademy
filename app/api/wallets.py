import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import services
from app.database import get_session
from app.schemas import OperationRequest, WalletResponse

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(session: AsyncSession = Depends(get_session)):
    wallet = await services.create_wallet(session)
    return WalletResponse(wallet_id=wallet.id, balance=wallet.balance)


@router.post("/{wallet_id}/operation", response_model=WalletResponse)
async def wallet_operation(
    wallet_id: uuid.UUID,
    body: OperationRequest,
    session: AsyncSession = Depends(get_session),
):
    balance = await services.apply_operation(
        session, wallet_id, body.operation_type, body.amount
    )
    return WalletResponse(wallet_id=wallet_id, balance=balance)


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    balance = await services.get_balance(session, wallet_id)
    return WalletResponse(wallet_id=wallet_id, balance=balance)
