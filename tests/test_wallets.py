import asyncio
import uuid

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

API = "/api/v1/wallets"


async def operate(client, wallet_id, operation_type, amount):
    return await client.post(
        f"{API}/{wallet_id}/operation",
        json={"operation_type": operation_type, "amount": amount},
    )


async def test_create_wallet(client):
    response = await client.post(API)
    assert response.status_code == 201
    body = response.json()
    uuid.UUID(body["wallet_id"])
    assert body["balance"] == 0


async def test_get_balance(client, wallet_id):
    response = await client.get(f"{API}/{wallet_id}")
    assert response.status_code == 200
    assert response.json() == {"wallet_id": wallet_id, "balance": 0}


async def test_get_balance_not_found(client):
    response = await client.get(f"{API}/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_get_balance_invalid_uuid(client):
    response = await client.get(f"{API}/not-a-uuid")
    assert response.status_code == 422


async def test_deposit(client, wallet_id):
    response = await operate(client, wallet_id, "DEPOSIT", 1000)
    assert response.status_code == 200
    assert response.json()["balance"] == 1000

    response = await client.get(f"{API}/{wallet_id}")
    assert response.json()["balance"] == 1000


async def test_withdraw(client, wallet_id):
    await operate(client, wallet_id, "DEPOSIT", 1000)
    response = await operate(client, wallet_id, "WITHDRAW", 400)
    assert response.status_code == 200
    assert response.json()["balance"] == 600


async def test_withdraw_exact_balance(client, wallet_id):
    await operate(client, wallet_id, "DEPOSIT", 500)
    response = await operate(client, wallet_id, "WITHDRAW", 500)
    assert response.status_code == 200
    assert response.json()["balance"] == 0


async def test_withdraw_insufficient_funds(client, wallet_id):
    await operate(client, wallet_id, "DEPOSIT", 100)
    response = await operate(client, wallet_id, "WITHDRAW", 101)
    assert response.status_code == 409

    response = await client.get(f"{API}/{wallet_id}")
    assert response.json()["balance"] == 100


async def test_fractional_amount(client, wallet_id):
    response = await operate(client, wallet_id, "DEPOSIT", 10.25)
    assert response.status_code == 200
    assert response.json()["balance"] == 10.25


async def test_operation_wallet_not_found(client):
    response = await operate(client, uuid.uuid4(), "DEPOSIT", 10)
    assert response.status_code == 404

    response = await operate(client, uuid.uuid4(), "WITHDRAW", 10)
    assert response.status_code == 404


@pytest.mark.parametrize("amount", [0, -10, "abc", None, 1.234])
async def test_invalid_amount(client, wallet_id, amount):
    response = await operate(client, wallet_id, "DEPOSIT", amount)
    assert response.status_code == 422


async def test_invalid_operation_type(client, wallet_id):
    response = await operate(client, wallet_id, "TRANSFER", 10)
    assert response.status_code == 422


async def test_missing_fields(client, wallet_id):
    response = await client.post(f"{API}/{wallet_id}/operation", json={})
    assert response.status_code == 422


async def test_amount_too_large(client, wallet_id):
    response = await operate(client, wallet_id, "DEPOSIT", 999_999_999_999_999)
    assert response.status_code == 422


async def test_balance_overflow(client, wallet_id):
    big = 9_999_999_999_999
    response = await operate(client, wallet_id, "DEPOSIT", big)
    assert response.status_code == 200

    response = await operate(client, wallet_id, "DEPOSIT", big)
    assert response.status_code == 400

    response = await client.get(f"{API}/{wallet_id}")
    assert response.json()["balance"] == big


async def test_concurrent_deposits(client, wallet_id):
    responses = await asyncio.gather(
        *(operate(client, wallet_id, "DEPOSIT", 10) for _ in range(50))
    )
    assert all(r.status_code == 200 for r in responses)

    response = await client.get(f"{API}/{wallet_id}")
    assert response.json()["balance"] == 500


async def test_concurrent_withdrawals_never_go_negative(client, wallet_id):
    await operate(client, wallet_id, "DEPOSIT", 100)

    responses = await asyncio.gather(
        *(operate(client, wallet_id, "WITHDRAW", 10) for _ in range(30))
    )
    codes = [r.status_code for r in responses]
    assert codes.count(200) == 10
    assert codes.count(409) == 20

    response = await client.get(f"{API}/{wallet_id}")
    assert response.json()["balance"] == 0


async def test_concurrent_mixed_operations(client, wallet_id):
    await operate(client, wallet_id, "DEPOSIT", 1000)

    tasks = []
    for _ in range(20):
        tasks.append(operate(client, wallet_id, "DEPOSIT", 5))
        tasks.append(operate(client, wallet_id, "WITHDRAW", 5))
    responses = await asyncio.gather(*tasks)
    assert all(r.status_code == 200 for r in responses)

    response = await client.get(f"{API}/{wallet_id}")
    assert response.json()["balance"] == 1000
