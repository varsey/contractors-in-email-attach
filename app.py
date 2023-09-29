import os
from flask import Flask, jsonify, request

from common.Logger import Logger
from src.ApiProcessor import ApiProcessor


app = Flask(__name__)

email, password, server = os.getenv("EMAIL"), os.getenv('PASS'), os.getenv('SERVER')

logger = Logger()
prc = ApiProcessor(email, password, server, logger)


@app.route("/")
def route_status():
    return "This is contractor parser"


@app.route("/api/parse/<email_id>/")
def contractor_parser_url(email_id: str):
    card = prc.process_email_by_id(message_id=email_id)
    return jsonify(card)


@app.route("/api/parsing/")
def contractor_parser_parameter():
    email_id = request.args.get('mid')
    card = prc.process_email_by_id(message_id=email_id, mail_folder='inbox')
    return jsonify(card)


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=8000)
