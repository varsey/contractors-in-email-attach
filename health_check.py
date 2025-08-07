import os
import time
import random
import smtplib
import requests
import logging
from logging.handlers import RotatingFileHandler
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('health_checker')
logger.setLevel(logging.INFO)

# Create rotating file handler, 10MB = 10 * 1024 * 1024 bytes
file_handler = RotatingFileHandler('health.logs', maxBytes=10*1024*1024, backupCount=30)
file_handler.setLevel(logging.INFO)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

SERVER_URL = os.getenv("SERVER_URL")
CHECK_INTERVAL = random.choice(range(120, 300))

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

if any(v is None for v in [SMTP_USERNAME, SMTP_PASSWORD, TO_EMAIL]):
    logger.error("One of the SMTP_USERNAME, SMTP_PASSWORD, TO_EMAIL parameter is not set")
    raise ValueError("One of the SMTP_USERNAME, SMTP_PASSWORD, TO_EMAIL parameter is not set")


def send_email_alert(body: str):
    logger.info(f'Sending email alert to {TO_EMAIL}')
    subject = 'Flask Server Down Alert'

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = ", ".join(TO_EMAIL.split(','))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, TO_EMAIL.split(','), msg.as_string())
        logger.info(f'Alert email sent to {TO_EMAIL}')
    except Exception as e:
        logger.error(f'Failed to send email: {e}')


def check_server():
    try:
        response = requests.get(SERVER_URL, timeout=130)
        if response.status_code != 200:
            logger.error(f'Server is broken: status code: {response.status_code}')
            send_email_alert(f'The Flask server at {SERVER_URL} is broken: {response.content}')
        else:
            logger.info(f'Server is up: {response.content}, it took {response.elapsed.total_seconds()} s')
    except requests.exceptions.RequestException as e:
        logger.error(f'Server is down: exception: {e}')
        send_email_alert(f'The Flask server at {SERVER_URL} is not reachable')


if __name__ == '__main__':
    logger.info('Health check service started')
    while True:
        check_server()
        time.sleep(CHECK_INTERVAL)
