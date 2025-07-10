from flask import request, jsonify, stream_with_context, Blueprint, Response
from dify_api_python import DifyClient
import os, uuid, io
import json, requests
from datetime import datetime

chat_interface_bp = Blueprint('chat_interface_bp', __name__)
DIFY_API_KEY = os.getenv('DIFY_API_KEY')
DIFY_BASE_URL = os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1')
dify_client = DifyClient(api_key=DIFY_API_KEY, base_url=DIFY_BASE_URL)

conversations = {}
@chat_interface_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    username = data.get('username')
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
                user=username,
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

@chat_interface_bp.route('/api/conversations/list/<string:username>', methods=['GET'])
def list_conversations(username):
    print(username)
    conversations:list[dict] = dify_client.get_conversations(user=username, last_id=None, limit=20, pinned=None)['data']
    conversations = [
        {
            'id': conversation['id'],
            'name': conversation['name'],
            'created_at': conversation['created_at'],
            'updated_at': conversation['updated_at'],
        } for conversation in conversations
    ]
    conversations.sort(key=lambda x: x['created_at'], reverse=True)
    print(len(conversations))
    return jsonify({'conversations': conversations, 'total': len(conversations)})

# @chat_interface_bp.route('/api/conversations/<string:chat_id>', methods=['GET'])
# def get_chat_history(chat_id):

#     return jsonify()


@chat_interface_bp.route('/api/conversations/<string:conversation_id>', methods=['GET', 'DELETE'])
def manage_conv(conversation_id):
    if conversation_id not in conversations:
        return jsonify({'error': '对话不存在'}), 404
    if request.method == 'GET':
        return jsonify({'conversation': conversations[conversation_id]})
    else:
        del conversations[conversation_id]
        return jsonify({'message': '对话已删除', 'conversation_id': conversation_id})

@chat_interface_bp.route('/api/file/upload', methods=["POST"])
def upload_files():
    # 获取多个文件
    uploaded_files = request.files.getlist('files')
    username = request.form.get('username')
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
            response = requests.post(url, files={"file": (bio.name, bio, mime)}, data={'user' : username}, headers=headers)
            response.raise_for_status()
            response = response.json()
            file_ids.append(response.get('id'))
    except Exception as error:
        print(error)

    return jsonify({'file_ids': file_ids})

