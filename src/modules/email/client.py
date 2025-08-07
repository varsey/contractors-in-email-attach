import os
import imaplib

import eml_parser

from src.logger.Logger import Logger
from src.modules.parsers.attachment import AttachmentParser

log = Logger().log


class EmailClient(AttachmentParser):
    def __init__(self, email: str, password: str, server: str, mail_folder: str):
        AttachmentParser.__init__(self)
        self.email = email
        self.password = password
        self.server = server
        self.mail_folder = mail_folder

    def setup_mail_connector(self):
        try:
            self.mail_connector = imaplib.IMAP4_SSL(self.server)
            self.mail_connector.login(self.email, self.password)
            self.sel = self.mail_connector.select(self.mail_folder) # mail_connector.list()[1] - list of folders in mailbox
        except Exception as e:
            log.error(f'Cannot connect, check connection params {e}')
        return self.mail_connector

    def teardown_mail_connector(self):
        if self.mail_connector.state == 'SELECTED':
            try:
                self.mail_connector.close()
                self.mail_connector.logout()
            except Exception as e:
                log.error(f'Cannot close imap connection: {e}')
        return None

    def get_message_attributes(self, data) -> (dict, str, str):

        def _parsing_wrapper(attach_path):
            text = ''
            pdf_file = ''.join(attach_path.split('.')[:-1]) + '.pdf'
            csv_file = ''.join(attach_path.split('.')[:-1]) + '.csv'
            docx_file = ''.join(attach_path.split('.')[:-1]) + self.docx_ext
            if os.path.isfile(pdf_file):
                text = self.parse_pdf(pdf_file)
            elif os.path.isfile(csv_file):
                text = self.parse_csv(csv_file)
            elif os.path.isfile(docx_file):
                text = self.parse_docx(docx_file)
            else:
                log.error('No files to process!')
            return text

        ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=True)
        message_text, attach_name, header_from = '', '', ''
        attach_names, attach_texts = [], {}
        for response_part in data:
            if isinstance(response_part, tuple):
                parsed_eml = ep.decode_email_bytes(response_part[1])
                message_text, header_from = self.get_message_text_and_header(parsed_eml)
                attach_names = self.save_attachments_files(parsed_eml)
                for attach_name in attach_names:
                    try:
                        attachment_path = self.convert_attachment_file(attach_name)
                        full_text = _parsing_wrapper(attachment_path)
                        attach_texts[attach_name] = full_text
                    except Exception as ex:
                        log.error(f'{ex}')
                        self.error_processor(ex)
                        continue

        return attach_texts, message_text, header_from

    @staticmethod
    def see_msg(mail_connector: imaplib, mail_id, message_parts: str = '(BODY.PEEK[])') -> imaplib:
        return mail_connector.fetch(mail_id, message_parts)[1]   # not mark as seen: '(BODY.PEEK[])', otherwise 'RFC822'

    def get_mail_ids(self, tag: str = 'SEEN') -> list:
        mail_ids = []
        for block in self.mail_connector.search(None, f'({tag})')[1]:
            mail_ids += block.split()
        print(len(mail_ids))
        return mail_ids
