"""Watermark manager for tracking incremental data loads."""
from datetime import datetime
from pathlib import Path
from typing import Optional
import sqlite3
import pandas as pd


class WatermarkManager:
    """Manages watermarks for incremental data loading using SQLite."""
    
    def __init__(self, db_path: Path):
        """
        Initialize watermark manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize watermark database tables."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watermarks (
                    source_name TEXT PRIMARY KEY,
                    watermark_value TEXT NOT NULL,
                    watermark_type TEXT NOT NULL DEFAULT 'timestamp',
                    last_updated TIMESTAMP NOT NULL,
                    records_processed INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS load_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    load_start TIMESTAMP NOT NULL,
                    load_end TIMESTAMP,
                    records_processed INTEGER,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    watermark_value TEXT
                )
            """)
            conn.commit()
    
    def _get_connection(self):
        """Get database connection context manager."""
        return sqlite3.connect(str(self.db_path))
    
    def get_watermark(self, source_name: str) -> Optional[str]:
        """
        Get current watermark for a data source.
        
        Args:
            source_name: Name of the data source
            
        Returns:
            Current watermark value or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT watermark_value FROM watermarks WHERE source_name = ?",
                (source_name,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    def update_watermark(
        self,
        source_name: str,
        watermark_value: str,
        records_processed: int = 0,
        metadata: Optional[str] = None
    ) -> None:
        """
        Update watermark for a data source.
        
        Args:
            source_name: Name of the data source
            watermark_value: New watermark value
            records_processed: Number of records processed
            metadata: Optional JSON metadata string
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO watermarks 
                (source_name, watermark_value, watermark_type, last_updated, 
                 records_processed, metadata)
                VALUES (?, ?, 'timestamp', ?, ?, ?)
            """, (
                source_name,
                watermark_value,
                datetime.utcnow().isoformat(),
                records_processed,
                metadata
            ))
            conn.commit()
    
    def start_load(
        self,
        source_name: str,
        watermark_value: Optional[str] = None
    ) -> int:
        """
        Record the start of a load process.
        
        Args:
            source_name: Name of the data source
            watermark_value: Starting watermark value
            
        Returns:
            Load ID for tracking
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO load_history 
                (source_name, load_start, status, watermark_value)
                VALUES (?, ?, 'running', ?)
            """, (
                source_name,
                datetime.utcnow().isoformat(),
                watermark_value
            ))
            conn.commit()
            return cursor.lastrowid
    
    def complete_load(
        self,
        load_id: int,
        records_processed: int,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Record the completion of a load process.
        
        Args:
            load_id: Load ID from start_load
            records_processed: Number of records processed
            success: Whether the load was successful
            error_message: Error message if load failed
        """
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE load_history 
                SET load_end = ?,
                    records_processed = ?,
                    status = ?,
                    error_message = ?
                WHERE id = ?
            """, (
                datetime.utcnow().isoformat(),
                records_processed,
                "success" if success else "failed",
                error_message,
                load_id
            ))
            conn.commit()
    
    def list_watermarks(self) -> pd.DataFrame:
        """
        List all watermarks as a DataFrame.
        
        Returns:
            DataFrame containing all watermarks
        """
        with self._get_connection() as conn:
            return pd.read_sql_query(
                "SELECT * FROM watermarks ORDER BY last_updated DESC",
                conn
            )
    
    def get_load_history(
        self,
        source_name: Optional[str] = None,
        limit: int = 10
    ) -> pd.DataFrame:
        """
        Get load history.
        
        Args:
            source_name: Optional source name filter
            limit: Maximum number of records to return
            
        Returns:
            DataFrame containing load history
        """
        with self._get_connection() as conn:
            if source_name:
                query = """
                    SELECT * FROM load_history 
                    WHERE source_name = ?
                    ORDER BY load_start DESC 
                    LIMIT ?
                """
                return pd.read_sql_query(query, conn, params=(source_name, limit))
            else:
                query = """
                    SELECT * FROM load_history 
                    ORDER BY load_start DESC 
                    LIMIT ?
                """
                return pd.read_sql_query(query, conn, params=(limit,))
