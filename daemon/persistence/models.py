"""
SQLAlchemy ORM models — the database schema.

Three tables for v1:

- Deployment: a configured, running strategy instance ("a bot")
- Fill: every order execution, attributed to its deployment (or marked manual)
- Bar: historical OHLCV cache, composite PK prevents duplicates

Conventions:
- All monetary / quantity values use Numeric(18, 8) — Decimal in Python, not float
- All timestamps are UTC datetimes (be sure to store UTC, not local)
- account_id is a string on every row — supports multi-account scenarios
- Enums (Side, Timeframe) are shared with the Strategy base class
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    JSON,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from daemon.strategies.base import Side, Timeframe


class Base(DeclarativeBase):
    """Shared declarative base for every ORM model."""
    pass


# ----------------------------- Enums ------------------------------------------


class DeploymentStatus(str, Enum):
    """Lifecycle state of a deployment."""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


# ----------------------------- Models -----------------------------------------


class Deployment(Base):
    """
    A configured, instantiated strategy bot.

    One row per "deployed bot." When the daemon restarts, it loads all rows
    where status='running', re-instantiates each strategy with its saved
    params and state, and resumes trading.
    """

    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[str] = mapped_column(String(32), index=True)

    # Python class path of the strategy, e.g. "daemon.strategies.examples.MaCrossover"
    # The daemon uses this to look up the class at startup.
    strategy_class: Mapped[str] = mapped_column(String(256))

    # Human-readable name pulled from Strategy.name at deploy time.
    # Denormalized here for fast dashboard queries.
    strategy_name: Mapped[str] = mapped_column(String(128))

    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[Timeframe] = mapped_column(SqlEnum(Timeframe))

    # User-supplied configuration (e.g. {"fast": 12, "slow": 26}).
    params: Mapped[dict] = mapped_column(JSON)

    # The strategy's self.state dict — survives restarts.
    state: Mapped[dict] = mapped_column(JSON, default=dict)

    status: Mapped[DeploymentStatus] = mapped_column(
        SqlEnum(DeploymentStatus),
        default=DeploymentStatus.RUNNING,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # All fills triggered by this deployment.
    fills: Mapped[list[Fill]] = relationship(back_populates="deployment")

    def __repr__(self) -> str:
        return (
            f"<Deployment id={self.id} {self.strategy_name} "
            f"{self.symbol}/{self.timeframe.value} status={self.status.value}>"
        )


class Fill(Base):
    """
    A single order execution.

    This is the trade journal. Every fill is recorded here, attributed to the
    deployment that triggered it (or NULL for manual trades from the UI).
    """

    __tablename__ = "fills"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[str] = mapped_column(String(32), index=True)

    # The deployment that triggered this fill. NULL for manual trades.
    deployment_id: Mapped[int | None] = mapped_column(
        ForeignKey("deployments.id"),
        nullable=True,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[Side] = mapped_column(SqlEnum(Side))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    commission: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=0)

    # IBKR identifiers. exec_id is unique per execution — used to dedupe if
    # we receive duplicate notifications during reconnection.
    ibkr_order_id: Mapped[str] = mapped_column(String(64), index=True)
    ibkr_exec_id: Mapped[str] = mapped_column(String(64), unique=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)

    # Why the strategy did this — copied from Signal.reason at order time.
    # Invaluable when debugging "why on earth did my bot take that trade."
    reason: Mapped[str] = mapped_column(Text, default="")

    deployment: Mapped[Deployment | None] = relationship(back_populates="fills")

    def __repr__(self) -> str:
        return (
            f"<Fill {self.side.value} {self.quantity} {self.symbol} "
            f"@ {self.price} at {self.timestamp.isoformat()}>"
        )


class Bar(Base):
    """
    Historical OHLCV bar.

    Composite primary key (symbol, timeframe, timestamp) prevents duplicate
    inserts. The daemon caches bars here as it receives them so the analysis
    desk and backtester have a local data store to work against.
    """

    __tablename__ = "bars"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    timeframe: Mapped[Timeframe] = mapped_column(
        SqlEnum(Timeframe), primary_key=True,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)

    open: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    high: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    low: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    close: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    volume: Mapped[Decimal] = mapped_column(Numeric(18, 8))

    def __repr__(self) -> str:
        return (
            f"<Bar {self.symbol} {self.timeframe.value} "
            f"{self.timestamp.isoformat()} close={self.close}>"
        )
