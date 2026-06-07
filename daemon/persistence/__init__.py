"""
Persistence layer — database models and session management.

Public API:

    from daemon.persistence import (
        # session and lifecycle
        get_session, init_db, close_db, engine,
        # schema
        Base, Deployment, DeploymentStatus, Fill, Bar,
    )
"""

from daemon.persistence.database import (
    close_db,
    engine,
    get_session,
    init_db,
)
from daemon.persistence.models import (
    Base,
    Bar,
    Deployment,
    DeploymentStatus,
    Fill,
)

__all__ = [
    "Base",
    "Bar",
    "Deployment",
    "DeploymentStatus",
    "Fill",
    "close_db",
    "engine",
    "get_session",
    "init_db",
]
