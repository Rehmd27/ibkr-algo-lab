# daemon/

The Python backend. A long-running process that connects to IB Gateway, runs strategies, persists state, and exposes a REST + WebSocket API for the dashboard.

## What lives here

```
daemon/
├── strategies/     # Strategy classes (start here if you're contributing one)
├── ibkr/           # ib_async wrapper, connection management, reconnection logic
├── api/            # FastAPI routes + WebSocket endpoints
├── persistence/    # Database layer (SQLite for v1, abstracted for later migration)
└── runtime/        # Strategy orchestrator — discovers, instantiates, supervises bots
```

## How it works (high level)

On startup the daemon:

1. Connects to IB Gateway on the configured port (paper or live)
2. Discovers strategy classes in `strategies/`
3. Loads active deployments from the database
4. Hydrates each strategy's state and reconciles with IBKR's actual positions
5. Subscribes to market data for each deployment's instrument and timeframe
6. Begins routing bar/tick/fill events to the appropriate strategies
7. Starts the FastAPI server for the dashboard to connect to

The daemon is designed to run as a `systemd` service on the VPS so it auto-starts on boot and auto-restarts on crash.

## Stack

- Python 3.12
- `ib_async` — IBKR API client
- FastAPI + Uvicorn — REST and WebSocket surface
- SQLite (v1) — persistence
- `asyncio` — concurrency model (matches `ib_async`'s native loop)

## Status

Pre-alpha. Files coming online incrementally.
