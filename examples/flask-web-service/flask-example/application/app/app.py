#!/usr/bin/env python


from __future__ import unicode_literals, print_function

import json
import logging
import os
from StringIO import StringIO
from logging.handlers import RotatingFileHandler

import cv2
from PIL import Image
from flask import Flask, make_response, request, send_from_directory, jsonify, render_template, send_file


def configure_logging():
    namespace = {}
    namespace['base_dir'] = os.path.abspath(os.path.dirname(__file__))
    namespace['logfile'] = os.path.join(namespace['base_dir'], "flask-example.log")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    rotating_file_handler = RotatingFileHandler(namespace['logfile'], maxBytes=10000, backupCount=20)
    rotating_file_handler.setLevel(logging.DEBUG)
    console_stream_handler = logging.StreamHandler()
    console_stream_handler.setLevel(logging.DEBUG if namespace.get('debug') else logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_stream_handler.setFormatter(formatter)
    rotating_file_handler.setFormatter(formatter)
    logger.addHandler(console_stream_handler)
    logger.addHandler(rotating_file_handler)
    return logger, rotating_file_handler, console_stream_handler


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


app = Flask(__name__, static_url_path='')
app.config.update(
        DEBUG=True,
)

# Generate a secret random key for the session
app.secret_key = os.urandom(24)


def _format_json_response(result):
    json_content = json.dumps(result)
    response = make_response(json_content)
    response.headers["Content-Type"] = "application/json"
    return response


def _handle_api():
    return {"data": "Hello, World!"}


@app.errorhandler(403)
def not_authorized():
    message = {
        'status': 403,
        'message': 'Not authorized: ' + request.url,
    }
    response = jsonify(message)
    response.status_code = 403
    return response


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    response = jsonify(message)
    response.status_code = 404
    return response


@app.route('/api', methods=['GET'])
def api():
    result = _handle_api()
    return _format_json_response(result)


@app.route('/static/<path:path>')
def send_web(path):
    return send_from_directory('static', path)


@app.route('/')
def index(name=None):
    return render_template('index.html', name=name)


@app.route('/canny')
def canny():
    # adapted from https://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_imgproc/py_canny/py_canny.html#canny
    img = cv2.imread('static/img/ship.jpg', 0)
    edges = cv2.Canny(img, 100, 200)
    im = Image.fromarray(edges)
    img2 = StringIO()
    im.save(img2, format="png")
    img2.seek(0)
    return send_file(img2, mimetype='image/png')


@app.errorhandler(500)
def internal_error(exception):
    app.logger.error(exception)
    return render_template('500.html'), 500


@app.errorhandler(400)
def internal_error(exception):
    app.logger.exception("Error: %s", exception)
    return render_template('400.html'), 500


if __name__ == '__main__':
    logger, file_handler, stream_handler = configure_logging()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    app.run(
            host="0.0.0.0",
            port=int("8001"),
    )
