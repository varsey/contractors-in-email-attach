import os


MAIL_FOLDER = 'inbox'
email, password, server = os.getenv("EMAIL"), os.getenv('PASS'), os.getenv('SERVER')


class Config:
    def __init__(self):
        self.email = os.getenv("EMAIL")
        self.password = os.getenv('PASS')
        self.server = os.getenv('SERVER')
        self.mail_folder = MAIL_FOLDER
        self.check()


    @property
    def creds(self):
        return {'email': self.email, 'password': self.password, 'server': self.server, 'mail_folder': self.mail_folder}

    @property
    def creds2(self):
        email2 = os.getenv("EMAIL2")
        password2 = os.getenv('PASS2')
        server = os.getenv('SERVER')
        return {'email': email2, 'password': password2, 'server': server, 'mail_folder': self.mail_folder}

    def check(self):
        if any(v is None for v in self.creds.values()):
            raise ValueError(f"One of the EMAIL, PASS, SERVER parameter is not set: {self.creds}")
