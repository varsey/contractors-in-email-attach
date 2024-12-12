import gc
import os
import logging

from flask import Flask, jsonify, request

from common.Logger import Logger
from src.ApiProcessor import ApiProcessor


app = Flask(__name__)

mail_folder = 'inbox'
email, password, server = os.getenv("EMAIL"), os.getenv('PASS'), os.getenv('SERVER')
if any(v is None for v in [email, password, server]):
    raise ValueError("One of the EMAIL, PASS, SERVER parameter is not set")

logger = Logger()
prc = ApiProcessor(email, password, server, mail_folder, logger)

logging.getLogger('pymorphy2.opencorpora_dict.wrapper').setLevel(logging.ERROR)


@app.route("/")
def route_status():
    return "This is contractor parser"


@app.route("/api/parsing/")
def contractor_parser_parameter():
    email_id = request.args.get('mid')
    card = prc.process_email_by_id(message_id=email_id)
    gc.collect()
    return jsonify(card)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)
