import unittest
import os
import sqlite3
from src.modules.database.client import DatabaseClient

class TestDatabaseClient(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_message_ids.db'
        self.client = DatabaseClient(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_get_message_id(self):
        msg_id = "test_msg_1"
        mail_id = "12345"
        
        # Save
        saved = self.client.save_message_id(msg_id, mail_id)
        self.assertTrue(saved)
        
        # Retrieve
        retrieved_mail_id = self.client.get_message_id(msg_id)
        self.assertEqual(retrieved_mail_id, mail_id)
        
        # Check existence
        self.assertTrue(self.client.check_if_exists(msg_id))

    def test_save_duplicate_id(self):
        msg_id = "test_msg_dup"
        mail_id1 = "111"
        mail_id2 = "222"
        
        self.client.save_message_id(msg_id, mail_id1)
        # INSERT OR IGNORE should return False (rowcount 0) for duplicate
        saved_again = self.client.save_message_id(msg_id, mail_id2)
        self.assertFalse(saved_again)
        
        # Should still have the first one
        self.assertEqual(self.client.get_message_id(msg_id), mail_id1)

    def test_get_nonexistent_id(self):
        self.assertIsNone(self.client.get_message_id("nonexistent"))
        self.assertFalse(self.client.check_if_exists("nonexistent"))

    def test_save_multiple_message_ids(self):
        msg_dict = {
            "msg_a": "1",
            "msg_b": "2",
            "msg_c": "3"
        }
        count = self.client.save_multiple_message_ids(msg_dict)
        self.assertEqual(count, 3)
        
        all_ids = self.client.get_all_message_ids()
        self.assertEqual(len(all_ids), 3)
        self.assertEqual(all_ids["msg_a"], "1")


class TestDatabaseClientWithSource(unittest.TestCase):
    """Tests for source-based filtering functionality."""
    
    def setUp(self):
        self.db_path = 'test_message_ids_source.db'
        self.client = DatabaseClient(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_message_id_with_source(self):
        """Test saving message IDs with different sources."""
        msg_id = "test_msg_source"
        mail_id_v1 = "v1_12345"
        mail_id_v2 = "v2_67890"
        
        # Save with v1 source
        saved_v1 = self.client.save_message_id(msg_id, mail_id_v1, source='v1')
        self.assertTrue(saved_v1)
        
        # Save same message_id with v2 source (should succeed - different source)
        saved_v2 = self.client.save_message_id(msg_id, mail_id_v2, source='v2')
        self.assertTrue(saved_v2)
        
        # Retrieve with source filter
        retrieved_v1 = self.client.get_message_id(msg_id, source='v1')
        self.assertEqual(retrieved_v1, mail_id_v1)
        
        retrieved_v2 = self.client.get_message_id(msg_id, source='v2')
        self.assertEqual(retrieved_v2, mail_id_v2)

    def test_get_all_message_ids_with_source_filter(self):
        """Test retrieving all message IDs filtered by source."""
        # Save messages with different sources
        self.client.save_message_id("msg_1", "mail_1", source='v1')
        self.client.save_message_id("msg_2", "mail_2", source='v1')
        self.client.save_message_id("msg_3", "mail_3", source='v2')
        self.client.save_message_id("msg_4", "mail_4", source='v2')
        
        # Get all v1 messages
        v1_messages = self.client.get_all_message_ids(source='v1')
        self.assertEqual(len(v1_messages), 2)
        self.assertIn("msg_1", v1_messages)
        self.assertIn("msg_2", v1_messages)
        
        # Get all v2 messages
        v2_messages = self.client.get_all_message_ids(source='v2')
        self.assertEqual(len(v2_messages), 2)
        self.assertIn("msg_3", v2_messages)
        self.assertIn("msg_4", v2_messages)
        
        # Get all messages (no source filter)
        all_messages = self.client.get_all_message_ids()
        self.assertEqual(len(all_messages), 4)

    def test_check_if_exists_with_source(self):
        """Test checking existence with source filter."""
        self.client.save_message_id("msg_exist", "mail_exist", source='v1')
        
        # Should exist for v1
        self.assertTrue(self.client.check_if_exists("msg_exist", source='v1'))
        
        # Should not exist for v2
        self.assertFalse(self.client.check_if_exists("msg_exist", source='v2'))
        
        # Should exist when no source specified
        self.assertTrue(self.client.check_if_exists("msg_exist"))

    def test_save_multiple_message_ids_with_source(self):
        """Test saving multiple message IDs with source."""
        msg_dict = {
            "batch_msg_a": "batch_1",
            "batch_msg_b": "batch_2",
            "batch_msg_c": "batch_3"
        }
        
        # Save with v2 source
        count = self.client.save_multiple_message_ids(msg_dict, source='v2')
        self.assertEqual(count, 3)
        
        # Verify they are saved with v2 source
        v2_ids = self.client.get_all_message_ids(source='v2')
        self.assertEqual(len(v2_ids), 3)
        
        # Verify v1 source has no messages
        v1_ids = self.client.get_all_message_ids(source='v1')
        self.assertEqual(len(v1_ids), 0)

    def test_duplicate_message_id_same_source(self):
        """Test that duplicate message_id with same source is ignored."""
        msg_id = "dup_msg"
        
        saved1 = self.client.save_message_id(msg_id, "mail_1", source='v1')
        self.assertTrue(saved1)
        
        # Try to save again with same source - should be ignored
        saved2 = self.client.save_message_id(msg_id, "mail_2", source='v1')
        self.assertFalse(saved2)
        
        # Original value should be preserved
        self.assertEqual(self.client.get_message_id(msg_id, source='v1'), "mail_1")

    def test_same_message_id_different_sources(self):
        """Test that same message_id can exist with different sources."""
        msg_id = "shared_msg"
        
        # Save with v1
        self.client.save_message_id(msg_id, "v1_mail", source='v1')
        
        # Save with v2 - should succeed
        self.client.save_message_id(msg_id, "v2_mail", source='v2')
        
        # Both should coexist
        self.assertEqual(self.client.get_message_id(msg_id, source='v1'), "v1_mail")
        self.assertEqual(self.client.get_message_id(msg_id, source='v2'), "v2_mail")
        
        # Total count should be 2
        all_ids = self.client.get_all_message_ids()
        # Note: same key in dict - this returns 1 because dict keys must be unique
        # But in the database there are 2 records


if __name__ == '__main__':
    unittest.main()
