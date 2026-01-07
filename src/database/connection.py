"""
Database connection management
"""
import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base

# Load environment variables
load_dotenv()

# Database URL
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'hf_tracker')

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

# Create engine
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20
        )
        logger.info(f"Database engine created: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    return _engine


def get_session_factory():
    """Get or create session factory"""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get database session with context manager

    Usage:
        with get_session() as session:
            session.query(...)
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def check_connection() -> bool:
    """Check database connection

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connection successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False


def init_db() -> bool:
    """Initialize database - create all tables

    Returns:
        True if successful, False otherwise
    """
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        return False


def drop_all_tables() -> bool:
    """Drop all tables - USE WITH CAUTION!

    Returns:
        True if successful, False otherwise
    """
    try:
        engine = get_engine()
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped!")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to drop database tables: {e}")
        return False


def get_table_stats() -> dict:
    """Get table statistics

    Returns:
        Dictionary with table names and row counts
    """
    stats = {}
    try:
        engine = get_engine()
        with engine.connect() as conn:
            for table in Base.metadata.tables.keys():
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                stats[table] = count
        return stats
    except SQLAlchemyError as e:
        logger.error(f"Failed to get table stats: {e}")
        return {}
