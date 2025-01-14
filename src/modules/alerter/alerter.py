import os
import smtplib
from email.mime.text import MIMEText
from src.logger.Logger import Logger

log = Logger().log


SMTP_SERVER = 'smtp.yandex.ru'
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

if any(v is None for v in [SMTP_USERNAME, SMTP_PASSWORD, TO_EMAIL]):
    raise ValueError("One of the SMTP_USERNAME, SMTP_PASSWORD, TO_EMAIL parameter is not set")


def send_email_alert(body_text: str):
    subject = 'Уведомление от парсера ИНН'
    body = f'В письме от {body_text} есть нераспознаные ИНН'

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = ", ".join(TO_EMAIL.split(','))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, TO_EMAIL.split(','), msg.as_string())
        log.warning(f'Alert email sent to {TO_EMAIL}')
    except Exception as e:
        log.error(f'Failed to send email: {e}')

