import requests, os, uuid
from flask import request, jsonify, stream_with_context, Blueprint, Response
from dify_api_python import DifyClient
import os, uuid, io
from typing import Tuple, List, Dict
import json, requests
from datetime import datetime
APIKEY = os.getenv("DIFY_API_KEY") 

# url = "https://api.dify.ai/v1/messages"
# headers = {"Authorization": f"Bearer {APIKEY}"}
# params = {
#   "conversation_id": "487c3971-1166-4809-9b7c-a68bb2ebc688",
#   "user": "ShiningFinger",
#   "limit": 20
# }
# chat_interface_bp = Blueprint('chat_interface_bp', __name__)
# DIFY_API_KEY = os.getenv('DIFY_API_KEY')
# DIFY_BASE_URL = os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1')
# PAGE_LIMIT = 20
# dify_client = DifyClient(api_key=DIFY_API_KEY, base_url=DIFY_BASE_URL)

# conversation_id='487c3971-1166-4809-9b7c-a68bb2ebc688'
# result = dify_client.delete_conversation(conversation_id, user="ShiningFinger")
resp = requests.delete(url=f"https://api.dify.ai/v1/conversations/19a6e7fb-d3d1-415d-83c2-86d5e85f228f", 
                        headers={'Authorization': f"Bearer {APIKEY}",
                                'Content-Type': 'application/json'},
                        json={'user':'ShiningFinger'})

print(resp.status_code)