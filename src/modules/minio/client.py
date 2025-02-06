import boto3


class MinioClient:
    def __init__(self):
        session = boto3.session.Session()
        self.s3 = session.client(
            service_name='s3',
            endpoint_url='https://storage.yandexcloud.net',
            use_ssl=False,
        )


    def upload_file(self, file_path):
        filename = file_path.split('/')[-1]
        print('Uploading file: {}'.format(filename))
        self.s3.upload_file(file_path, 'varsey-backet', f'mails/{filename}')

# mc = MinioClient()
# mc.upload_file('/home/varsey/PycharmProjects/contractors-in-email-attach/mail.pdf')