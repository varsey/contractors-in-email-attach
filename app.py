import gc
import logging
import traceback

from flask import Flask, jsonify, request

from src.modules.parsers.message import (
    INNMessageProcessor, 
    DateRangeMessageProcessor, 
    MessageNotFoundError,
    # Backward compatibility aliases
    MessageProcessor, 
    MessageProcessor2,
)
from src.config.cfg import Config
from src.logger.Logger import log

app = Flask(__name__)
cfg = Config()
prc = MessageProcessor(**cfg.creds, db_path = 'message_ids.db')
prc2 = MessageProcessor2(**cfg.creds2, db_path = 'message_ids.db')

logging.getLogger('pymorphy2.opencorpora_dict.wrapper').setLevel(logging.ERROR)


@app.route("/")
def route_status():
    return "This is contractor parser"


@app.route("/api/parsing/")
def contractor_parser_parameter():
    email_id = request.args.get('mid')
    try:
        card = prc.process_email_by_id(message_id=email_id)
        gc.collect()
        return jsonify(card)
    except MessageNotFoundError as e:
        log.warning(f"Message not found: {e}")
        return jsonify({"error": "message-id not found"}), 404
    except Exception as e:
        log.error(f"Error processing mid {email_id}: {e}")
        log.error(traceback.format_exc())
        return jsonify({"error": str(e), "status": "failed"}), 500


@app.route("/api/parsing/v2/")
def contractor_parser_parameter_v2():
    email_id = request.args.get('mid')
    try:
        card = prc2.process_email_by_id_v2(message_id=email_id)
        # card = prc2.process_all_emails_v2()
        gc.collect()
        return jsonify(card)
    except MessageNotFoundError as e:
        log.warning(f"Message not found (v2): {e}")
        return jsonify({"error": "message-id not found"}), 404
    except Exception as e:
        log.error(f"Error processing mid {email_id} (v2): {e}")
        log.error(traceback.format_exc())
        return jsonify({"error": str(e), "status": "failed"}), 500


@app.route("/sample/")
def parse_random():
    try:
        card = prc.process_random_id()
        gc.collect()
        return jsonify(card)
    except Exception as e:
        log.error(f"Error processing random id: {e}")
        log.error(traceback.format_exc())
        return jsonify({"error": str(e), "status": "failed"}), 500



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8001)
