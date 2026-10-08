# Wallet API

REST API для работы с кошельками: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Alembic.

## Запуск

```bash
docker compose up --build
```

Одна команда поднимает PostgreSQL, применяет миграции (`alembic upgrade head`)
и запускает приложение на http://localhost:8000. Swagger: http://localhost:8000/docs

Настройки БД лежат в `.env` (шаблон — `.env.example`).

## Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/v1/wallets` | Создать кошелёк (баланс 0) |
| POST | `/api/v1/wallets/{uuid}/operation` | `DEPOSIT` / `WITHDRAW` |
| GET | `/api/v1/wallets/{uuid}` | Текущий баланс |

```bash
curl -X POST localhost:8000/api/v1/wallets
curl -X POST localhost:8000/api/v1/wallets/<UUID>/operation \
  -H 'Content-Type: application/json' \
  -d '{"operation_type": "DEPOSIT", "amount": 1000}'
curl localhost:8000/api/v1/wallets/<UUID>
```

Коды ответов: `200` успех, `201` кошелёк создан, `404` кошелёк не найден,
`409` недостаточно средств, `400` переполнение баланса, `422` невалидный запрос
(неверный UUID, `amount <= 0`, неизвестный `operation_type`, больше 2 знаков после запятой).

## Конкурентность

Баланс меняется одним атомарным SQL-запросом без цикла «прочитать → посчитать → записать»:

```sql
UPDATE wallets SET balance = balance - :amount
WHERE id = :id AND balance >= :amount
RETURNING balance
```

PostgreSQL блокирует строку на время `UPDATE`, а конкурирующие транзакции после
ожидания перепроверяют условие `WHERE` по актуальной версии строки. Поэтому
пополнения не теряются, а баланс не уходит в минус. Дополнительная защита —
`CHECK (balance >= 0)` на уровне БД. Деньги хранятся в `NUMERIC(15, 2)`, не во float.

## Тесты

```bash
docker compose --profile test run --rm tests
```

Тесты идут в отдельной БД `wallet_test` и включают проверки параллельных
пополнений, списаний и смешанных операций над одним кошельком.

Локально (нужен запущенный PostgreSQL, переменные `POSTGRES_*`):

```bash
pip install -r requirements-dev.txt
pytest
flake8
```

## Структура

```
app/            config, database, models, schemas, services, api/
migrations/     Alembic (async env + 0001_create_wallets)
tests/          pytest + httpx
```
