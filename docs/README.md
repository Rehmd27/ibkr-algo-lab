# docs/

Architecture documentation, design decisions, and reference material. Treat this folder as the "why" behind everything in the rest of the repo.

## What lives here

```
docs/
├── architecture.md      # System architecture: components, data flow, deployment topology
├── strategy-interface.md # Strategy contract: how to write one, what the daemon expects
├── decisions/           # Decision log (ADRs) — one file per significant choice
└── diagrams/            # SVG / PNG architecture diagrams
```

## Decision log

Significant architectural choices get a numbered file in `decisions/`:

- `001-ib-async-over-ibapi.md` — why we use `ib_async` instead of the raw `ibapi` package
- `002-vps-over-local-host.md` — why the daemon must run on a VPS, not a developer machine
- `003-sqlite-for-v1.md` — why SQLite is enough for v1 and what triggers a migration
- (more added as decisions get made)

Each ADR is short: context, decision, consequences. The point is so future-you and the team know *why* something is the way it is six months later.

## Diagrams

Architecture diagrams (system topology, strategy lifecycle, data flow) go in `diagrams/`. The two starting diagrams that came out of the planning conversations:

- Trading platform architecture (devs → GitHub → VPS → IBKR)
- Strategy deployment workflow (the 5-step lifecycle)

## Status

Pre-alpha. Content gets written as the system takes shape.
