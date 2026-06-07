# daemon/persistence/

The database layer. Owns the schema, the engine, and the session factory.

## What lives here

```
persistence/
├── __init__.py    # public API re-exports
├── database.py    # async engine, session factory, init_db, close_db
├── models.py      # SQLAlchemy ORM models (the schema)
└── README.md      # you are here
```

## Tables

Three tables for v1:

### `deployments`

A row per running bot — the configured, instantiated strategy. The daemon loads all rows with `status='running'` on startup, re-instantiates each strategy with its saved params and state, and resumes trading.

Key fields: `account_id`, `strategy_class` (Python class path), `strategy_name` (human-readable), `symbol`, `timeframe`, `params` (JSON), `state` (JSON), `status` (running / paused / stopped / error), timestamps.

### `fills`

Every order execution. This is the trade journal. Each fill is attributed to the deployment that triggered it via `deployment_id` (or NULL for manual trades from the UI).

Key fields: `account_id`, `deployment_id`, `symbol`, `side`, `quantity`, `price`, `commission`, `ibkr_order_id`, `ibkr_exec_id` (unique, for dedup), `timestamp`, `reason` (from `Signal.reason`).

### `bars`

OHLCV cache. Composite primary key (`symbol`, `timeframe`, `timestamp`) prevents duplicates. Populated as the daemon receives bars from IBKR. Useful for backtesting and analysis later.

## Conventions

- **Money and quantities use `Numeric(18, 8)`** (Decimal in Python). Floats would be simpler but have precision quirks that bite in financial code. Cost is small; correctness is worth it.
- **All timestamps are UTC**. Store UTC, convert to local only at display time.
- **`account_id` is on every transactional row.** Even though one daemon = one account today, this leaves the door open for shared deployments or multi-account scenarios later without a painful migration.
- **Enums are shared with the Strategy base class.** `Side` and `Timeframe` come from `daemon.strategies.base` so the DB and runtime can never drift apart on what a valid value is.

## How to use it

```python
from daemon.persistence import get_session, Deployment, DeploymentStatus

# Read
async with get_session() as session:
    result = await session.execute(
        select(Deployment).where(Deployment.status == DeploymentStatus.RUNNING)
    )
    active = result.scalars().all()

# Write
async with get_session() as session:
    session.add(Deployment(
        account_id="DU1234567",
        strategy_class="daemon.strategies.examples.MaCrossover",
        strategy_name="MA crossover 12/26",
        symbol="SPY",
        timeframe=Timeframe.H4,
        params={"fast": 12, "slow": 26},
    ))
    # auto-commits on context exit
```

## Configuration

The connection string is controlled by the `DATABASE_URL` env var. Default is a local `trading.db` SQLite file. On the VPS we'll point it at a stable path. When we eventually migrate to PostgreSQL + TimescaleDB, the only change is the connection string — the rest of the code is identical.

## Migrations

For the initial schema, `init_db()` creates tables via SQLAlchemy's `create_all`. Once the daemon goes live and the schema is in use, all future changes go through [Alembic](https://alembic.sqlalchemy.org/) migrations (already declared in `pyproject.toml`). Don't change `models.py` and rely on `create_all` after that point — it doesn't migrate existing tables.
