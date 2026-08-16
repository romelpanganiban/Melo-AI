"""Database connection and session management"""

from sqlalchemy import create_engine, event
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


def init_database() -> None:
    """Initialize database - create all tables"""
    try:
        logger.info(
            "Initializing database",
            extra={"database_url": db_config.get_connection_string()}
        )
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(
            f"Failed to initialize database: {str(e)}",
            extra={"database_url": db_config.get_connection_string()}
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


def DatabaseSession():
    """Context manager for database sessions
    
    Usage:
        with DatabaseSession() as db:
            # Use db, auto commits on success
            pass
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _session_context():
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    
    return _session_context()


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
