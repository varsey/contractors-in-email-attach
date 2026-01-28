import unittest
from unittest.mock import MagicMock, patch
from src.modules.email.client import EmailClient

class TestEmailClient(unittest.TestCase):
    @patch('src.modules.email.client.imaplib.IMAP4_SSL')
    def test_setup_mail_connector(self, mock_imap):
        mock_conn = MagicMock()
        mock_imap.return_value = mock_conn
        
        client = EmailClient("test@email.com", "pass", "server.com", "INBOX")
        conn = client.setup_mail_connector()
        
        mock_conn.login.assert_called_once_with("test@email.com", "pass")
        mock_conn.select.assert_called_once_with("INBOX")
        self.assertEqual(conn, mock_conn)

    def test_get_mail_ids(self):
        client = EmailClient("test@email.com", "pass", "server.com", "INBOX")
        client.mail_connector = MagicMock()
        client.mail_connector.search.return_value = ('OK', [b'1 2 3'])
        
        ids = client.get_mail_ids(tag='UNSEEN')
        self.assertEqual(ids, [b'1', b'2', b'3'])

    @patch('src.modules.email.client.eml_parser.EmlParser')
    @patch.object(EmailClient, 'get_message_text_and_header')
    @patch.object(EmailClient, 'save_attachments_files')
    @patch.object(EmailClient, 'convert_attachment_file')
    def test_get_message_attributes(self, mock_convert, mock_save, mock_get_text, mock_eml_parser):
        client = EmailClient("test@email.com", "pass", "server.com", "INBOX")
        
        # Mock data
        data = [(None, b'raw_eml_data')]
        mock_ep = MagicMock()
        mock_eml_parser.return_value = mock_ep
        mock_ep.decode_email_bytes.return_value = {'parsed': 'eml'}
        
        mock_get_text.return_value = ("Message Text", "From Header")
        mock_save.return_value = ["attach1.pdf"]
        mock_convert.return_value = "temp/attach1.pdf"
        
        # We need to mock _parsing_wrapper or the methods it calls
        with patch.object(EmailClient, 'parse_pdf') as mock_parse_pdf:
            mock_parse_pdf.return_value = "Parsed PDF Text"
            
            with patch('src.modules.email.client.os.path.isfile') as mock_isfile:
                mock_isfile.side_effect = lambda p: p.endswith('.pdf')
                
                attach_texts, message_text, header_from = client.get_message_attributes(data)
                
                self.assertEqual(message_text, "Message Text")
                self.assertEqual(header_from, "From Header")
                self.assertEqual(attach_texts["attach1.pdf"], "Parsed PDF Text")

if __name__ == '__main__':
    unittest.main()
