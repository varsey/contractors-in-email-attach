import os
import json
import random
import shutil
import pickle
import imaplib
from typing import Optional
from email import message_from_bytes

from src.logger.Logger import log
from src.modules.parsers.text import TextParser
from src.modules.parsers.attachment import AttachmentParser
from src.modules.parsers.date_range_extractor import extract_date_range
from src.modules.email.client import EmailClient
from src.modules.alerter.alerter import send_email_alert
from src.modules.minio.client import MinioClient
from src.modules.database.client import DatabaseClient

s3 = MinioClient()



def clear_folders(folder_paths: list):
    for folder_path in folder_paths:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                log.error(f'Failed to delete {file_path}: {e}')
    return None


class MessageProcessor(EmailClient):
    def __init__(self, email: str, password: str, server: str, mail_folder: str, db_path: str = 'message_ids_v1.db'):
        AttachmentParser.__init__(self)
        # TO-DO remove email client from here
        EmailClient.__init__(self, email, password, server, mail_folder)
        self.parsers = TextParser()
        self.mail_folder = mail_folder
        # Initialize database client for SQL-based message ID storage
        self.db_client = DatabaseClient(db_path=db_path)
        log.info(f'MessageProcessor initialized with database at {db_path}')

    @staticmethod
    def org_structure(inns):
        return {
            'inn': [inn if len(inn) in (10, 12) else inn + '*' for inn in inns if len(inn + '*') > 9],
        }


    def parse_attributes(self, attach_texts: dict, message_text: str) -> dict:
        organization_dict = {}
        inns = []
        for mess_part in [f'инн{x}' for x in self.parsers.clean_text(message_text).split('инн')]:
            inn = self.parsers.parse_inn(mess_part)
            inns.append(inn)
        organization_dict['message'] = self.org_structure(inns)

        for attach_name, full_text in attach_texts.items():
            inns = []
            log.info(f'Processing attachment: {attach_name}')
            card = self.parsers.clean_text(full_text)  # full_text att_text
            if not card:
                log.info('No card found')

            for card_part in card.lower().split('инн'):
                inn = self.parsers.parse_inn(card_part)
                inns.append(inn)

            org_key = str(attach_name).split('/')[-1]
            organization_dict[org_key] = self.org_structure(inns)

        return organization_dict


    def process_email_by_id(self, message_id: str) -> dict:
        if len(message_id) <= 1:
            return {}
        else:
            log.info(f'Starting {message_id} parsing')
            # TO-DO move last_letters to settings
            message_ids = self.upd_index(message_id, last_letters=120)
            orgs_dict = {}
            if message_ids.get(message_id, 0) != 0:
            # for message_id in list(message_ids.keys())[:1000]:
                try:
                    data = self.see_msg(self.mail_connector, mail_id=message_ids[message_id])
                    attach_texts, message_text, header_from = self.get_message_attributes(data)
                    organization_candidates = self.parse_attributes(attach_texts, message_text)
                    if (
                        len(organization_candidates.values()) == 1
                        and
                        '*' in str(organization_candidates.values())
                    ):
                        send_email_alert(header_from)
                    for k, v in organization_candidates.items():
                        log.info(f'\n{k}:\n{v}')
                    orgs_dict.update(organization_candidates)
                except Exception as ex:
                    self.error_processor(ex)
                    log.error('Email processing failed')
                    return {}
            log.info(f'{len(orgs_dict)} - {orgs_dict.__str__()}')
            log.info('Parsing finished\n\n')
            clear_folders([f'{os.getcwd()}/temp/'])
            inns = [x['inn'] for x in orgs_dict.values()]
            return {'inns': list(set([x for xs in inns for x in xs if '*' not in x]))}

    def get_index(self, mail_id) -> str:
        """
        Extract Message-ID from an email by mail_id.
        
        tries  fetching the full message and parsing the Message-ID.
        
        Args:
            mail_id: The IMAP mail ID to fetch
            
        Returns:
            The Message-ID string (without angle brackets) or empty string if not found
        """
        idx = ''

        # Use BODY.PEEK[] instead of RFC822 to avoid marking the email as read
        try:
            full_response = self.mail_connector.fetch(mail_id, '(BODY.PEEK[])')
            if full_response[0] == 'OK' and full_response[1] and full_response[1][0]:
                msg = message_from_bytes(full_response[1][0][1])
                message_id = msg.get('Message-ID')
                if message_id:
                    # Strip angle brackets and whitespace
                    idx = message_id.strip().strip('<>')
                    return idx
        except (IndexError, TypeError, AttributeError, Exception) as ex:
            log.warning(f'Failed to extract Message-ID for mail_id {mail_id}: {ex}')
        
        return idx

    def dump_messages(self, mail_ids, message_ids):
        """
        Save message IDs to SQLite database instead of pickle file.

        Args:
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
                    indx = self.get_index(mail_id)
                    if len(indx) > 0 and indx not in message_ids.keys():
                        if self.db_client.save_message_id(indx, mail_id):
                            message_ids[indx] = mail_id
                            new_entries += 1
                except imaplib.IMAP4.error:
                    log.warning(f'Cannot find email_id at server, skipping')
        log.info(f'Saved {new_entries} new message IDs to database')
        return message_ids

    def upd_index(self, message_id: Optional[str], last_letters: int = 30):
        """
        Update message ID index using SQLite database instead of pickle file.

        Args:
            message_id: The message ID to search for
            last_letters: Number of last emails to check

        Returns:
            Dictionary of message_id -> mail_id mappings
        """
        self.setup_mail_connector()
        last_indx = int(self.mail_connector.select(self.mail_folder)[1][0])
        mail_ids = [str(x).encode() for x in range(last_indx - last_letters, last_indx + 1)]

        # Get all existing message IDs from database
        message_ids = self.db_client.get_all_message_ids()
        print(f'Existing message IDs count: {len(message_ids)}')
        print(f'Existing message IDs: {message_ids}')

        if message_id in message_ids.keys():
            log.info('Message-id found in database')
            return message_ids
        else:
            log.warning('Message-id not found in database, fetching new messages')

        # Dump new messages to database
        self.dump_messages(mail_ids, message_ids)
        # Reload message IDs after dump
        message_ids = self.db_client.get_all_message_ids()


        self.setup_mail_connector()
        last_indx = int(self.mail_connector.select(self.mail_folder)[1][0])
        mail_ids = [str(x).encode() for x in range(last_indx - last_letters, last_indx + 1)]

        # Get all existing message IDs from database
        message_ids = self.db_client.get_all_message_ids()

        if message_id in message_ids.keys():
            log.info('Message-id found in database')
            return message_ids
        else:
            log.warning('Message-id not found in database')

        self.dump_messages_v2(mail_ids, message_ids)
        # Reload message IDs after dump
        message_ids = self.db_client.get_all_message_ids()

        return message_ids

    def process_random_id(self) -> dict:
            message_ids = self.upd_index(None, last_letters=50)
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


class MessageProcessor2(MessageProcessor):
    """
    MessageProcessor variant that uses SQLite database for caching instead of pickle files.
    Uses EMAIL2 and PASS2 credentials for a different mailbox.
    """
    def __init__(self, email: str, password: str, server: str, mail_folder: str, db_path: str = 'message_ids.db'):
        super().__init__(email, password, server, mail_folder)
        self.db_client = DatabaseClient(db_path=db_path)
        log.info(f'MessageProcessor2 initialized with database at {db_path}')

    def dump_messages_v2(self, mail_ids, message_ids):
        """
        Save message IDs to SQLite database instead of pickle file.

        Args:
            mail_ids: List of mail IDs to process
            message_ids: Dictionary of existing message_id -> mail_id mappings
        """
        log.info('Dumping messages to database, please wait...')
        new_entries = 0
        log.info('222')
        for num, mail_id in enumerate(mail_ids):
            if mail_id not in message_ids.values():
                try:
                    indx = self.get_index(mail_id)
                    if len(indx) > 0 and indx not in message_ids.keys():
                        if self.db_client.save_message_id(indx, mail_id):
                            message_ids[indx] = mail_id
                            new_entries += 1
                except imaplib.IMAP4.error:
                    log.warning(f'Cant find email_id at server, skipping')
        log.info(f'Saved {new_entries} new message IDs to database')

    def process_email_by_id_v2(self, message_id: str) -> dict:
        """
        Process email by ID using database-based caching and extract date range.

        Args:
            message_id: The message ID to process

        Returns:
            Dictionary with date range extraction result:
            {
                'start_month': ISO date string or None,
                'end_month': ISO date string or None,
                'success': bool
            }
        """
        if len(message_id) <= 1:
            return {'start_month': None, 'end_month': None, 'success': False}
        
        log.info(f'Starting {message_id} parsing (v2)')
        message_ids = self.upd_index(message_id, last_letters=120)
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
        
        log.info('Parsing finished (v2)\n\n')
        clear_folders([f'{os.getcwd()}/temp/'])
        return date_range_result

    def process_all_emails_v2(self) -> list:
        """
        Load all message_ids from database and process each one using process_email_by_id_v2().

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
                result = self.process_email_by_id_v2(message_id)
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
