import json
import requests
from requests.auth import HTTPBasicAuth


class ApiClient:
    def __init__(self, endpoint: str, user: str = '', password: str = ''):
        self.endpoint = endpoint
        self.user = user
        self.password = password

    def send_contractor_payload(self, payload: dict) -> requests.Response:
        response = requests.post(
            self.endpoint,
            data=json.dumps(payload),
            auth=HTTPBasicAuth(self.user, self.password),
            headers={'Accept': 'application/json'}
        )
        response.encoding = response.apparent_encoding
        return response

    def send_ls_payload(self, payload: str, project_id: str = '1') -> requests.Response:
        """Sending payload to label studio server"""
        response = requests.post(
            url=f'{self.endpoint}/api/projects/{project_id}/import',
            headers={
                'Authorization': f'Token {self.password}',
                'Content-Type': 'application/json',
            },
            data=json.dumps({"text": payload}),
        )
        print(response, response.content)
        return response
