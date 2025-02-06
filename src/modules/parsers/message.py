import os
import json
import random
import shutil
import pickle
from typing import Optional

import requests

from src.logger.Logger import Logger
from src.modules.parsers.text import TextParser
from src.modules.parsers.attachment import AttachmentParser
from src.modules.email.client import EmailClient
from src.modules.alerter.alerter import send_email_alert
from src.modules.generator.pdf import generate_pdf
from src.modules.minio.client import MinioClient

log = Logger().log

s3 = MinioClient()

URL = "http://158.160.98.2:8000/parse_pdf"


def compose_organizations(organization_dict: dict) -> dict:
    return {k: v for k, v in organization_dict.items()}


def clear_folders(folder_paths: list):
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
    def org_structure(inns):
        return {
            'inn': [inn if len(inn) in (10, 12) else inn + '*' for inn in inns if len(inn + '*') > 9],
        }


    def parse_attributes(self, attach_texts: dict, message_text: str) -> dict:
        organization_dict = {}
        inns = []
        for mess_part in [f'инн{x}' for x in self.parsers.clean_text(message_text).split('инн')]:
            inn = self.parsers.parse_inn(mess_part)
            inns.append(inn)
        organization_dict['message'] = self.org_structure(inns)

        for attach_name, full_text in attach_texts.items():
            inns = []
            log.info(f'Processing attachment: {attach_name}')
            card = self.parsers.clean_text(full_text)  # full_text att_text
            if not card:
                log.info('No card found')

            for card_part in card.lower().split('инн'):
                inn = self.parsers.parse_inn(card_part)
                inns.append(inn)

            org_key = str(attach_name).split('/')[-1]
            organization_dict[org_key] = self.org_structure(inns)

        return organization_dict


    def process_email_by_id(self, message_id: str) -> dict:
        if len(message_id) <= 1:
            return {}
        else:
            log.info(f'Starting {message_id} parsing')
            # TO-DO move last_letters to settings
            message_ids = self.upd_index(message_id, last_letters=20)
            orgs_dict = {}
            if message_ids.get(message_id, 0) != 0:
            # for message_id in list(message_ids.keys())[:1000]:
                try:
                    data = self.see_msg(self.mail_connector, mail_id=message_ids[message_id])
                    attach_texts, message_text, header_from = self.get_message_attributes(data)
                    organization_candidates = self.parse_attributes(attach_texts, message_text)
                    if (
                        len(organization_candidates.values()) == 1
                        and
                        '*' in str(organization_candidates.values())
                    ):
                        send_email_alert(header_from)
                    organization = compose_organizations(organization_candidates)
                    for k, v in organization_candidates.items():
                        log.info(f'\n{k}:\n{v}')
                    orgs_dict.update(organization)
                except Exception as ex:
                    self.error_processor(ex)
                    log.error('Email processing failed')
                    return {}
            log.info(f'{len(orgs_dict)} - {orgs_dict.__str__()}')
            log.info('Parsing finished\n\n')
            clear_folders([f'{os.getcwd()}/temp/'])
            inns = [x['inn'] for x in orgs_dict.values()]
            return {'inns': list(set([x for xs in inns for x in xs if '*' not in x]))}

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
        log.info('Dumping messages, please wait...')
        for num, mail_id in enumerate(mail_ids):
            if mail_id not in message_ids.values():
                indx = self.get_index(mail_id)
                if len(indx) > 0 and indx not in message_ids.keys():
                    message_ids[indx] = mail_id
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
        else:
            log.warning('Message-id not found')

        self.dump_messages(mail_ids, message_ids)
        with open(self.index_file, 'rb') as fp:
            message_ids = pickle.load(fp)

        return message_ids

    def process_random_id(self) -> dict:
            message_ids = self.upd_index(None, last_letters=50)
            message_id = random.choice(list(message_ids.keys())[:50])
            if message_ids.get(message_id, 0) != 0:
                try:
                    data = self.see_msg(self.mail_connector, mail_id=message_ids[message_id])
                    attach_texts, message_text, _ = self.get_message_attributes(data)
                except Exception as ex:
                    self.error_processor(ex)
                    log.error('Email processing failed')
                    return {}
            log.info('Parsing finished\n\n')
            clear_folders([f'{os.getcwd()}/temp/'])

            names = []
            names.extend(generate_pdf({'mail': message_text}))
            names.extend(generate_pdf(attach_texts))
            print(names)
            for name in names:
                print('uploading', f'{os.getcwd()}/{name}')
                s3.upload_file(f'{os.getcwd()}/{name}')

            data = {
                "urls": [f"https://storage.yandexcloud.net/varsey-backet/mails/{file}" for file in names if 'карт' in file or 'mail' in file]
            }
            print(data, '***')
            response = requests.post(URL, headers={"Content-Type": "application/json"}, data=json.dumps(data))

            if response.status_code == 200:
                print("Response JSON:", response.json())
            else:
                print("Error:", response.status_code, response.text)

            log.info('Processing successful')
            return {'attach': attach_texts, 'mail': message_text}
