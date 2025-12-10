import gc
import logging
import traceback

from flask import Flask, jsonify, request

from src.modules.parsers.message import MessageProcessor, MessageProcessor2
from src.config.cfg import Config
from src.logger.Logger import log

app = Flask(__name__)
cfg = Config()
prc = MessageProcessor(**cfg.creds)
prc2 = MessageProcessor2(**cfg.creds2)

logging.getLogger('pymorphy2.opencorpora_dict.wrapper').setLevel(logging.ERROR)


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all uncaught exceptions and log full traceback"""
    log.error("Internal Server Error occurred:")
    log.error(traceback.format_exc())
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'The server encountered an internal error and was unable to complete your request.'
    }), 500


@app.route("/")
def route_status():
    return "This is contractor parser"


@app.route("/api/parsing/")
def contractor_parser_parameter():
    email_id = request.args.get('mid')
    card = prc.process_email_by_id(message_id=email_id)
    gc.collect()
    return jsonify(card)

@app.route("/api/parsing/v2/")
def contractor_parser_parameter_v2():
    email_id = request.args.get('mid')
    card = prc2.process_email_by_id_v2(message_id=email_id)
    # card = prc2.process_all_emails_v2()
    gc.collect()
    return jsonify(card)

@app.route("/sample/")
def parse_random():
    card = prc.process_random_id()
    gc.collect()
    return jsonify(card)



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8001)
