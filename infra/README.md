# infra/

Deployment configuration for the VPS. Everything needed to take a fresh Ubuntu droplet and turn it into a running trading host.

## What lives here

```
infra/
├── systemd/        # Service unit files (daemon, gateway watcher, etc.)
├── caddy/          # Caddyfile — HTTPS reverse proxy + auto TLS via Let's Encrypt
├── docker/         # docker-compose.yml for IB Gateway (uses ib-gateway-docker)
└── scripts/        # Provisioning, deploy, and maintenance scripts
```

## Target environment

- DigitalOcean droplet
- Ubuntu 24.04 LTS
- Premium AMD NVMe, 4 GB RAM, 2 vCPU (starting size)
- Region: FRA1 (Frankfurt)

## Deployment model

- **IB Gateway** runs as a Docker container (`ib-gateway-docker`), exposes port 4002 on localhost only
- **Trading daemon** runs as a `systemd` service, connects to Gateway on `localhost:4002`
- **Caddy** runs as a `systemd` service, terminates HTTPS, forwards API traffic to the daemon
- **Frontend** is served as static files by Caddy (built locally, scp'd to the droplet)

## Daily Gateway restart

`ib-gateway-docker` handles the IBKR-mandated daily restart automatically. The daemon's reconnection logic in `daemon/ibkr/` ensures bots come back online once Gateway re-authenticates.

## Status

Pre-alpha. Files will be added as the deploy story matures.
