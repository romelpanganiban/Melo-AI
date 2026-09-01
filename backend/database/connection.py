"""Database connection and session management"""

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional
import os
from core.logging import logger
from core.errors import ChatServiceError
from database.models import Base


class DatabaseConfig:
    """Database configuration"""
    
    def __init__(self):
        # Get database URL from environment or use SQLite for development
        self.database_url = os.getenv(
            "DATABASE_URL",
            "sqlite:///./melo_ai.db"  # Local SQLite for development
        )
        
        # For PostgreSQL production, use something like:
        # postgresql+psycopg://postgres:****@localhost:5432/melo_ai
        
        self.echo_sql = os.getenv("DEBUG_SQL", "false").lower() == "true"
    
    def get_connection_string(self) -> str:
        """Get the database connection string"""
        return self.database_url

    def get_safe_connection_string(self) -> str:
        """Return the connection string with its password hidden in logs."""
        return make_url(self.database_url).render_as_string(hide_password=True)


# Database configuration instance
db_config = DatabaseConfig()

# Create engine
engine = create_engine(
    db_config.get_connection_string(),
    echo=db_config.echo_sql,
    connect_args={"check_same_thread": False} if "sqlite" in db_config.database_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
REQUIRED_MIGRATION_REVISION = "0008_revoked_tokens"


def validate_migration_state(database_engine) -> None:
    """Require a PostgreSQL database to be stamped at the application head."""
    inspector = inspect(database_engine)
    if "alembic_version" not in inspector.get_table_names():
        raise ChatServiceError(
            "PostgreSQL schema is not migrated. Run 'alembic upgrade head' before starting Melo-AI."
        )
    with database_engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
    if revision != REQUIRED_MIGRATION_REVISION:
        raise ChatServiceError(
            f"PostgreSQL schema revision {revision!r} is not supported. Run 'alembic upgrade head'."
        )


def init_database() -> None:
    """Validate database readiness without mutating a PostgreSQL schema."""
    try:
        logger.info(
            "Initializing database",
            extra={"database_url": db_config.get_safe_connection_string()}
        )
        if "sqlite" not in db_config.database_url:
            validate_migration_state(engine)
        else:
            Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(
            f"Failed to initialize database: {str(e)}",
            extra={"database_url": db_config.get_safe_connection_string()}
        )
        raise ChatServiceError(f"Database initialization failed: {str(e)}")


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session in FastAPI
    
    Usage:
        @app.get("/example")
        def example_endpoint(db: Session = Depends(get_db)):
            # Use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a database session (for non-FastAPI use)
    
    Usage:
        db = get_db_session()
        try:
            # Use db
            pass
        finally:
            db.close()
    """
    return SessionLocal()


class DatabaseSession:
    """Context manager for database sessions
    
    Usage:
        with DatabaseSession() as db:
            # Use db
            pass
    """
    
    def __init__(self):
        self.db: Optional[Session] = None
    
    def __enter__(self) -> Session:
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            try:
                if exc_type is None:
                    self.db.commit()
                else:
                    self.db.rollback()
            except Exception as e:
                logger.error(f"Error closing database session: {str(e)}")
                self.db.rollback()
            finally:
                self.db.close()


# SQLite-specific optimizations
if "sqlite" in db_config.database_url:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
