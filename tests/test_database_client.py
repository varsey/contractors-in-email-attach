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

    def test_normalizes_message_ids_and_mail_ids(self):
        saved = self.client.save_message_id(" <TeSt-Id@example.com>\n", " 77 ")
        self.assertTrue(saved)

        retrieved_mail_id = self.client.get_message_id("TeSt-Id@example.com")
        self.assertEqual(retrieved_mail_id, "77")

        all_ids = self.client.get_all_message_ids()
        self.assertIn("TeSt-Id@example.com", all_ids)
        self.assertEqual(all_ids["TeSt-Id@example.com"], "77")

    def test_save_multiple_message_ids_ignores_empty_after_normalization(self):
        count = self.client.save_multiple_message_ids(
            {
                " <id-1> ": " 1 ",
                "<>": "2",
                "": "3",
            }
        )

        self.assertEqual(count, 1)
        all_ids = self.client.get_all_message_ids()
        self.assertEqual(all_ids, {"id-1": "1"})


if __name__ == '__main__':
    unittest.main()
