daemon/
├── strategies/     # Strategy classes (start here if you're contributing one)
├── ibkr/           # ib_async wrapper, connection management, reconnection logic
├── api/            # FastAPI routes + WebSocket endpoints
├── persistence/    # Database layer (SQLite for v1, abstracted for later migration)
└── runtime/        # Strategy orchestrator — discovers, instantiates, supervises bots
