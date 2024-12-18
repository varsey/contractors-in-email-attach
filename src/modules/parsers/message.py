import os
import shutil
import pickle
from typing import Optional

from src.logger.Logger import Logger
from src.modules.parsers.text import TextParser
from src.modules.parsers.attachment import AttachmentParser
from src.modules.email.client import EmailClient

log = Logger().log


class MessageProcessor(EmailClient):
    def __init__(self, email: str, password: str, server: str, mail_folder: str):
        AttachmentParser.__init__(self)
        # TO-DO remove email client from here
        EmailClient.__init__(self, email, password, server, mail_folder)
        self.parsers = TextParser()
        # TO-DO move name to settings
        self.index_file = 'message_ids.pkl'
        self.mail_folder = mail_folder

    @staticmethod
    def org_structure(inn, bik, r_account, tel):
        return {
            'inn': [inn if len(inn) == 10 or len(inn) == 12 else inn + '*'][0],
            'bik': [bik if len(bik) == 9 else bik + '*'][0],
            'r_account': [r_account if len(r_account) == 20 else r_account + '*'][0],
            "phone": tel,
        }

    def parse_attributes(self, attach_texts: dict, message_text: str) -> dict:
        organization_dict = {}
        for attach_name, full_text in attach_texts.items():
            log.info(f'Processing attachment: {attach_name}')
            card = self.parsers.clean_text(full_text)  # full_text att_text
            if not card:
                log.info('No card found')

            inn = self.parsers.parse_inn(card.lower())
            bik = self.parsers.parse_bik(card)
            r_account = self.parsers.parse_r_account(card)

            tel = self.parsers.parse_tel(self.parsers.clean_text(message_text))
            if len(tel) == 0:
                tel = self.parsers.parse_tel(card)

            org_key = str(attach_name).split('/')[-1]
            organization_dict[org_key] = self.org_structure(
                inn, bik, r_account, tel
            )

        return organization_dict

    def process_email_by_id(self, message_id: str) -> dict:
        if len(message_id) <= 1:
            return {}
        else:
            log.info(f'Starting {message_id} parsing')
            # TO-DO move last_letters to settings
            message_ids = self.upd_index(message_id, last_letters=30)
            orgs_dict = {}
            if message_ids.get(message_id, 0) != 0:
            # for message_id in list(message_ids.keys())[:1000]:
                try:
                    data = self.see_msg(self.mail_connector, mail_id=message_ids[message_id])
                    attach_texts, message_text, _ = self.get_message_attributes(data)
                    organization_candidates = self.parse_attributes(attach_texts, message_text)
                    organization = self.compose_organizations(organization_candidates)
                    for k, v in organization_candidates.items():
                        log.info(f'{k}:')
                        log.info(f'{v}')
                    orgs_dict.update(organization)
                except Exception as ex:
                    self.error_processor(ex)
                    log.error('Email processing failed')
                    return {}
            log.info(f'{len(orgs_dict)} - {orgs_dict.__str__()}')
            log.info('Parsing finished\n\n')
            self.clear_folders([f'{os.getcwd()}/temp/'])
            return orgs_dict

    def compose_organizations(self, organization_dict: dict) -> dict:
        organization = {
            k: v for k, v in organization_dict.items()
            if '*' not in v['inn']
               and '*' not in v['r_account']
               and '*' not in v['bik']
        }
        return organization

    def get_index(self, mail_id) -> str:
        try:
            idx = ''.join((self.mail_connector.fetch(mail_id, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')[1][0][-1] # BODY.PEEK[])
            .decode('UTF-8')
            .split('<')[1]
            .split('>'))[:-1])
        except (IndexError, TypeError):
            return ''
        return idx

    def dump_messages(self, mail_ids, message_ids):
        to_process_list = mail_ids
        for num, mail_id in enumerate(to_process_list):
            indx = self.get_index(mail_id)
            log.info(f'{num} - {mail_id} - {indx}')
            if len(indx) > 0 and indx not in message_ids.keys():
                message_ids[indx] = mail_id
                log.info(f'{indx} added')
        with open(self.index_file, 'wb') as fp:
            pickle.dump(message_ids, fp, protocol=pickle.HIGHEST_PROTOCOL)

    def upd_index(self, message_id: Optional[str], last_letters: int = 30):
        self.setup_mail_connector()
        last_indx = int(self.mail_connector.select(self.mail_folder)[1][0])
        mail_ids = [str(x).encode() for x in range(last_indx - last_letters, last_indx + 1)]
        if not os.path.exists(self.index_file):
            log.warning(f'No {self.index_file} file, creating one for {last_letters} last items')
            self.dump_messages(mail_ids, message_ids={})
        with open(self.index_file, 'rb') as fp:
            message_ids = pickle.load(fp)
        if message_id in message_ids.keys():
            log.info('Message-id found')
            return message_ids
        self.dump_messages(mail_ids, message_ids,)
        return message_ids

    def clear_folders(self, folder_paths: list):
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
