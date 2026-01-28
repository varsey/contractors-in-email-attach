import sqlite3
from typing import Dict
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
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='message_ids'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                cursor.execute('''
                    CREATE TABLE message_ids (
                        message_id TEXT PRIMARY KEY,
                        mail_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    def save_message_id(self, message_id: str, mail_id: str) -> bool:
        """
        Save a message_id and mail_id pair to the database.
        
        Args:
            message_id: The message ID to save
            mail_id: The mail ID to associate with the message ID
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR IGNORE INTO message_ids (message_id, mail_id) VALUES (?, ?)',
                    (message_id, mail_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            log.error(f'Error saving message_id {message_id}: {e}')
            return False

    def get_message_id(self, message_id: str) -> str | None:
        """
        Retrieve the mail_id associated with a message_id.
        
        Args:
            message_id: The message ID to look up
            
        Returns:
            The mail_id if found, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT mail_id FROM message_ids WHERE message_id = ?',
                    (message_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            log.error(f'Error retrieving message_id {message_id}: {e}')
            return None

    def check_if_exists(self, message_id: str) -> bool:
        """
        Check if a message_id exists in the database.
        
        Args:
            message_id: The message ID to check
            
        Returns:
            True if the message_id exists, False otherwise
        """
        return self.get_message_id(message_id) is not None

    def get_all_message_ids(self) -> Dict[str, str]:
        """
        Retrieve all message_id to mail_id mappings.
        
        Returns:
            Dictionary mapping message_ids to mail_ids
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT message_id, mail_id FROM message_ids')
                results = cursor.fetchall()
                return {message_id: mail_id for message_id, mail_id in results}
        except Exception as e:
            log.error(f'Error retrieving all message_ids: {e}')
            return {}

    def save_multiple_message_ids(self, message_ids: Dict[str, str]) -> int:
        """
        Save multiple message_id and mail_id pairs to the database.
        
        Args:
            message_ids: Dictionary mapping message_ids to mail_ids
            
        Returns:
            Number of records successfully inserted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                data = [(msg_id, mail_id) for msg_id, mail_id in message_ids.items()]
                cursor.executemany(
                    'INSERT OR IGNORE INTO message_ids (message_id, mail_id) VALUES (?, ?)',
                    data
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            log.error(f'Error saving multiple message_ids: {e}')
            return 0
