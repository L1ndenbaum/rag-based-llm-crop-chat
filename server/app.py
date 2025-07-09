from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from dify_api_python import DifyClient
import os, logging, uuid, io
import waitress, json, requests
from datetime import datetime
from PIL import Image

STATIC_FOLDER_PATH = "..'/../client/out"
DIFY_API_KEY = os.getenv('DIFY_API_KEY')
DIFY_BASE_URL = os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='out')
CORS(app)
dify_client = DifyClient(api_key=DIFY_API_KEY, base_url=DIFY_BASE_URL)
conversations = {}

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

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    conversation_id = data.get('conversation_id') or str(uuid.uuid4())
    file_ids = data.get('file_ids') or None
    print(file_ids)
    files = []  
    if file_ids is not None:
        for file_id in file_ids:
            files.append(
                            {
                                'type' : 'image',
                                'transfer_method' : 'local_file',
                                'upload_file_id' : file_id
                            }
                        )
    if not message:
        return jsonify({'error': '消息内容不能为空'}), 400

    conv = conversations.setdefault(conversation_id, 
                                    {
                                        'id': conversation_id,
                                        'created_at': datetime.now().isoformat(),
                                        'messages': []
                                    })
    conv['messages'].append({
                             'role': 'user', 
                             'content': message, 
                             'timestamp': datetime.now().isoformat()
                            })
    
    def generate():
        try:
            resp = dify_client.chat_message(
                query=message,
                user="TestUser",
                inputs={},
                files=files,
                stream=True
            )
            buffer = ""
            for chunk in resp:
                data = json.loads(chunk.data)
                if data.get('event') == 'message':
                    delta = data.get("answer")
                    print(delta)
                    if delta:
                        buffer += delta
                        yield delta

            # 完成后整理 AI 全文
            conv['messages'].append(
                {
                    'role': 'assistant', 
                    'content': buffer, 
                    'timestamp': datetime.now().isoformat()
                }
            )
        except Exception as error:
            yield f"[ERROR] AI服务异常: {error}"

    # 返回 chunked 流式响应
    return Response(stream_with_context(generate()),
                    content_type='text/plain; charset=utf-8')

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    conversations:list[dict] = dify_client.get_conversations(user="TestUser", last_id=None, limit=20, pinned=None)['data']
    conversations = [
        {
            'id': conversation['id'],
            'name': conversation['name'],
            'created_at': conversation['created_at'],
            'updated_at': conversation['updated_at'],
        } for conversation in conversations
    ]
    conversations.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify({'conversations': conversations, 'total': len(conversations)})

@app.route('/api/conversations/<int:conversation_id>', methods=['GET', 'DELETE'])
def manage_conv(conversation_id):
    if conversation_id not in conversations:
        return jsonify({'error': '对话不存在'}), 404
    if request.method == 'GET':
        return jsonify({'conversation': conversations[conversation_id]})
    else:
        del conversations[conversation_id]
        return jsonify({'message': '对话已删除', 'conversation_id': conversation_id})

@app.route('/api/file/upload', methods=["POST"])
def upload_files():
    # 获取多个文件
    uploaded_files = request.files.getlist('files')  # 'files' 与前端的name保持一致
    print(uploaded_files)
    file_ids = []
    headers = {
            "Authorization": f"Bearer {DIFY_API_KEY}",
        }
    url = 'https://api.dify.ai/v1/files/upload'
    try:
        for file in uploaded_files:
            content = file.read()
            bio = io.BytesIO(content)
            bio.name = file.filename
            mime = file.mimetype
            response = requests.post(url, files={"file": (bio.name, bio, mime)}, data={'user' : 'TestUser'}, headers=headers)
            response.raise_for_status()
            response = response.json()
            file_ids.append(response.get('id'))
    except Exception as error:
        print(error)

    return jsonify({'file_ids': file_ids})

@app.errorhandler(404)
def not_found(e): return jsonify({'error': '接口不存在'}), 404
@app.errorhandler(500)
def err(e): return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    waitress.serve(app, host='0.0.0.0', port=8080)
    #app.run(debug=True, host='0.0.0.0', port=8080)
