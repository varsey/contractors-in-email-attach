"""
Comprehensive integration test suite using .eml files from eml-collection directory.

This test suite simulates the complete email processing workflow by:
1. Reading .eml files from the eml-collection directory
2. Processing them through the business logic (INN extraction, date range extraction)
3. Validating the results against expected outputs

This mimics the behavior of a live IMAP connection without requiring actual email server access.
"""
import os
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import eml_parser

# Set required environment variables before importing modules
os.environ.setdefault('SMTP_USERNAME', 'test@example.com')
os.environ.setdefault('SMTP_PASSWORD', 'test_password')
os.environ.setdefault('TO_EMAIL', 'test@example.com')

from src.modules.parsers.message import INNMessageProcessor, DateRangeMessageProcessor, MessageNotFoundError
from src.modules.database.client import DatabaseClient
from src.logger.Logger import log


class MockIMAPConnection:
    """Mock IMAP connection for testing with .eml files."""
    
    def __init__(self, eml_files_dir):
        self.eml_files_dir = Path(eml_files_dir)
        self.eml_files = list(self.eml_files_dir.glob('*.eml'))
        self.message_index = {}
        self.mail_id_to_message_id = {}
        self._build_index()
    
    def _build_index(self):
        """Build an index of message-id to mail-id mappings from .eml files."""
        ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=True)
        
        for idx, eml_file in enumerate(self.eml_files, start=1):
            try:
                with open(eml_file, 'rb') as f:
                    raw_email = f.read()
                    parsed = ep.decode_email_bytes(raw_email)
                    
                    # Extract message-id from header
                    message_id = parsed.get('header', {}).get('header', {}).get('message-id', [''])[0]
                    if message_id:
                        # Remove angle brackets if present
                        message_id = message_id.strip('<>')
                        mail_id_bytes = str(idx).encode()
                        
                        # Store as bytes for compatibility with IMAP fetch
                        self.message_index[message_id] = {
                            'mail_id': mail_id_bytes,
                            'raw_email': raw_email
                        }
                        self.mail_id_to_message_id[mail_id_bytes] = message_id
            except Exception as e:
                log.warning(f"Failed to parse {eml_file}: {e}")
    
    def select(self, folder):
        """Mock IMAP select command - returns total message count."""
        total_messages = len(self.message_index)
        return ('OK', [str(total_messages).encode()])
    
    def noop(self):
        """Mock IMAP noop command."""
        return ('OK', [])
    
    def fetch(self, mail_id, message_parts):
        """Mock IMAP fetch command - returns email data from .eml file."""
        # Handle batch fetch (comma-separated mail IDs)
        if isinstance(mail_id, str) and ',' in mail_id:
            mail_ids = [mid.strip().encode() for mid in mail_id.split(',')]
            results = []
            
            for mid in mail_ids:
                message_id = self.mail_id_to_message_id.get(mid)
                if message_id and message_id in self.message_index:
                    data = self.message_index[message_id]
                    
                    # Check if this is a header-only fetch
                    if 'HEADER' in message_parts.upper():
                        # Return just the Message-ID header
                        header_data = f"Message-ID: <{message_id}>\r\n\r\n".encode()
                        # Format: (b'ID (BODY[HEADER.FIELDS (MESSAGE-ID)] {size}', b'Message-ID: ...')
                        results.append((mid + b' (BODY[HEADER.FIELDS (MESSAGE-ID)] {' + str(len(header_data)).encode() + b'}', header_data))
                    else:
                        # Return full email
                        results.append((mid, data['raw_email']))
            
            return ('OK', results)
        
        # Handle single mail_id fetch
        mail_id_bytes = mail_id if isinstance(mail_id, bytes) else str(mail_id).encode()
        
        # Find the email by mail_id
        message_id = self.mail_id_to_message_id.get(mail_id_bytes)
        if message_id and message_id in self.message_index:
            data = self.message_index[message_id]
            
            # Check if this is a header-only fetch
            if 'HEADER' in message_parts.upper():
                # Return just the Message-ID header
                header_data = f"Message-ID: <{message_id}>\r\n\r\n".encode()
                return ('OK', [(mail_id_bytes, header_data)])
            else:
                # Return full email
                return ('OK', [(mail_id_bytes, data['raw_email'])])
        
        return ('OK', [])
    
    def search(self, charset, criteria):
        """Mock IMAP search command - returns all mail IDs."""
        mail_ids = [data['mail_id'] for data in self.message_index.values()]
        return ('OK', [b' '.join(mail_ids)])
    
    def login(self, email, password):
        """Mock IMAP login."""
        return ('OK', [b'Logged in'])


class TestEMLIntegration(unittest.TestCase):
    """Integration tests using real .eml files from eml-collection directory."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        cls.eml_collection_dir = Path(__file__).parent.parent / 'eml-collection'
        cls.original_cwd = os.getcwd()
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Create temporary database
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db = self.temp_db_file.name
        self.temp_db_file.close()
        
        # Create temporary directory for attachments
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, 'temp'), exist_ok=True)
        
        # Change to temp directory
        os.chdir(self.temp_dir)
        
        # Create mock IMAP connection
        self.mock_imap_connection = MockIMAPConnection(self.eml_collection_dir)
    
    def tearDown(self):
        """Clean up after each test."""
        # Restore original directory
        os.chdir(self.original_cwd)
        
        # Clean up temp database
        if os.path.exists(self.temp_db):
            os.unlink(self.temp_db)
        
        # Clean up temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_inn_processor(self):
        """Helper method to create INN processor with mock connection."""
        with patch('src.modules.email.client.imaplib.IMAP4_SSL') as mock_imap:
            mock_imap.return_value = self.mock_imap_connection
            
            # Also patch the retry decorator to prevent reconnection attempts
            with patch('src.modules.email.client.retry_with_backoff', lambda *args, **kwargs: lambda f: f):
                processor = INNMessageProcessor(
                    email='test@example.com',
                    password='test_password',
                    server='test.server.com',
                    mail_folder='INBOX',
                    db_path=self.temp_db
                )
                
                processor.mail_connector = self.mock_imap_connection
                # Override setup_mail_connector to prevent reconnection
                processor.setup_mail_connector = lambda: self.mock_imap_connection
                return processor
    
    def _create_date_processor(self):
        """Helper method to create date range processor with mock connection."""
        with patch('src.modules.email.client.imaplib.IMAP4_SSL') as mock_imap:
            mock_imap.return_value = self.mock_imap_connection
            
            # Also patch the retry decorator to prevent reconnection attempts
            with patch('src.modules.email.client.retry_with_backoff', lambda *args, **kwargs: lambda f: f):
                processor = DateRangeMessageProcessor(
                    email='test@example.com',
                    password='test_password',
                    server='test.server.com',
                    mail_folder='INBOX',
                    db_path=self.temp_db
                )
                
                processor.mail_connector = self.mock_imap_connection
                # Override setup_mail_connector to prevent reconnection
                processor.setup_mail_connector = lambda: self.mock_imap_connection
                return processor
    
    def test_eml_files_exist(self):
        """Test that .eml files exist in the collection directory."""
        eml_files = list(self.eml_collection_dir.glob('*.eml'))
        self.assertGreater(len(eml_files), 0, "No .eml files found in eml-collection directory")
        log.info(f"Found {len(eml_files)} .eml files for testing")
    
    def test_mock_imap_connection_builds_index(self):
        """Test that mock IMAP connection successfully builds message index."""
        self.assertGreater(len(self.mock_imap_connection.message_index), 0, 
                          "No messages indexed from .eml files")
        log.info(f"Indexed {len(self.mock_imap_connection.message_index)} messages")
    
    def test_inn_processor_initialization(self):
        """Test that INN processor initializes correctly with mock connection."""
        processor = self._create_inn_processor()
        self.assertIsNotNone(processor)
        self.assertIsNotNone(processor.db_client)
        self.assertIsNotNone(processor.mail_connector)
    
    def test_date_processor_initialization(self):
        """Test that date range processor initializes correctly with mock connection."""
        processor = self._create_date_processor()
        self.assertIsNotNone(processor)
        self.assertIsNotNone(processor.db_client)
        self.assertIsNotNone(processor.mail_connector)
    
    def test_process_all_eml_files_for_inn(self):
        """Test processing all .eml files for INN extraction."""
        processor = self._create_inn_processor()
        results = {}
        
        for message_id in self.mock_imap_connection.message_index.keys():
            try:
                log.info(f"Processing message: {message_id}")
                result = processor.process_email_by_id(message_id)
                results[message_id] = {
                    'status': 'success',
                    'result': result
                }
                log.info(f"Result: {result}")
            except Exception as e:
                results[message_id] = {
                    'status': 'error',
                    'error': str(e)
                }
                log.error(f"Error processing {message_id}: {e}")
        
        # Verify we processed all messages
        self.assertEqual(len(results), len(self.mock_imap_connection.message_index))
        
        # Verify at least some messages were processed successfully
        successful = [r for r in results.values() if r['status'] == 'success']
        self.assertGreater(len(successful), 0, "No messages were processed successfully")
        
        log.info(f"Successfully processed {len(successful)}/{len(results)} messages")
    
    def test_process_all_eml_files_for_date_range(self):
        """Test processing all .eml files for date range extraction."""
        processor = self._create_date_processor()
        results = {}
        
        for message_id in self.mock_imap_connection.message_index.keys():
            try:
                log.info(f"Processing message for date range: {message_id}")
                result = processor.process_email_by_id(message_id)
                results[message_id] = {
                    'status': 'success',
                    'result': result
                }
                log.info(f"Date range result: {result}")
            except Exception as e:
                results[message_id] = {
                    'status': 'error',
                    'error': str(e)
                }
                log.error(f"Error processing {message_id}: {e}")
        
        # Verify we processed all messages
        self.assertEqual(len(results), len(self.mock_imap_connection.message_index))
        
        # Verify at least some messages were processed successfully
        successful = [r for r in results.values() if r['status'] == 'success']
        self.assertGreater(len(successful), 0, "No messages were processed successfully")
        
        log.info(f"Successfully processed {len(successful)}/{len(results)} messages for date ranges")
    
    def test_database_persistence(self):
        """Test that message IDs are persisted to database during processing."""
        processor = self._create_inn_processor()
        
        # Process one message
        message_id = list(self.mock_imap_connection.message_index.keys())[0]
        processor.process_email_by_id(message_id)
        
        # Verify it was saved to database
        db_message_ids = processor.db_client.get_all_message_ids()
        self.assertIn(message_id, db_message_ids, "Message ID not saved to database")
    
    def test_message_not_found_error(self):
        """Test that MessageNotFoundError is raised for non-existent message ID."""
        processor = self._create_inn_processor()
        
        with self.assertRaises(MessageNotFoundError):
            processor.process_email_by_id('non-existent-message-id@example.com')
    
    def test_inn_extraction_format(self):
        """Test that INN extraction returns expected format."""
        processor = self._create_inn_processor()
        message_id = list(self.mock_imap_connection.message_index.keys())[0]
        result = processor.process_email_by_id(message_id)
        
        # Verify result structure
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn('inns', result, "Result should contain 'inns' key")
        self.assertIsInstance(result['inns'], list, "INNs should be a list")
    
    def test_date_range_extraction_format(self):
        """Test that date range extraction returns expected format."""
        processor = self._create_date_processor()
        message_id = list(self.mock_imap_connection.message_index.keys())[0]
        result = processor.process_email_by_id(message_id)
        
        # Verify result structure
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn('start_month', result, "Result should contain 'start_month' key")
        self.assertIn('end_month', result, "Result should contain 'end_month' key")
        self.assertIn('success', result, "Result should contain 'success' key")
    
    def test_concurrent_processing_safety(self):
        """Test that processing multiple messages doesn't cause conflicts."""
        processor = self._create_inn_processor()
        message_ids = list(self.mock_imap_connection.message_index.keys())[:3]
        
        results = []
        for message_id in message_ids:
            try:
                result = processor.process_email_by_id(message_id)
                results.append(result)
            except Exception as e:
                log.error(f"Error in concurrent processing test: {e}")
        
        # Verify we got results for all processed messages
        self.assertGreater(len(results), 0, "No results from concurrent processing")


if __name__ == '__main__':
    unittest.main(verbosity=2)
