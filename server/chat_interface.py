from flask import request, jsonify, stream_with_context, Blueprint, Response
from dify_api_python import DifyClient
import os, uuid, io
from typing import Tuple, List, Dict
import json, requests
from datetime import datetime

chat_interface_bp = Blueprint('chat_interface_bp', __name__)
DIFY_API_KEY = os.getenv('DIFY_API_KEY')
DIFY_BASE_URL = os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1')
PAGE_LIMIT = 20
dify_client = DifyClient(api_key=DIFY_API_KEY, base_url=DIFY_BASE_URL)

conversations = {}
@chat_interface_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    username = data.get('username')
    conversation_id = data.get('conversation_id')
    file_ids = data.get('file_ids') or None
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
    
    print(conv)
    def generate():
        try:
            resp = dify_client.chat_message(
                query=message,
                user=username,
                inputs={},
                files=files,
                conversation_id=conversation_id or "",
                stream=True
            )
            buffer = ""
            for chunk in resp:
                data = json.loads(chunk.data)
                if data.get('event') == 'message':
                    delta = data.get("answer")
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
    conversations:list[dict] = dify_client.get_conversations(user=username, last_id=None, limit=20, pinned=None)['data']
    conversations = [
        {
            'id': conversation['id'],
            'name': conversation['name'],
            'created_at': conversation['created_at'],
            'updated_at': conversation['updated_at'],
        } for conversation in conversations
    ]
    print(conversations)
    conversations.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify({'conversations': conversations, 'total': len(conversations)})

@chat_interface_bp.route('/api/conversations/<string:conversation_id>/history', methods=['GET'])
def get_chat_history(conversation_id):
    username = request.args.get('username')

    def fetch_messages(first_id=None) -> Tuple[List[Dict], bool]:
        params = {
                    "conversation_id": conversation_id,
                    "user": username,
                    "limit": PAGE_LIMIT
                 }
        if first_id:
            params["first_id"] = first_id

        resp = requests.get(url=f"{DIFY_BASE_URL}/messages", 
                            headers={"Authorization": f"Bearer {DIFY_API_KEY}"}, 
                            params=params)
        resp.raise_for_status()
        data = resp.json()

        return data['data'], data.get("has_more", False)

    def load_all_history() -> List[Dict]:
        all_msgs = []
        first_id = None
        while True:
            messages_data, has_more = fetch_messages(first_id)
            if not messages_data:
                break

            all_msgs = messages_data + all_msgs  # 前插，按时间正序合并
            if not has_more:
                break

            # 下一次分页从最旧的消息开始，其 id 作为 new first_id
            first_id = messages_data[0]["id"]

        return all_msgs

    all_message_history = load_all_history()
    #print(f"Total messages fetched: {len(history)}")
    all_message_history = [{
                            'query' : message.get('query'),
                            'answer' : message.get('answer'),
                            'message_files': message.get('message_files')
                            } for message in all_message_history]

    return jsonify(all_message_history)

@chat_interface_bp.route('/api/conversations/<string:conversation_id>/delete', methods=['DELETE'])
def delete_conversation(conversation_id: str):
    username = request.args.get('username')
    resp = requests.delete(url=f"{DIFY_BASE_URL}/conversations/{conversation_id}", 
                           headers={"Authorization": f"Bearer {DIFY_API_KEY}"},
                           json={'user':username})

    if resp.status_code == 204:
        return jsonify({'message': '对话已删除', 'conversation_id': conversation_id})
    else:
        return jsonify({'error': '对话不存在'}), 404

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

