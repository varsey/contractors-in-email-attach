import os
import imaplib
import logging
import eml_parser
from typing import Optional
from .Processor import Processor


class ProcessorServer(Processor):
    def __init__(self, email: str, password: str, server: str, mail_folder: str, log: logging):
        Processor.__init__(self, log.log)
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
            self.log.error(f'Cannot connect, check connection params {e}')
        return self.mail_connector

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
                self.log.error('No files to process!')
            return text

        ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=True)
        _, message_text, _, attach_name, header_from = '', '', '', '', ''
        attach_names, _, attach_texts = [], [], {}
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
                        self.log.error(f'{ex}')
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

    def process_email(self, mail_folder: str, msg_id: Optional[str], start_point: int = 0) -> dict:
        """Email message from gmail"""
        if msg_id is not None:
            self.log.info(f'With with a single id {msg_id}')
            to_process_list = [msg_id]
        else:
            self.log.info(f'With with last {abs(start_point)} ids')
            mail_ids = self.get_mail_ids(mail_folder)
            to_process_list = mail_ids[start_point:]
        orgs_dict = {}
        for mail_id in to_process_list:
            try:
                data = self.see_msg(self.mail_connector, mail_id)
                attach_texts, message_text, header_from = self.get_message_attributes(data)
                organization_dict = self.parse_attributes(attach_texts, message_text, header_from)
                # filter if any field has * - doubts on correctness
                organization = {k: v for k, v in organization_dict.items() if '*' not in ''.join(v.values())}
                orgs_dict.update(organization)
            except Exception as ex:
                self.error_processor(ex)
                self.log.warning('Email processing failed')
                return {}

        return orgs_dict

    def is_next_day(self, start_point: int = 2) -> bool:
        mail_ids = self.get_mail_ids('(SEEN)')
        dates, day_names = [], []
        for mail_id in mail_ids[-start_point:]:
            data = self.see_msg(self.mail_connector, mail_id)
            ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=True)
            for response_part in data:
                if isinstance(response_part, tuple):
                    parsed_eml = ep.decode_email_bytes(response_part[1])
                    email_date = parsed_eml['header']['header']['date'][0]
                    dates.append(email_date.split()[1])
                    day_names.append(email_date.split(',')[0])
        self.log.info(f'dates - {dates}, day names - {day_names}')
        if len(set(dates)) > 1 and (day_names[0] in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']):
            return True
        return False

    def get_messages_for_ml(self, start_point: int = 90) -> list:
        messages = []
        mail_ids = self.get_mail_ids('(SEEN)')
        for mail_id in mail_ids[-start_point:]:
            data = self.see_msg(self.mail_connector, mail_id, '(BODY.PEEK[])')
            ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=True)
            message_text = ''
            for response_part in data:
                if isinstance(response_part, tuple):
                    parsed_eml = ep.decode_email_bytes(response_part[1])
                    if len(parsed_eml['body']) > 0:
                        message_text = self.parse_message_text(parsed_eml)
            messages.append(message_text)

        return messages
