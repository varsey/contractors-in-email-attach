"""
Message Index Manager - handles message index operations.

Extracted from MessageProcessor to follow Single Responsibility Principle.
"""
import imaplib
from typing import Optional, Dict
from email import message_from_bytes

from src.logger.Logger import log
from src.modules.database.client import DatabaseClient


class MessageIndexManager:
    """
    Manages message ID indexing operations.
    
    Handles:
    - Extracting Message-ID from emails
    - Saving message IDs to database
    - Updating message ID index
    """
    
    def __init__(self, db_client: DatabaseClient, source: str = 'v1'):
        """
        Initialize the MessageIndexManager.
        
        Args:
            db_client: DatabaseClient instance for database operations
            source: Source identifier for this processor ('v1' or 'v2')
        """
        self.db_client = db_client
        self.source = source
    
    def get_index(self, mail_connector: imaplib.IMAP4_SSL, mail_id) -> str:
        """
        Extract Message-ID from an email by mail_id.
        
        Args:
            mail_connector: IMAP connection object
            mail_id: The IMAP mail ID to fetch
            
        Returns:
            The Message-ID string (without angle brackets) or empty string if not found
        """
        idx = ''
        
        try:
            print(f'{mail_id=}')
            full_response = mail_connector.fetch(mail_id, '(BODY.PEEK[])')
            if full_response[0] == 'OK' and full_response[1] and full_response[1][0]:
                msg = message_from_bytes(full_response[1][0][1])
                message_id = msg.get('Message-ID')
                if message_id:
                    idx = message_id.strip().strip('<>')
                    return idx
        except (IndexError, TypeError, AttributeError, Exception) as ex:
            log.warning(f'Failed to extract Message-ID for mail_id {mail_id}: {ex}')
        
        return idx
    
    def dump_messages(self, mail_connector: imaplib.IMAP4_SSL, mail_ids, message_ids: Dict[str, str]) -> Dict[str, str]:
        """
        Save message IDs to SQLite database.

        Args:
            mail_connector: IMAP connection object
            mail_ids: List of mail IDs to process
            message_ids: Dictionary of existing message_id -> mail_id mappings
        
        Returns:
            Updated dictionary of message_id -> mail_id mappings
        """
        log.info('Dumping messages to database, please wait...')
        new_entries = 0
        for num, mail_id in enumerate(mail_ids):
            if mail_id not in message_ids.values():
                try:
                    indx = self.get_index(mail_connector, mail_id)
                    if len(indx) > 0 and indx not in message_ids.keys():
                        if self.db_client.save_message_id(indx, mail_id, source=self.source):
                            message_ids[indx] = mail_id
                            new_entries += 1
                except imaplib.IMAP4.error:
                    log.warning(f'Cannot find email_id at server, skipping')
        log.info(f'Saved {new_entries} new message IDs to database')
        return message_ids
    
    def upd_index(
        self, 
        mail_connector: imaplib.IMAP4_SSL,
        mail_folder: str,
        setup_connector_callback,
        message_id: Optional[str], 
        last_letters: int = 30
    ) -> Dict[str, str]:
        """
        Update message ID index using SQLite database.

        Args:
            mail_connector: IMAP connection object
            mail_folder: Mail folder name
            setup_connector_callback: Callback to setup mail connector
            message_id: The message ID to search for
            last_letters: Number of last emails to check

        Returns:
            Dictionary of message_id -> mail_id mappings
        """
        setup_connector_callback()
        last_indx = int(mail_connector.select(mail_folder)[1][0])
        mail_ids = [str(x).encode() for x in range(last_indx - last_letters, last_indx + 1)]

        # Get all existing message IDs from database for this source
        message_ids = self.db_client.get_all_message_ids(source=self.source)
        print(f'Existing message IDs count: {len(message_ids)}')

        if message_id in message_ids.keys():
            log.info('Message-id found in database')
            return message_ids
        else:
            log.warning('Message-id not found in database, fetching new messages')

        self.dump_messages(mail_connector, mail_ids, message_ids)

        setup_connector_callback()
        last_indx = int(mail_connector.select(mail_folder)[1][0])
        mail_ids = [str(x).encode() for x in range(last_indx - last_letters, last_indx + 1)]

        message_ids = self.db_client.get_all_message_ids(source=self.source)

        if message_id in message_ids.keys():
            log.info('Message-id found in database')
            return message_ids
        else:
            log.warning('Message-id not found in database')

        self.dump_messages(mail_connector, mail_ids, message_ids)

        # Reload message IDs after dump
        message_ids = self.db_client.get_all_message_ids(source=self.source)

        return message_ids
