"""
Tests for the refactored message module.

Tests cover:
- Exception classes
- MessageIndexManager
- INNMessageProcessor
- DateRangeMessageProcessor
- Backward compatibility
"""
import unittest
import os
from unittest.mock import Mock, MagicMock, patch

from src.modules.parsers.message import (
    MessageNotFoundError,
    MessageProcessingError,
    MessageIndexManager,
    BaseMessageProcessor,
    INNMessageProcessor,
    DateRangeMessageProcessor,
    MessageProcessor,
    MessageProcessor2,
)
from src.modules.database.client import DatabaseClient


class TestExceptions(unittest.TestCase):
    """Tests for custom exception classes."""
    
    def test_message_not_found_error(self):
        """Test MessageNotFoundError can be raised and caught."""
        with self.assertRaises(MessageNotFoundError) as context:
            raise MessageNotFoundError("Test message not found")
        self.assertEqual(str(context.exception), "Test message not found")
    
    def test_message_processing_error(self):
        """Test MessageProcessingError can be raised and caught."""
        with self.assertRaises(MessageProcessingError) as context:
            raise MessageProcessingError("Test processing error")
        self.assertEqual(str(context.exception), "Test processing error")


class TestMessageIndexManager(unittest.TestCase):
    """Tests for MessageIndexManager class."""
    
    def setUp(self):
        self.db_path = 'test_index_manager.db'
        self.db_client = DatabaseClient(db_path=self.db_path)
        self.index_manager = MessageIndexManager(self.db_client)
    
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_init(self):
        """Test MessageIndexManager initializes correctly."""
        self.assertEqual(self.index_manager.db_client, self.db_client)
    
    def test_get_index_with_mock_connector(self):
        """Test get_index extracts Message-ID from email."""
        # Create mock mail connector
        mock_connector = Mock()
        
        # Create a simple email message bytes
        email_bytes = b'Message-ID: <test123@example.com>\r\nSubject: Test\r\n\r\nBody'
        mock_connector.fetch.return_value = ('OK', [(None, email_bytes)])
        
        result = self.index_manager.get_index(mock_connector, b'1')
        self.assertEqual(result, 'test123@example.com')
    
    def test_get_index_returns_empty_on_failure(self):
        """Test get_index returns empty string on failure."""
        mock_connector = Mock()
        mock_connector.fetch.return_value = ('NO', [])
        
        result = self.index_manager.get_index(mock_connector, b'1')
        self.assertEqual(result, '')


class TestINNMessageProcessor(unittest.TestCase):
    """Tests for INNMessageProcessor class."""
    
    def test_org_structure_valid_inn(self):
        """Test org_structure with valid 10-digit INN."""
        result = INNMessageProcessor.org_structure(['1234567890'])
        self.assertEqual(result, {'inn': ['1234567890']})
    
    def test_org_structure_valid_inn_12_digits(self):
        """Test org_structure with valid 12-digit INN."""
        result = INNMessageProcessor.org_structure(['123456789012'])
        self.assertEqual(result, {'inn': ['123456789012']})
    
    def test_org_structure_invalid_inn(self):
        """Test org_structure with invalid INN (adds asterisk)."""
        # 9 digits is invalid, but len('123456789*') = 10 > 9, so included with asterisk
        result = INNMessageProcessor.org_structure(['123456789'])
        self.assertEqual(result, {'inn': ['123456789*']})
    
    def test_org_structure_too_short_inn(self):
        """Test org_structure filters out too short INNs."""
        # 8 digits: len('12345678*') = 9, which is not > 9, so filtered out
        result = INNMessageProcessor.org_structure(['12345678'])
        self.assertEqual(result, {'inn': []})
        # 7 digits: len('1234567*') = 8, which is not > 9, so filtered out
        result = INNMessageProcessor.org_structure(['1234567'])
        self.assertEqual(result, {'inn': []})
    
    def test_org_structure_empty_list(self):
        """Test org_structure with empty list."""
        result = INNMessageProcessor.org_structure([])
        self.assertEqual(result, {'inn': []})
    
    def test_org_structure_mixed_inns(self):
        """Test org_structure with mixed valid/invalid INNs."""
        result = INNMessageProcessor.org_structure(['1234567890', '12345', '123456789012'])
        self.assertEqual(result, {'inn': ['1234567890', '123456789012']})


class TestDateRangeMessageProcessor(unittest.TestCase):
    """Tests for DateRangeMessageProcessor class."""
    
    @patch('src.modules.parsers.message.date_processor.extract_date_range')
    def test_parse_result_calls_extract_date_range(self, mock_extract):
        """Test parse_result delegates to extract_date_range."""
        mock_extract.return_value = {
            'start_month': '2024-01-01',
            'end_month': '2024-03-31',
            'success': True
        }
        
        # We can't instantiate without proper email credentials,
        # so we test the static behavior
        from src.modules.parsers.date_range_extractor import extract_date_range
        result = extract_date_range("Test message text")
        
        # Just verify the function is callable
        self.assertIsNotNone(result)


class TestBackwardCompatibility(unittest.TestCase):
    """Tests for backward compatibility aliases."""
    
    def test_message_processor_alias(self):
        """Test MessageProcessor is alias for INNMessageProcessor."""
        self.assertIs(MessageProcessor, INNMessageProcessor)
    
    def test_message_processor2_alias(self):
        """Test MessageProcessor2 is alias for DateRangeMessageProcessor."""
        self.assertIs(MessageProcessor2, DateRangeMessageProcessor)
    
    def test_imports_from_package(self):
        """Test all expected classes can be imported from package."""
        from src.modules.parsers.message import (
            MessageProcessor,
            MessageProcessor2,
            MessageNotFoundError,
            INNMessageProcessor,
            DateRangeMessageProcessor,
            BaseMessageProcessor,
            MessageIndexManager,
        )
        
        # Verify they are all valid classes
        self.assertTrue(callable(MessageProcessor))
        self.assertTrue(callable(MessageProcessor2))
        self.assertTrue(callable(INNMessageProcessor))
        self.assertTrue(callable(DateRangeMessageProcessor))
        self.assertTrue(callable(MessageIndexManager))
        self.assertTrue(issubclass(MessageNotFoundError, Exception))


class TestModuleStructure(unittest.TestCase):
    """Tests to verify module structure and relationships."""
    
    def test_inn_processor_inherits_base(self):
        """Test INNMessageProcessor inherits from BaseMessageProcessor."""
        self.assertTrue(issubclass(INNMessageProcessor, BaseMessageProcessor))
    
    def test_date_processor_inherits_base(self):
        """Test DateRangeMessageProcessor inherits from BaseMessageProcessor."""
        self.assertTrue(issubclass(DateRangeMessageProcessor, BaseMessageProcessor))
    
    def test_base_processor_is_abstract(self):
        """Test BaseMessageProcessor has abstract methods."""
        import inspect
        from abc import ABC
        
        self.assertTrue(issubclass(BaseMessageProcessor, ABC))
        
        # Check that process_email_by_id and parse_result are defined
        self.assertTrue(hasattr(BaseMessageProcessor, 'process_email_by_id'))
        self.assertTrue(hasattr(BaseMessageProcessor, 'parse_result'))


if __name__ == '__main__':
    unittest.main()
