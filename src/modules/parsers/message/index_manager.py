import imaplib
import time
from typing import Optional, Dict, List

from src.logger.Logger import log
from src.modules.database.client import DatabaseClient
from src.config.cfg import LAST_MESSAGES
from .message_id_utils import normalize_message_id, extract_normalized_message_id


class MessageIndexManager:
    """
    Manages message ID indexing operations.
    
    Handles:
    - Extracting Message-ID from emails
    - Saving message IDs to database
    - Updating message ID index
    """
    
    def __init__(self, db_client: DatabaseClient):
        """
        Initialize the MessageIndexManager.
        
        Args:
            db_client: DatabaseClient instance for database operations
        """
        self.db_client = db_client
    
    @staticmethod
    def is_connection_alive(mail_connector) -> bool:
        """Check if IMAP connection is still alive without changing state."""
        try:
            status, _ = mail_connector.noop()
            return status == 'OK'
        except:
            return False
    
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
            # Fetch only the Message-ID header instead of the entire email for better performance
            response = mail_connector.fetch(mail_id, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
            if response[0] == 'OK' and response[1] and response[1][0]:
                header_data = response[1][0][1]
                if isinstance(header_data, bytes):
                    header_data = header_data.decode('utf-8', errors='ignore')
                idx = extract_normalized_message_id(header_data)
        except (IndexError, TypeError, AttributeError, Exception) as ex:
            log.warning(f'Failed to extract Message-ID for mail_id {mail_id}: {ex}')
        
        return idx
    
    def get_index_batch(self, mail_connector: imaplib.IMAP4_SSL, mail_ids: List[bytes]) -> Dict[str, str]:
        """
        Extract Message-IDs from multiple emails in a single IMAP command (batch fetching).
        
        This is more efficient than calling get_index() for each mail_id individually,
        as it reduces IMAP round-trips.
        
        Args:
            mail_connector: IMAP connection object
            mail_ids: List of IMAP mail IDs to fetch (as bytes)
            
        Returns:
            Dictionary mapping mail_id (as string) to Message-ID string
        """
        result = {}
        
        if not mail_ids:
            return result
        
        try:
            # Build comma-separated list of mail IDs for batch fetch
            mail_ids_str = ','.join([mid.decode() if isinstance(mid, bytes) else str(mid) for mid in mail_ids])
            print(f'{mail_ids_str=}')
            print(f'{mail_ids_str=}')
            # Fetch Message-ID headers for all messages in a single IMAP command
            response = mail_connector.fetch(mail_ids_str, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
            
            if response[0] != 'OK':
                log.warning(f'Batch fetch failed with status: {response[0]}')
                return result
            
            # Parse batch response - it contains tuples for each message
            current_mail_id = None
            for item in response[1]:
                if item is None:
                    continue
                    
                if isinstance(item, tuple):
                    # First element contains the mail ID info, second contains the header data
                    # Format: (b'123 (BODY[HEADER.FIELDS (MESSAGE-ID)] {XX}', b'Message-ID: <...>\r\n')
                    if len(item) >= 2:
                        # Extract mail_id from the first part
                        first_part = item[0]
                        if isinstance(first_part, bytes):
                            first_part = first_part.decode('utf-8', errors='ignore')
                        # Parse mail_id from format like "123 (BODY..."
                        mail_id_part = first_part.split()[0] if first_part else None
                        
                        # Extract Message-ID from header data
                        header_data = item[1]
                        if isinstance(header_data, bytes):
                            header_data = header_data.decode('utf-8', errors='ignore')
                        
                        message_id = extract_normalized_message_id(header_data)
                        
                        if mail_id_part and message_id:
                            result[mail_id_part] = message_id
                            
        except (IndexError, TypeError, AttributeError, Exception) as ex:
            log.warning(f'Batch fetch failed: {ex}')
        
        return result
    
    def dump_messages(
        self, 
        mail_connector: imaplib.IMAP4_SSL, 
        mail_ids, 
        message_ids: Dict[str, str], 
        batch_size: int = None,
        setup_connector_callback = None,
        max_retries: int = 2
    ) -> Dict[str, str]:
        """
        Save message IDs to SQLite database using batch fetching for better performance.

        Args:
            mail_connector: IMAP connection object
            mail_ids: List of mail IDs to process
            message_ids: Dictionary of existing message_id -> mail_id mappings
            batch_size: Number of messages to fetch per IMAP command (default: 1/5 of total mail_ids)
            setup_connector_callback: Callback to reinitialize connection if needed
            max_retries: Maximum retry attempts for failed batch operations
        
        Returns:
            Updated dictionary of message_id -> mail_id mappings
        """
        log.info('Dumping messages to database, please wait...')
        
        # Filter out mail_ids that are already in the provided mapping snapshot
        existing_mail_ids = set(message_ids.values())
        print(f'{mail_ids=}')
        mail_ids_to_fetch = [
            mid
            for mid in mail_ids
            if (mid.decode() if isinstance(mid, bytes) else str(mid)) not in existing_mail_ids
        ]
        
        if not mail_ids_to_fetch:
            log.info('No new messages to fetch')
            return message_ids
        
        # Calculate batch_size if not provided (default: 1/5 of total mail_ids, minimum 1)
        if batch_size is None:
            batch_size = max(1, len(mail_ids_to_fetch) // 10)
        
        total_saved = 0
        
        # Process mail_ids in batches
        for i in range(0, len(mail_ids_to_fetch), batch_size):
            batch = mail_ids_to_fetch[i:i + batch_size]
            
            for attempt in range(max_retries):
                try:
                    # Validate connection before operation
                    if not self.is_connection_alive(mail_connector):
                        log.warning('Connection not alive, attempting to reconnect')
                        if setup_connector_callback:
                            mail_connector = setup_connector_callback()
                        else:
                            raise imaplib.IMAP4.error("Connection lost and no callback provided")
                    
                    # Batch fetch Message-IDs for current batch
                    batch_results = self.get_index_batch(mail_connector, batch)
                    
                    # Prepare new entries for batch save
                    new_entries = {}
                    for mail_id_str, msg_id in batch_results.items():
                        print(mail_id_str, msg_id)
                        normalized_msg_id = normalize_message_id(msg_id)
                        if normalized_msg_id and normalized_msg_id not in message_ids:
                            new_entries[normalized_msg_id] = str(mail_id_str)
                    
                    # Batch save to database
                    if new_entries:
                        saved_count = self.db_client.save_multiple_message_ids(new_entries)
                        message_ids.update(new_entries)
                        total_saved += saved_count
                    
                    break  # Success, exit retry loop
                    
                except (imaplib.IMAP4.error, ConnectionResetError, OSError) as ex:
                    if attempt == max_retries - 1:
                        log.error(f'Batch fetch failed after {max_retries} attempts: {ex}')
                        # Try to reinitialize connection for next batch if callback provided
                        if setup_connector_callback:
                            try:
                                mail_connector = setup_connector_callback()
                            except Exception as reconnect_ex:
                                log.error(f'Failed to reconnect: {reconnect_ex}')
                    else:
                        log.warning(f'Batch fetch failed (attempt {attempt + 1}), retrying: {ex}')
                        time.sleep(2 ** attempt)  # Exponential backoff
                        # Try to reconnect before next attempt
                        if setup_connector_callback:
                            try:
                                mail_connector = setup_connector_callback()
                            except Exception as reconnect_ex:
                                log.warning(f'Reconnect attempt failed: {reconnect_ex}')
                except Exception as ex:
                    log.warning(f'Error during batch message dump: {ex}')
                    break  # Non-retryable error
        
        if total_saved > 0:
            log.info(f'Saved {total_saved} new message IDs to database')
        else:
            log.info('No new unique message IDs to save')
        
        return message_ids
    
    def upd_index(
        self, 
        mail_connector: imaplib.IMAP4_SSL,
        mail_folder: str,
        setup_connector_callback,
        message_id: Optional[str], 
        last_letters: int = LAST_MESSAGES
    ) -> Dict[str, str]:
        """
        Update message ID index using SQLite database.

        Args:
            mail_connector: IMAP connection object
            mail_folder: Mail folder name
            setup_connector_callback: Callback to setup mail connector
            message_id: The message ID to search for
            last_letters: Number of last emails to check (capped to available messages)

        Returns:
            Dictionary of message_id -> mail_id mappings
        """
        normalized_message_id = normalize_message_id(message_id)
        if normalized_message_id and self.db_client.check_if_exists(normalized_message_id):
            log.info('Message-id found in database')
            return self.db_client.get_all_message_ids()

        if normalized_message_id:
            log.warning('Message-id not found in database, fetching new messages')

        # Use the connection returned by callback to ensure we have a fresh connection
        mail_connector = setup_connector_callback()
        last_indx = int(mail_connector.select(mail_folder)[1][0])
        last_letters = min(last_letters, last_indx)
        mail_ids = [str(x).encode() for x in range(max(1, last_indx - last_letters), last_indx + 1)]
        batch_size = last_letters

        message_ids = self.db_client.get_message_ids_by_mail_ids(mail_ids)
        print(f'{message_ids=}')

        if normalized_message_id and normalized_message_id in message_ids:
            log.info('Message-id found in database')
            return message_ids
        if normalized_message_id:
            log.warning('Message-id not found in database')

        self.dump_messages(
            mail_connector, mail_ids, message_ids, batch_size=batch_size,
            setup_connector_callback=setup_connector_callback
        )
        refreshed_message_ids = self.db_client.get_message_ids_by_mail_ids(mail_ids)

        if normalized_message_id and normalized_message_id not in refreshed_message_ids:
            log.warning('Message-id not found in indexed window after refresh')

        return refreshed_message_ids
