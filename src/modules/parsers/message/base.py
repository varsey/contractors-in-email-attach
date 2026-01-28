"""
Base Message Processor - abstract base class for message processors.

Provides common functionality for all message processor implementations.
"""
import os
from abc import ABC, abstractmethod
from typing import Optional

from src.logger.Logger import log
from src.modules.parsers.text import TextParser
from src.modules.parsers.attachment import AttachmentParser
from src.modules.email.client import EmailClient
from src.modules.database.client import DatabaseClient
from src.modules.utils.utils import clear_folders

from .index_manager import MessageIndexManager
from .exceptions import MessageNotFoundError


class BaseMessageProcessor(EmailClient, ABC):
    """
    Abstract base class for message processors.
    
    Provides common functionality:
    - Email client connection
    - Database client for message ID storage
    - Message index management
    - Text parsing utilities
    
    Subclasses must implement:
    - process_email_by_id(): Process email and return result specific to processor type
    - parse_result(): Parse email content and return processor-specific result
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
        Initialize the BaseMessageProcessor.
        
        Args:
            email: Email address for IMAP login
            password: Password for IMAP login
            server: IMAP server address
            mail_folder: Mail folder to process
            db_path: Path to SQLite database for message ID storage
        """
        AttachmentParser.__init__(self)
        EmailClient.__init__(self, email, password, server, mail_folder)
        self.parsers = TextParser()
        self.mail_folder = mail_folder
        
        # Initialize database client for SQL-based message ID storage
        self.db_client = DatabaseClient(db_path=db_path)
        
        # Initialize message index manager
        self.index_manager = MessageIndexManager(self.db_client)
        
        # Initialize mail connector
        self.setup_mail_connector()
        
        log.info(f'{self.__class__.__name__} initialized with database at {db_path}')
    
    def _fetch_email_data(self, message_id: str, last_letters: int = 120):
        """
        Common email fetching logic.
        
        Args:
            message_id: The message ID to fetch
            last_letters: Number of last emails to check in index update
            
        Returns:
            Tuple of (attach_texts, message_text, header_from)
            
        Raises:
            MessageNotFoundError: If the message ID is not found
        """
        message_ids = self.index_manager.upd_index(
            self.mail_connector,
            self.mail_folder,
            self.setup_mail_connector,
            message_id,
            last_letters=last_letters
        )
        
        if message_ids.get(message_id, 0) == 0:
            raise MessageNotFoundError(f"Message-id {message_id} not found in database")
        
        data = self.see_msg(self.mail_connector, mail_id=message_ids[message_id])
        return self.get_message_attributes(data)
    
    def upd_index(self, message_id: Optional[str], last_letters: int = 120):
        """
        Update message ID index - delegates to index_manager.
        
        Provides backward compatibility with existing code.
        
        Args:
            message_id: The message ID to search for
            last_letters: Number of last emails to check

        Returns:
            Dictionary of message_id -> mail_id mappings
        """
        return self.index_manager.upd_index(
            self.mail_connector,
            self.mail_folder,
            self.setup_mail_connector,
            message_id,
            last_letters=last_letters
        )
    
    def get_index(self, mail_id) -> str:
        """
        Extract Message-ID from an email - delegates to index_manager.
        
        Provides backward compatibility with existing code.
        
        Args:
            mail_id: The IMAP mail ID to fetch
            
        Returns:
            The Message-ID string (without angle brackets) or empty string if not found
        """
        return self.index_manager.get_index(self.mail_connector, mail_id)
    
    def dump_messages(self, mail_ids, message_ids):
        """
        Save message IDs to database - delegates to index_manager.
        
        Provides backward compatibility with existing code.
        
        Args:
            mail_ids: List of mail IDs to process
            message_ids: Dictionary of existing message_id -> mail_id mappings
        
        Returns:
            Updated dictionary of message_id -> mail_id mappings
        """
        return self.index_manager.dump_messages(self.mail_connector, mail_ids, message_ids)
    
    @staticmethod
    def _clear_temp_folders():
        """Clear temporary folders after processing."""
        clear_folders([f'{os.getcwd()}/temp/'])
    
    @abstractmethod
    def process_email_by_id(self, message_id: str) -> dict:
        """
        Process email and return result specific to processor type.
        
        Args:
            message_id: The message ID to process
            
        Returns:
            Dictionary with processor-specific result
        """
        pass
    
    @abstractmethod
    def parse_result(self, attach_texts: dict, message_text: str) -> dict:
        """
        Parse email content and return processor-specific result.
        
        Args:
            attach_texts: Dictionary of attachment names to their text content
            message_text: The email body text
            
        Returns:
            Dictionary with parsed result
        """
        pass
