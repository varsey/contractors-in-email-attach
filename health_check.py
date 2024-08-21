import os
import time
import smtplib
import requests
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()


SERVER_URL = 'http://0.0.0.0:8000'
CHECK_INTERVAL = 10

SMTP_SERVER = 'smtp.yandex.ru'
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

if any(v is None for v in [SMTP_USERNAME, SMTP_PASSWORD, TO_EMAIL]):
    raise ValueError("One of the SMTP_USERNAME, SMTP_PASSWORD, TO_EMAIL parameter is not set")


def send_email_alert():
    print(f'Sending email alert to {TO_EMAIL}')
    subject = 'Flask Server Down Alert'
    body = f'The Flask server at {SERVER_URL} is not reachable.'

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = ", ".join(TO_EMAIL.split(','))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, TO_EMAIL.split(','), msg.as_string())
        print(f'Alert email sent to {TO_EMAIL}')
    except Exception as e:
        print(f'Failed to send email: {e}')


def check_server():
    try:
        response = requests.get(SERVER_URL, timeout=30)
        if response.status_code != 200:
            print(f'Server is down! Status code: {response.status_code}')
            send_email_alert()
        else:
            print('Server is up.')
    except requests.exceptions.RequestException as e:
        print(f'Server is down! Exception: {e}')
        send_email_alert()


if __name__ == '__main__':
    while True:
        check_server()
        time.sleep(CHECK_INTERVAL)