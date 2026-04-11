"""
INN Message Processor - extracts INN (tax identification numbers) from emails.

Serves the /api/parsing/ endpoint.
"""
import imaplib
import os
import random

from src.logger.Logger import log
from src.modules.alerter.alerter import send_email_alert
from src.modules.utils.utils import clear_folders
from src.config.cfg import LAST_MESSAGES

from .base import BaseMessageProcessor
from .exceptions import MessageNotFoundError, NetworkError
from .message_id_utils import normalize_message_id


class INNMessageProcessor(BaseMessageProcessor):
    """
    Processor for INN (Taxpayer Identification Number) extraction.
    
    Extracts INN values from email body and attachments.
    Serves the /api/parsing/ endpoint.
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
        Initialize the INNMessageProcessor.
        
        Args:
            email: Email address for IMAP login
            password: Password for IMAP login
            server: IMAP server address
            mail_folder: Mail folder to process
            db_path: Path to SQLite database for message ID storage
        """
        super().__init__(email, password, server, mail_folder, db_path)
    
    @staticmethod
    def org_structure(inns):
        """
        Create organization structure from INN list.
        
        Args:
            inns: List of INN values
            
        Returns:
            Dictionary with 'inn' key containing filtered INN list
        """
        return {
            'inn': [inn if len(inn) in (10, 12) else inn + '*' for inn in inns if len(inn + '*') > 9],
        }
    
    def parse_result(self, attach_texts: dict, message_text: str) -> dict:
        """
        Parse email content and extract INN values.
        
        Alias for parse_attributes for interface compatibility.
        
        Args:
            attach_texts: Dictionary of attachment names to their text content
            message_text: The email body text
            
        Returns:
            Dictionary with organization data including INN values
        """
        return self.parse_attributes(attach_texts, message_text)
    
    def parse_attributes(self, attach_texts: dict, message_text: str) -> dict:
        """
        Parse email attributes and extract INN values from message and attachments.
        
        Args:
            attach_texts: Dictionary of attachment names to their text content
            message_text: The email body text
            
        Returns:
            Dictionary with organization data for each source (message, attachments)
        """
        organization_dict = {}
        inns = []
        for mess_part in [f'инн{x}' for x in self.parsers.clean_text(message_text).split('инн')]:
            inn = self.parsers.parse_inn(mess_part)
            inns.append(inn)
        organization_dict['message'] = self.org_structure(inns)

        for attach_name, full_text in attach_texts.items():
            inns = []
            log.info(f'Processing attachment: {attach_name}')
            card = self.parsers.clean_text(full_text)
            if not card:
                log.info('No card found')

            for card_part in card.lower().split('инн'):
                inn = self.parsers.parse_inn(card_part)
                inns.append(inn)

            org_key = str(attach_name).split('/')[-1]
            organization_dict[org_key] = self.org_structure(inns)

        return organization_dict
    
    def process_email_by_id(self, message_id: str) -> dict:
        """
        Process email by ID and extract INN values.
        
        Args:
            message_id: The message ID to process
            
        Returns:
            Dictionary with 'inns' key containing list of extracted INN values
            
        Raises:
            MessageNotFoundError: If the message ID is not found
            NetworkError: If connection to mail server fails
        """
        message_id = normalize_message_id(message_id)
        log.info(f'Updating message index for message_id: {message_id}')

        if len(message_id) <= 1:
            return {}
        
        try:
            log.info(f'Starting {message_id} parsing')
            message_ids = self.upd_index(message_id)
            orgs_dict = {}
            
            if message_ids.get(message_id, 0) != 0:
                try:
                    data = self.see_msg(self.mail_connector, mail_id=message_ids[message_id])
                    attach_texts, message_text, header_from = self.get_message_attributes(data)
                    organization_candidates = self.parse_attributes(attach_texts, message_text)
                    
                    if (
                        len(organization_candidates.values()) == 1
                        and
                        '*' in str(organization_candidates.values())
                    ):
                        print(header_from)
                    
                    for k, v in organization_candidates.items():
                        log.info(f'\n{k}:\n{v}')
                    orgs_dict.update(organization_candidates)
                except Exception as ex:
                    self.error_processor(ex)
                    log.error('Email processing failed')
                    return {}
            else:
                raise MessageNotFoundError(f"Message-id {message_id} not found in database")
            
            log.info(f'{len(orgs_dict)} - {orgs_dict.__str__()}')
            log.info('Parsing finished\n\n')
            clear_folders([f'{os.getcwd()}/temp/'])
            inns = [x['inn'] for x in orgs_dict.values()]
            return {'inns': list(set([x for xs in inns for x in xs if '*' not in x]))}
        
        except (ConnectionResetError, imaplib.IMAP4.error, OSError) as e:
            log.error(f'Network error while processing message {message_id}: {e}')
            raise NetworkError(f"Failed to connect to mail server: {e}") from e
        except MessageNotFoundError:
            raise
        except Exception as ex:
            self.error_processor(ex)
            log.error(f'Critical error in process_email_by_id: {ex}')
            return {}
    
    def process_random_id(self) -> dict:
        """
        Process a random email from recent messages.
        
        Returns:
            Dictionary with 'mail' key containing the message text
        """
        try:
            message_ids = self.upd_index(None, last_letters=LAST_MESSAGES)
            message_id = random.choice(list(message_ids.keys())[:50])
            
            if message_ids.get(message_id, 0) != 0:
                try:
                    data = self.see_msg(self.mail_connector, mail_id=message_ids[message_id])
                    attach_texts, message_text, _ = self.get_message_attributes(data)
                except Exception as ex:
                    self.error_processor(ex)
                    log.error('Email processing failed')
                    return {}
            
            log.info('Parsing finished\n\n')
            clear_folders([f'{os.getcwd()}/temp/'])

            message_text = message_text if 'уважением' not in message_text.lower() else message_text.split('уважением')[0]

            res = {'mail': message_text.replace('\n', ' ')}
            return res
        except (ConnectionResetError, imaplib.IMAP4.error, OSError) as e:
            log.error(f'Network error in process_random_id: {e}')
            raise NetworkError(f"Failed to connect to mail server: {e}") from e
        except Exception as ex:
            self.error_processor(ex)
            log.error(f'Critical error in process_random_id: {ex}')
            return {}


# Backward compatibility alias
MessageProcessor = INNMessageProcessor
