# frontend/

The React dashboard. Talks to the daemon's API over HTTPS to render account info, positions, running bots, charts, and trade history.

## Pages (planned)

1. **Dashboard** — account KPIs, open positions (with bot attribution), equity curve, active strategies
2. **Bots** — manage running and idle strategies, deploy new instances, view per-bot performance
3. **Charts** — TradingView-lite charting with bot trade markers overlaid, optional manual order entry
4. **History** — trade journal with full bot attribution and per-strategy filtering
5. **Builder** *(future)* — visual strategy composition

## Stack

- React 18 + TypeScript
- Vite — dev server and build tool
- `lightweight-charts` — TradingView's open-source charting library, for the charts page
- Tailwind CSS — utility styling
- shadcn/ui (or similar) — base component primitives
- React Query (TanStack Query) — server-state caching, polling, WebSocket integration

## Talking to the daemon

The frontend points at the daemon's base URL (configurable via env). In development that's `http://localhost:8000`; in production it's the VPS via HTTPS (`https://yourdomain.com/api`). REST for one-shot reads, WebSocket for live bars, fills, and bot state.

## Design language

Dark theme, density-first ("Command Center" template from the design phase). Theme tokens live in `frontend/src/styles/theme.ts` and mirror the palette from the original Alpaca dashboard work.

## Status

Pre-alpha. Will be scaffolded after the daemon's basic API surface is online.
