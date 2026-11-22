"""
Database Connection Manager using SQLAlchemy.

Purpose:
  Provides centralized database engine creation and connection lifecycle management.
  Attempts connection to MySQL (smart_energy_dw) using credentials from config.py.
  If MySQL is unreachable (e.g., student running on a machine without MySQL service),
  it seamlessly switches to an embedded SQLite database (data/processed/smart_energy_dw.sqlite)
  and logs a clear notification so the student and teacher can run everything without roadblocks!

Inputs:
  - config.py database configuration
Outputs:
  - SQLAlchemy Engine & Connection objects
  - Active dialect indicator ('mysql' or 'sqlite')

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config

logger = logging.getLogger("DBConnection")


def get_db_engine() -> Tuple[Engine, str]:
    """
    Creates and tests an SQLAlchemy database engine.
    Tries MySQL first. Falls back to SQLite if MySQL is unavailable.

    Returns:
        Tuple[Engine, str]: The active SQLAlchemy engine and dialect name ('mysql' or 'sqlite').
    """
    mysql_url = (
        f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@"
        f"{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    )

    try:
        engine = create_engine(mysql_url, pool_recycle=3600, pool_pre_ping=True)
        # Verify connection with a lightweight ping
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        logger.info("Successfully connected to MySQL database: '%s' on %s:%s",
                    config.DB_NAME, config.DB_HOST, config.DB_PORT)
        return engine, "mysql"
    except Exception as e:
        logger.warning("Could not connect to MySQL (%s). Using high-performance local SQLite fallback.", str(e))
        sqlite_url = f"sqlite:///{config.SQLITE_DB_PATH}"
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        logger.info("Connected to SQLite Data Warehouse at: %s", config.SQLITE_DB_PATH)
        return engine, "sqlite"


def test_connection():
    """Diagnostic function to test and print database health."""
    engine, dialect = get_db_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS status;")).fetchone()
        print(f"[DB STATUS] Engine: {dialect.upper()} | Health check returned: {result[0]}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_connection()

