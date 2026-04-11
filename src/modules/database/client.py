import sqlite3
from typing import Dict
from contextlib import contextmanager

from src.logger.Logger import log
from src.modules.parsers.message.message_id_utils import normalize_message_id


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
            normalized_message_id = normalize_message_id(message_id)
            normalized_mail_id = str(mail_id).strip()
            if not normalized_message_id or not normalized_mail_id:
                return False

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR IGNORE INTO message_ids (message_id, mail_id) VALUES (?, ?)',
                    (normalized_message_id, normalized_mail_id)
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
            normalized_message_id = normalize_message_id(message_id)
            if not normalized_message_id:
                return None

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT mail_id FROM message_ids WHERE message_id = ?',
                    (normalized_message_id,)
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
                return {
                    normalize_message_id(message_id): str(mail_id).strip()
                    for message_id, mail_id in results
                    if normalize_message_id(message_id)
                }
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
            normalized_entries = []
            for msg_id, mail_id in message_ids.items():
                normalized_message_id = normalize_message_id(msg_id)
                normalized_mail_id = str(mail_id).strip()
                if normalized_message_id and normalized_mail_id:
                    normalized_entries.append((normalized_message_id, normalized_mail_id))

            if not normalized_entries:
                return 0

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    'INSERT OR IGNORE INTO message_ids (message_id, mail_id) VALUES (?, ?)',
                    normalized_entries
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            log.error(f'Error saving multiple message_ids: {e}')
            return 0
