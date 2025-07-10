from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from dify_api_python import DifyClient
import os, logging, uuid, io
import waitress, json, requests
from datetime import datetime
from models import db
from user_control_interface import user_control_interface_bp
from chat_interface import chat_interface_bp
from db_config import SQLALCHEMY_DATABASE_URI

STATIC_FOLDER_PATH = "..'/../client/out"
logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='out')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.register_blueprint(user_control_interface_bp)
app.register_blueprint(chat_interface_bp)
db.init_app(app)
CORS(app)
logging.basicConfig(level=logging.INFO)

@app.route('/_next/static/<path:path>')
def next_static(path):
    return send_from_directory('./static/out/_next/static', path)

@app.route('/')
def index():
    return send_from_directory('./static/out', 'index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'chatbot-backend'
    })

@app.errorhandler(404)
def not_found(e): return jsonify({'error': '接口不存在'}), 404
@app.errorhandler(500)
def err(e): return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    waitress.serve(app, host='0.0.0.0', port=8080)
