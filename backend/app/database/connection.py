"""Database connection management and pooling for QueryPilot."""

import logging
from typing import Optional, Tuple
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings

logger = logging.getLogger("querypilot.database")

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker[Session]] = None


def get_engine(database_url: Optional[str] = None, echo: bool = False) -> Engine:
    """Get or initialize the SQLAlchemy Engine.

    Uses settings.database_url if not explicitly provided.
    Enforces pool pre-ping and appropriate timeout settings.
    """
    global _engine, _session_factory
    settings = get_settings()
    url = database_url or settings.database_url

    if _engine is not None and database_url is None:
        return _engine

    connect_args = {}
    timeout_sec = settings.query_timeout_seconds

    # Dialect-specific connection options
    if "postgres" in url:
        # statement_timeout in milliseconds for PostgreSQL
        connect_args["options"] = f"-c statement_timeout={timeout_sec * 1000}"
    elif "sqlite" in url:
        connect_args["timeout"] = timeout_sec

    engine = create_engine(
        url,
        echo=echo,
        pool_pre_ping=True,
        connect_args=connect_args,
    )

    if database_url is None:
        _engine = engine
        _session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    return engine


def get_session(database_url: Optional[str] = None) -> Session:
    """Create a new database session."""
    engine = get_engine(database_url)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return session_factory()


def check_connection(engine: Optional[Engine] = None) -> Tuple[bool, str]:
    """Test connectivity to the database by executing a lightweight ping query.

    Returns:
        Tuple of (is_connected: bool, message: str)
    """
    test_engine = engine or get_engine()
    try:
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                return True, "Database connection healthy"
            return False, "Database responded with unexpected result"
    except Exception as exc:
        sanitized_msg = str(exc).split("\n")[0]
        # Never leak passwords or sensitive tokens in connection check errors
        return False, f"Connection failed: {sanitized_msg}"


def reset_engine() -> None:
    """Reset cached engine and session factory (useful for testing)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _session_factory = None
