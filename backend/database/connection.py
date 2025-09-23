import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Import from centralized config
from backend.config import DATABASE_URL

# Create SQLAlchemy engine with production-ready settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
    pool_size=5,         # Number of connections to maintain
    max_overflow=10,     # Additional connections if needed
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    # SSL mode for production databases (Supabase, AWS RDS, etc.)
    connect_args={
        "sslmode": "prefer",  # Use SSL if available, fallback to non-SSL
        "connect_timeout": 30  # 30 second connection timeout
    } if not DATABASE_URL.startswith("postgresql://postgres:postgres@postgres:") else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Test database connection and return status"""
    try:
        # Test the connection
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        return True, "Database connection successful"
    except SQLAlchemyError as e:
        return False, f"Database connection failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error during connection test: {str(e)}"

def init_db():
    """Initialize database tables"""
    # Test connection first
    connected, message = test_connection()
    if not connected:
        raise ConnectionError(f"Cannot initialize database: {message}")
    
    # Import all models here to ensure they are registered with SQLAlchemy
    from backend.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables initialized successfully") 