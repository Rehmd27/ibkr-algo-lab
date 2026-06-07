"""
Strategy base class — the contract every trading strategy must follow.

Every strategy in this platform is a Python class that inherits from `Strategy`.
The daemon discovers these classes at startup, registers them, and runs
instances of them as live bots.

To write a new strategy:

    from daemon.strategies.base import Strategy, Bar, Fill, Signal

    class MyStrategy(Strategy):
        name = "My moving average crossover"
        description = "Buys when fast MA crosses above slow MA"
        required_params = {"fast": int, "slow": int}

        async def on_bar(self, bar: Bar) -> list[Signal]:
            # your logic here
            return []

That's the minimum. Optional hooks (on_start, on_stop, on_fill, on_tick) let
you do setup, cleanup, react to fills, or react to sub-bar price ticks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar


# ----------------------------- Data shapes ------------------------------------
# These are what the daemon passes to your strategy, and what your strategy
# returns. They're defined here so every strategy uses the same shapes.


class Side(str, Enum):
    """Buy or sell."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type. Start with MARKET; add LIMIT / STOP later if needed."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class Timeframe(str, Enum):
    """Bar timeframes the platform supports. Add more as needed."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


@dataclass(frozen=True)
class Bar:
    """One OHLCV bar. Frozen so strategies can't accidentally mutate history."""
    symbol: str
    timeframe: Timeframe
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Tick:
    """A single price update. Only delivered to strategies that opt in."""
    symbol: str
    timestamp: datetime
    price: float
    size: float


@dataclass(frozen=True)
class Fill:
    """Notification that an order has been (partially or fully) filled."""
    symbol: str
    side: Side
    quantity: float
    price: float
    timestamp: datetime
    order_id: str
    commission: float = 0.0


@dataclass(frozen=True)
class Position:
    """Current position in a symbol. Zero quantity means flat."""
    symbol: str
    quantity: float
    avg_entry_price: float

    @property
    def is_flat(self) -> bool:
        return self.quantity == 0

    @property
    def is_long(self) -> bool:
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        return self.quantity < 0


@dataclass(frozen=True)
class Signal:
    """
    A trade intent emitted by a strategy.

    The strategy doesn't place orders directly — it returns Signals from
    on_bar / on_tick, and the daemon's order manager translates them into
    actual orders after applying risk checks.
    """
    side: Side
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = None
    stop_price: float | None = None
    reason: str = ""  # human-readable rationale, ends up in the trade journal


# ------------------------------ Strategy --------------------------------------


class Strategy(ABC):
    """
    Base class every strategy must inherit from.

    Class-level attributes (override these in your subclass):
        name             — short, human-readable name (shown in the dashboard)
        description      — one-sentence description of what the strategy does
        required_params  — dict of {param_name: type} the daemon will collect
                           from the user before deploying an instance
        timeframe        — which bar timeframe the strategy operates on
        wants_ticks      — set True if you also need sub-bar tick updates

    Instance attributes (populated by the daemon when instantiating):
        symbol           — the instrument this bot is trading
        params           — the user-supplied config (must match required_params)
        position         — current position in `symbol`, updated by the daemon
        state            — a dict the strategy can use to persist its own data
                           across restarts (the daemon will save and restore it)
    """

    # ---------- Metadata (override in subclasses) ----------
    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    required_params: ClassVar[dict[str, type]] = {}
    timeframe: ClassVar[Timeframe] = Timeframe.D1
    wants_ticks: ClassVar[bool] = False

    # ---------- Runtime state (do not set directly; daemon manages these) ----
    symbol: str
    params: dict[str, Any]
    position: Position
    state: dict[str, Any]

    def __init__(self, symbol: str, params: dict[str, Any]) -> None:
        """
        The daemon instantiates strategies with the symbol and user-supplied
        params. You usually don't need to override __init__; use on_start
        for setup instead.
        """
        self._validate_params(params)
        self.symbol = symbol
        self.params = params
        self.position = Position(symbol=symbol, quantity=0, avg_entry_price=0)
        self.state = {}

    # ---------- Lifecycle hooks (override as needed) ----------

    async def on_start(self) -> None:
        """
        Called once when the bot is deployed or the daemon restarts. Use this
        to load models, warm up indicators with historical bars, etc.
        """
        pass

    async def on_stop(self) -> None:
        """
        Called once when the bot is paused or the daemon shuts down. Use this
        for graceful cleanup (saving state, closing files).
        """
        pass

    @abstractmethod
    async def on_bar(self, bar: Bar) -> list[Signal]:
        """
        Called every time a new bar closes on your configured timeframe.

        This is where the core trading logic lives. Inspect the bar, consult
        self.state, self.position, and self.params, and return zero or more
        Signals describing what you want to do.

        Returning an empty list means "do nothing this bar."
        """
        ...

    async def on_tick(self, tick: Tick) -> list[Signal]:
        """
        Called on every tick if `wants_ticks = True`. Default: ignored.

        Most strategies don't need this. Use it for tight stop management or
        intra-bar entry triggers.
        """
        return []

    async def on_fill(self, fill: Fill) -> None:
        """
        Called when one of your orders fills. The daemon updates `self.position`
        BEFORE calling this, so `self.position` already reflects the new state.

        Use this to record entries, set stop levels in self.state, etc.
        """
        pass

    # ---------- Helpers (use these to express trade intent) ----------

    def buy(self, quantity: float, reason: str = "") -> Signal:
        """Shortcut: emit a market buy signal."""
        return Signal(
            side=Side.BUY,
            quantity=quantity,
            order_type=OrderType.MARKET,
            reason=reason,
        )

    def sell(self, quantity: float, reason: str = "") -> Signal:
        """Shortcut: emit a market sell signal."""
        return Signal(
            side=Side.SELL,
            quantity=quantity,
            order_type=OrderType.MARKET,
            reason=reason,
        )

    def close_position(self, reason: str = "") -> list[Signal]:
        """Shortcut: exit the current position with a market order."""
        if self.position.is_flat:
            return []
        if self.position.is_long:
            return [self.sell(self.position.quantity, reason=reason)]
        return [self.buy(abs(self.position.quantity), reason=reason)]

    # ---------- Internal ----------

    def _validate_params(self, params: dict[str, Any]) -> None:
        """Verify the user-supplied params match the strategy's declared schema."""
        missing = set(self.required_params) - set(params)
        if missing:
            raise ValueError(
                f"{self.__class__.__name__} missing required params: {missing}"
            )
        for key, expected_type in self.required_params.items():
            if not isinstance(params[key], expected_type):
                raise TypeError(
                    f"{self.__class__.__name__} param '{key}' must be "
                    f"{expected_type.__name__}, got {type(params[key]).__name__}"
                )
