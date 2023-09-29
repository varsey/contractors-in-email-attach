import time
import random
import pathlib

from typing import Optional
from .ApiClient import ApiClient
from .ProcessorServer import ProcessorServer


class Worker:
    def __init__(self, prc: ProcessorServer):
        self.logger = prc.log
        self.prc = prc

    def sleep(self):
        """Sleep worker for some time period"""
        time_to_sleep = random.choice([0.1, 0.7])
        time.sleep(time_to_sleep)
        self.logger.info(f'Done sleeping for {time_to_sleep}')

    def msg_from_req(self, req) -> Optional[str]:
        message = None
        try:
            message = req.json['message']
        except Exception as ex:
            self.prc.error_processor(ex)
        return message if message else None

    def run_mail_process(self, mail_folder: str, msg_id: Optional[str], apiclient: Optional[ApiClient]) -> dict:
        result = {}
        try:
            result = self.prc.process_email(mail_folder, msg_id=msg_id)
        except Exception as ex:
            self.prc.error_processor(ex)
            self.logger.error('Email processing failed')
            if apiclient is not None:
                apiclient.send_ls_payload(payload=self.read_log_file(), project_id='10')
        return result

    @staticmethod
    def read_log_file(log_filename: str = pathlib.Path().resolve() / 'logs.txt') -> str:
        with open(log_filename, 'r') as f:
            log = f.read()
        return log
