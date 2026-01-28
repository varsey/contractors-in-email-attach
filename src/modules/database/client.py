import sqlite3
from typing import Optional, Dict
from contextlib import contextmanager

from src.logger.Logger import log


class DatabaseClient:
    def __init__(self, db_path: str = 'message_ids.db'):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the database and create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if table exists and has the source column
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='message_ids'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Check if source column exists
                cursor.execute("PRAGMA table_info(message_ids)")
                columns = [col[1] for col in cursor.fetchall()]
                if 'source' not in columns:
                    # Add source column to existing table
                    cursor.execute("ALTER TABLE message_ids ADD COLUMN source TEXT NOT NULL DEFAULT 'v1'")
                    log.info('Added source column to existing message_ids table')
            else:
                # Create new table with source column and composite primary key
                cursor.execute('''
                    CREATE TABLE message_ids (
                        message_id TEXT NOT NULL,
                        mail_id TEXT NOT NULL,
                        source TEXT NOT NULL DEFAULT 'v1',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (message_id, source)
                    )
                ''')
            conn.commit()
            log.info(f'Database initialized at {self.db_path}')

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def save_message_id(self, message_id: str, mail_id: str, source: str = 'v1') -> bool:
        """
        Save a message_id and mail_id pair to the database.
        
        Args:
            message_id: The message ID to save
            mail_id: The mail ID to associate with the message ID
            source: Source identifier for the processor ('v1' or 'v2')
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR IGNORE INTO message_ids (message_id, mail_id, source) VALUES (?, ?, ?)',
                    (message_id, mail_id, source)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            log.error(f'Error saving message_id {message_id}: {e}')
            return False

    def get_message_id(self, message_id: str, source: Optional[str] = None) -> Optional[str]:
        """
        Retrieve the mail_id associated with a message_id.
        
        Args:
            message_id: The message ID to look up
            source: Source identifier to filter by (if None, returns first match)
            
        Returns:
            The mail_id if found, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if source:
                    cursor.execute(
                        'SELECT mail_id FROM message_ids WHERE message_id = ? AND source = ?',
                        (message_id, source)
                    )
                else:
                    cursor.execute(
                        'SELECT mail_id FROM message_ids WHERE message_id = ?',
                        (message_id,)
                    )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            log.error(f'Error retrieving message_id {message_id}: {e}')
            return None

    def check_if_exists(self, message_id: str, source: Optional[str] = None) -> bool:
        """
        Check if a message_id exists in the database.
        
        Args:
            message_id: The message ID to check
            source: Source identifier to filter by (if None, checks any source)
            
        Returns:
            True if the message_id exists, False otherwise
        """
        return self.get_message_id(message_id, source) is not None

    def get_all_message_ids(self, source: Optional[str] = None) -> Dict[str, str]:
        """
        Retrieve all message_id to mail_id mappings.
        
        Args:
            source: Source identifier to filter by (if None, returns all)
        
        Returns:
            Dictionary mapping message_ids to mail_ids
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if source:
                    cursor.execute(
                        'SELECT message_id, mail_id FROM message_ids WHERE source = ?',
                        (source,)
                    )
                else:
                    cursor.execute('SELECT message_id, mail_id FROM message_ids')
                results = cursor.fetchall()
                return {message_id: mail_id for message_id, mail_id in results}
        except Exception as e:
            log.error(f'Error retrieving all message_ids: {e}')
            return {}

    def save_multiple_message_ids(self, message_ids: Dict[str, str], source: str = 'v1') -> int:
        """
        Save multiple message_id and mail_id pairs to the database.
        
        Args:
            message_ids: Dictionary mapping message_ids to mail_ids
            source: Source identifier for the processor ('v1' or 'v2')
            
        Returns:
            Number of records successfully inserted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                data = [(msg_id, mail_id, source) for msg_id, mail_id in message_ids.items()]
                cursor.executemany(
                    'INSERT OR IGNORE INTO message_ids (message_id, mail_id, source) VALUES (?, ?, ?)',
                    data
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            log.error(f'Error saving multiple message_ids: {e}')
            return 0
