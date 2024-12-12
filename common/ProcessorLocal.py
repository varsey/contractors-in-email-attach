import os
import logging
import eml_parser
from .Processor import Processor


class ProcessorLocal(Processor):
    def __init__(self, log: logging):
        Processor.__init__(self, log.log)

    # Processor for local *.eml file
    def get_eml_attributes(self, eml_file):
        ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=True)
        att_text, attach_name, full_text, attach_names, full_texts, attach_texts = '', '', '', [], [], {}
        parsed_eml = ep.decode_email_bytes(eml_file)
        message_text, header_from = self.get_message_text_and_header(parsed_eml)
        attach_names = self.save_attachments_files(parsed_eml)
        for attach_name in attach_names:
            try:
                attachment_path = self.convert_attachment_file(attach_name)
                if os.path.isfile(''.join(attachment_path.split('.')[:-1]) + '.pdf'):
                    full_text = self.parse_pdf(attachment_path)
                elif os.path.isfile(''.join(attachment_path.split('.')[:-1]) + self.docx_ext):
                    full_text = self.parse_docx(attachment_path)
                else:
                    full_text = self.parse_csv(attachment_path)
                attach_texts[attach_name] = full_text
            except Exception as ex:
                self.log.error_processor(ex)
                continue
        return attach_texts, message_text, header_from

    def process_eml(self, file) -> dict:
        organization_dict = {}
        try:
            with open(file, 'rb') as fhdl:
                eml_file = fhdl.read()
            attach_texts, message_text, header_from = self.get_eml_attributes(eml_file)
            organization_dict = self.parse_attributes(attach_texts, message_text, header_from)
            # filter if any field has * - doubts on correctness
            organization_dict = {k: v for k, v in organization_dict.items() if '*' not in ''.join(v.values())}
        except Exception as ex:
            self.log.error_processor(ex)
            self.log.info('email processing failed')
        return organization_dict
