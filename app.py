import gc
import logging

from flask import Flask, jsonify, request

from src.modules.parsers.message import MessageProcessor
from src.config.cfg import Config

app = Flask(__name__)
cfg = Config()
prc = MessageProcessor(**cfg.creds)

logging.getLogger('pymorphy2.opencorpora_dict.wrapper').setLevel(logging.ERROR)


@app.route("/")
def route_status():
    return "This is contractor parser"


@app.route("/api/parsing/")
def contractor_parser_parameter():
    try:
        email_id = request.args.get('mid')
        card = prc.process_email_by_id(message_id=email_id)
        gc.collect()

        return jsonify(card)

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")

        return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=8000)
