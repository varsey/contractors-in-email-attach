import os
import shutil
import pickle
import logging
from typing import Optional
from src.ApiParsers import ApiParsers
from common.Processor import Processor
from common.ProcessorServer import ProcessorServer


class ApiProcessor(ProcessorServer):
    def __init__(self, email: str, password: str, server: str, mail_folder: str, log: logging):
        Processor.__init__(self, log.log)
        ProcessorServer.__init__(self, email, password, server, mail_folder, log)
        self.parser = ApiParsers()
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
        self.log.info(self.parser.clean_text(message_text))
        for attach_name, full_text in attach_texts.items():
            self.log.info(f'Processing attachment: {attach_name}')
            card = self.parser.clean_text(full_text)  # full_text att_text
            self.log.info(['card: ', card])
            self.log.info(['full_text: ', full_text])
            self.log.info(card) if card else self.log.info('No card found')

            inn = self.parser.parse_inn(card.lower())
            bik = self.parser.parse_bik(card)
            r_account = self.parser.parse_r_account(card)

            tel = self.parser.parse_tel(self.parser.clean_text(message_text))
            if len(tel) == 0:
                tel = self.parser.parse_tel(card)

            org_key = str(attach_name).split('/')[-1]
            organization_dict[org_key] = self.org_structure(
                inn, bik, r_account, tel
            )
        return organization_dict

    def process_email_by_id(self, message_id: str) -> dict:
        if len(message_id) <= 1:
            return {}
        else:
            self.log.warning(f'Starting {message_id} parsing')
            message_ids = self.upd_index(message_id, last_letters=60)
            orgs_dict = {}
            if message_ids.get(message_id, 0) != 0:
                print(message_id, message_ids[message_id])
                try:
                    data = self.see_msg(self.mail_connector, mail_id=message_ids[message_id])
                    attach_texts, message_text, _ = self.get_message_attributes(data)
                    organization_dict = self.parse_attributes(attach_texts, message_text)
                    organization = {
                        k: v for k, v in organization_dict.items()
                        if '*' not in v['inn']
                           and '*' not in v['r_account']
                           and '*' not in v['bik']
                    }
                    orgs_dict.update(organization)
                    self.log.info(organization.keys().__str__())
                    self.log.info(organization.values().__str__())
                except Exception as ex:
                    self.error_processor(ex)
                    self.log.warning('Email processing failed')
                    return {}
                self.log.warning('Parsing finished')
            self.log.warning(orgs_dict.__str__())
            self.log.warning(len(orgs_dict))
            return orgs_dict

    def get_index(self, mail_id) -> str:
        try:
            idx = ''.join((self.mail_connector.fetch(mail_id, '(BODY[HEADER.FIELDS (MESSAGE-ID)])')[1][0][-1]
            .decode('UTF-8')
            .split('<')[1]
            .split('>'))[:-1])
        except (IndexError, TypeError):
            return ''
        return idx

    def dump_messages(self, mail_ids, message_ids, last_letters: int = 30):
        self.log.warning(f'Message-id not found, parsing {last_letters} last items')
        to_process_list = mail_ids #[-last_letters:]
        for num, mail_id in enumerate(to_process_list):
            indx = self.get_index(mail_id)
            self.log.warning(f'{num} - {mail_id} - {indx}')
            if len(indx) > 0 and indx not in message_ids.keys():
                message_ids[indx] = mail_id
                self.log.warning(f'{indx} added')
        with open(self.index_file, 'wb') as fp:
            pickle.dump(message_ids, fp, protocol=pickle.HIGHEST_PROTOCOL)

    def upd_index(self, message_id: Optional[str], last_letters: int = 30):
        self.setup_mail_connector()
        last_indx = int(self.mail_connector.select(self.mail_folder)[1][0])
        mail_ids = [str(x).encode() for x in range(last_indx - last_letters, last_indx + 1)]
        print(mail_ids)
        if not os.path.exists(self.index_file):
            logging.error(f'No {self.index_file} file')
            self.dump_messages(mail_ids, message_ids={}, last_letters=last_letters)
        with open(self.index_file, 'rb') as fp:
            message_ids = pickle.load(fp)
        if message_id in message_ids.keys():
            self.log.warning('Message-id found')
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
                    self.log.error(f'Failed to delete {file_path}: {e}')
        return None
