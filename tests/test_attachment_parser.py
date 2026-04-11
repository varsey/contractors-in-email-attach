import unittest
from unittest.mock import MagicMock, patch
import os
from src.modules.parsers.attachment import AttachmentParser

class TestAttachmentParser(unittest.TestCase):
    def setUp(self):
        self.parser = AttachmentParser()

    def test_attach_extention_check(self):
        self.assertTrue(self.parser.attach_extention_check("test.pdf"))
        self.assertTrue(self.parser.attach_extention_check("test.docx"))
        self.assertFalse(self.parser.attach_extention_check("test.txt"))

    def test_attach_name_check(self):
        self.assertTrue(self.parser.attach_name_check("Aкт сверки.pdf"))
        self.assertFalse(self.parser.attach_name_check("ТЗ на разработку.pdf"))
        self.assertFalse(self.parser.attach_name_check("Заявка.docx"))

    @patch('src.modules.parsers.attachment.Document')
    def test_parse_docx(self, mock_doc):
        # Mocking docx Document
        mock_document = MagicMock()
        mock_doc.return_value = mock_document
        
        # Mock table data
        mock_table = MagicMock()
        mock_row = MagicMock()
        mock_cell = MagicMock()
        mock_cell.text = "Cell Text"
        mock_row.cells = [mock_cell]
        mock_table.rows = [mock_row]
        mock_document.tables = [mock_table]
        
        # Mock paragraph data
        mock_para = MagicMock()
        mock_para.text = "Para Text"
        mock_document.paragraphs = [mock_para]
        
        result = self.parser.parse_docx("test.docx")
        self.assertIn("Cell Text", result)
        self.assertIn("Para Text", result)

    @patch('src.modules.parsers.attachment.PyPDF2.PdfReader')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_parse_pdf_text(self, mock_open, mock_pdf_reader):
        mock_reader = MagicMock()
        mock_pdf_reader.return_value = mock_reader
        mock_page_1 = MagicMock()
        mock_page_1.extract_text.return_value = "PDF Text content"
        mock_page_2 = MagicMock()
        mock_page_2.extract_text.return_value = "Second page"
        mock_reader.pages = [mock_page_1, mock_page_2]

        result = self.parser.parse_pdf("test.pdf")
        self.assertEqual(result, "PDF Text content Second page")

    @patch('src.modules.parsers.attachment.gc.collect')
    @patch('src.modules.parsers.attachment.pytesseract.image_to_string')
    @patch('src.modules.parsers.attachment.Image.open')
    @patch('src.modules.parsers.attachment.convert_from_path')
    @patch('src.modules.parsers.attachment.PyPDF2.PdfReader')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_parse_pdf_ocr_fallback_by_page(
            self,
            mock_open,
            mock_pdf_reader,
            mock_convert_from_path,
            mock_image_open,
            mock_image_to_string,
            mock_gc_collect,
    ):
        mock_reader = MagicMock()
        mock_pdf_reader.return_value = mock_reader
        mock_page_1 = MagicMock()
        mock_page_1.extract_text.return_value = ""
        mock_page_2 = MagicMock()
        mock_page_2.extract_text.return_value = ""
        mock_reader.pages = [mock_page_1, mock_page_2]

        page_image_1 = MagicMock()
        page_image_2 = MagicMock()
        mock_convert_from_path.side_effect = [[page_image_1], [page_image_2]]

        image_context = MagicMock()
        mock_image_open.return_value.__enter__.return_value = image_context
        mock_image_to_string.side_effect = ["ocr page 1", "ocr page 2"]

        result = self.parser.parse_pdf("test.pdf")

        self.assertIn("ocr page 1", result)
        self.assertIn("ocr page 2", result)
        self.assertEqual(mock_convert_from_path.call_count, 2)
        mock_gc_collect.assert_called()

    @patch('src.modules.parsers.attachment.csv.reader')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_parse_csv(self, mock_open, mock_csv_reader):
        mock_csv_reader.return_value = [['col1', 'col2'], ['val1', 'val2']]
        
        result = self.parser.parse_csv("test.csv")
        self.assertIn("col1 col2", result)
        self.assertIn("val1 val2", result)

    def test_parse_message_text_handles_missing_content(self):
        parsed_eml = {
            'body': [{'type': 'text/html'}]
        }

        result = self.parser.parse_message_text(parsed_eml)
        self.assertEqual(result, '')

    def test_parse_message_text_uses_text_fallback(self):
        parsed_eml = {
            'body': [{'text': 'plain body text'}]
        }

        result = self.parser.parse_message_text(parsed_eml)
        self.assertIn('plain body text', result)

if __name__ == '__main__':
    unittest.main()
