"""
Date Range Message Processor - extracts date ranges from emails.

Serves the /api/parsing/v2/ endpoint.
"""
import os

from src.logger.Logger import log
from src.modules.parsers.date_range_extractor import extract_date_range
from src.modules.utils.utils import clear_folders

from .base import BaseMessageProcessor
from .exceptions import MessageNotFoundError
from .message_id_utils import normalize_message_id


class DateRangeMessageProcessor(BaseMessageProcessor):
    """
    Processor for date range extraction from emails.
    
    Extracts start and end dates from email body text.
    Serves the /api/parsing/v2/ endpoint.
    """
    
    def __init__(
        self, 
        email: str, 
        password: str, 
        server: str, 
        mail_folder: str, 
        db_path: str = 'message_ids.db'
    ):
        """
        Initialize the DateRangeMessageProcessor.
        
        Args:
            email: Email address for IMAP login
            password: Password for IMAP login
            server: IMAP server address
            mail_folder: Mail folder to process
            db_path: Path to SQLite database for message ID storage
        """
        super().__init__(email, password, server, mail_folder, db_path)
    
    def parse_result(self, attach_texts: dict, message_text: str) -> dict:
        """
        Parse email content and extract date range.
        
        Args:
            attach_texts: Dictionary of attachment names to their text content (unused)
            message_text: The email body text
            
        Returns:
            Dictionary with date range extraction result
        """
        return extract_date_range(message_text)
    
    def process_email_by_id(self, message_id: str) -> dict:
        """
        Process email by ID and extract date range.
        
        Args:
            message_id: The message ID to process

        Returns:
            Dictionary with date range extraction result:
            {
                'start_month': ISO date string or None,
                'end_month': ISO date string or None,
                'success': bool
            }
            
        Raises:
            MessageNotFoundError: If the message ID is not found
        """
        message_id = normalize_message_id(message_id)
        log.info(f'Updating message index for message_id: {message_id}')

        if len(message_id) <= 1:
            return {'start_month': None, 'end_month': None, 'success': False}
        
        try:
            log.info(f'Starting {message_id} parsing (v2)')
            message_ids = self.upd_index(message_id)
            date_range_result = {'start_month': None, 'end_month': None, 'success': False}
            
            if message_ids.get(message_id, 0) != 0:
                try:
                    data = self.see_msg(self.mail_connector, mail_id=message_ids[message_id])
                    attach_texts, message_text, header_from = self.get_message_attributes(data)
                    log.info(f'Message text:\n{message_text}')
                    # Extract date range from message text
                    date_range_result = extract_date_range(message_text)
                    log.info(f'Date range extraction: {date_range_result}')
                except Exception as ex:
                    self.error_processor(ex)
                    log.error('Email processing failed')
                    return {'start_month': None, 'end_month': None, 'success': False}
            else:
                log.warning(f'Message ID {message_id} not found in database')
                raise MessageNotFoundError(f"Message ID {message_id} not found in database")
            
            log.info('Parsing finished (v2)\n\n')
            clear_folders([f'{os.getcwd()}/temp/'])
            return date_range_result
        
        except MessageNotFoundError:
            raise
        except Exception as ex:
            self.error_processor(ex)
            log.error(f'Critical error in process_email_by_id_v2: {ex}')
            return {'start_month': None, 'end_month': None, 'success': False}
    
    # Backward compatibility alias
    def process_email_by_id_v2(self, message_id: str) -> dict:
        """
        Backward compatibility alias for process_email_by_id.
        
        Args:
            message_id: The message ID to process

        Returns:
            Dictionary with date range extraction result
        """
        return self.process_email_by_id(message_id)
    
    def process_all_emails(self) -> list:
        """
        Load all message_ids from database and process each one.

        Returns:
            List of dictionaries with date range extraction results for each message_id
        """
        log.info('Starting batch processing of all emails from database (v2)')
        
        # Load all message_ids from database
        message_ids = self.db_client.get_all_message_ids()
        log.info(f'Found {len(message_ids)} message_ids in database')
        
        results = []
        processed_count = 0
        failed_count = 0
        
        # Process each message_id one by one
        for message_id in message_ids.keys():
            log.info(f'Processing {processed_count + 1}/{len(message_ids)}: {message_id}')
            try:
                result = self.process_email_by_id(message_id)
                results.append({
                    'message_id': message_id,
                    'result': result,
                    'status': 'success'
                })
                processed_count += 1
            except Exception as ex:
                log.error(f'Failed to process message_id {message_id}: {ex}')
                results.append({
                    'message_id': message_id,
                    'result': {'start_month': None, 'end_month': None, 'success': False},
                    'status': 'failed',
                    'error': str(ex)
                })
                failed_count += 1
        
        log.info(f'Batch processing completed: {processed_count} successful, {failed_count} failed')
        return results
    
    # Backward compatibility alias
    def process_all_emails_v2(self) -> list:
        """
        Backward compatibility alias for process_all_emails.

        Returns:
            List of dictionaries with date range extraction results
        """
        return self.process_all_emails()


# Backward compatibility alias
MessageProcessor2 = DateRangeMessageProcessor
