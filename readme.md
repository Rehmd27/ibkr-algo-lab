# ibkr-algo-lab

Custom algorithmic trading platform built on Interactive Brokers. Python strategies, React dashboard, deployed to a Linux VPS that runs 24/7.

## Architecture in one breath

```
[Devs] → GitHub → VPS (IB Gateway + Trading Daemon + SQLite) → IBKR servers
                         ↑
                  [Browser dashboard, HTTPS]
```

- **Trading daemon** — FastAPI + `ib_async`. Runs strategies. Exposes REST and WebSocket API.
- **IB Gateway** — IBKR's required connection client. Runs in Docker. Auto-restarts daily.
- **Dashboard** — React + TypeScript + `lightweight-charts`. Talks to the daemon over HTTPS.
- **Host** — DigitalOcean droplet running Ubuntu 24.04 LTS.

See `docs/architecture.md` for diagrams.

## Repository layout

```
ibkr-algo-lab/
├── daemon/           # Python backend
│   ├── strategies/     # Strategies live here — read strategies/README.md first
│   ├── ibkr/           # IBKR connection layer (ib_async wrapper)
│   ├── api/            # FastAPI routes + WebSocket
│   ├── persistence/    # DB layer (SQLite for now)
│   └── runtime/        # Strategy orchestrator
├── frontend/         # React dashboard
├── infra/            # Deployment configs (systemd, Caddy, Docker)
└── docs/             # Architecture notes, decision log, diagrams
```

## Status

Pre-alpha — scaffolding phase. Building toward an MVP that can:

1. Connect to an IBKR paper account via IB Gateway
2. Run a registered Python strategy on a configured symbol/timeframe
3. Persist state across restarts (in-position survival, deployment configs)
4. Render account, positions, bots, and trade history in the dashboard
5. Deploy to a DigitalOcean VPS as a long-running systemd service

## For strategy contributors

If you're writing a strategy for this platform, read `daemon/strategies/README.md` first. The short version: subclass `Strategy`, implement `on_bar` (and optionally `on_fill`, `on_tick`), declare your params and metadata. The daemon discovers and runs it.

## Stack decisions

- **Python** for backend and strategies — leverages the data science ecosystem
- **`ib_async`** as the IBKR API client (the actively maintained successor to `ib_insync`)
- **FastAPI** for the daemon's REST + WebSocket surface
- **React + TypeScript** for the frontend, with `lightweight-charts` (TradingView's open-source charting library) for the chart page
- **SQLite** for persistence in v1; PostgreSQL + TimescaleDB later if scale demands it
- **Linux VPS (DigitalOcean)** for hosting — IB Gateway must run 24/7 and Windows is a poor host for that

## License

Private. Not licensed for distribution.
