import uuid
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BalanceOverflow, InsufficientFunds, WalletNotFound
from app.models import Wallet
from app.schemas import OperationType


async def create_wallet(session: AsyncSession) -> Wallet:
    wallet = Wallet(balance=Decimal("0"))
    session.add(wallet)
    await session.commit()
    return wallet


async def get_balance(session: AsyncSession, wallet_id: uuid.UUID) -> Decimal:
    balance = await session.scalar(
        select(Wallet.balance).where(Wallet.id == wallet_id)
    )
    if balance is None:
        raise WalletNotFound
    return balance


async def apply_operation(
    session: AsyncSession,
    wallet_id: uuid.UUID,
    operation_type: OperationType,
    amount: Decimal,
) -> Decimal:
    """Атомарно изменяет баланс одним UPDATE ... RETURNING.

    PostgreSQL берёт блокировку строки на время UPDATE, а при ожидании
    блокировки перепроверяет условие WHERE по свежей версии строки
    (READ COMMITTED), поэтому параллельные списания не уводят баланс в минус,
    а пополнения не теряются (нет цикла read-modify-write в приложении).
    """
    stmt = update(Wallet).where(Wallet.id == wallet_id)
    if operation_type is OperationType.DEPOSIT:
        stmt = stmt.values(balance=Wallet.balance + amount)
    else:
        stmt = stmt.where(Wallet.balance >= amount).values(
            balance=Wallet.balance - amount
        )
    stmt = stmt.returning(Wallet.balance)

    try:
        balance = await session.scalar(stmt)
    except DBAPIError:  # numeric field overflow
        await session.rollback()
        raise BalanceOverflow

    if balance is None:
        await session.rollback()
        exists = await session.scalar(
            select(Wallet.id).where(Wallet.id == wallet_id)
        )
        if exists is None:
            raise WalletNotFound
        raise InsufficientFunds

    await session.commit()
    return balance
