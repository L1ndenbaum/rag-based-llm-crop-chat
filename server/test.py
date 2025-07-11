import requests, os, uuid
from flask import request, jsonify, stream_with_context, Blueprint, Response
from dify_api_python import DifyClient
import os, uuid, io
from typing import Tuple, List, Dict
import json, requests
from datetime import datetime
# APIKEY = os.getenv("DIFY_API_KEY") 
# DIFY_API_KEY = os.getenv('DIFY_API_KEY')
# DIFY_BASE_URL = os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1')
# PAGE_LIMIT = 20
# def get_chat_history(conversation_id):
#     username = 'TestUser1'

#     def fetch_messages(first_id=None) -> Tuple[List[Dict], bool]:
#         params = {
#                     "conversation_id": conversation_id,
#                     "user": username,
#                     "limit": PAGE_LIMIT
#                  }
#         if first_id:
#             params["first_id"] = first_id

#         resp = requests.get(url=f"{DIFY_BASE_URL}/messages", 
#                             headers={"Authorization": f"Bearer {DIFY_API_KEY}"}, 
#                             params=params)
#         resp.raise_for_status()
#         data = resp.json()

#         return data['data'], data.get("has_more", False)

#     def load_all_history() -> List[Dict]:
#         all_msgs = []
#         first_id = None
#         while True:
#             messages_data, has_more = fetch_messages(first_id)
#             if not messages_data:
#                 break

#             all_msgs = messages_data + all_msgs  # 前插，按时间正序合并
#             if not has_more:
#                 break

#             # 下一次分页从最旧的消息开始，其 id 作为 new first_id
#             first_id = messages_data[0]["id"]

#         return all_msgs

#     all_message_history = load_all_history()
#     #print(f"Total messages fetched: {len(history)}")
# #     all_message_history = [{
# #                             'query' : message.get('query'),
# #                             'answer' : message.get('answer')
# #                             } for message in all_message_history]

#     return all_message_history

# print(get_chat_history('3951b250-56cc-48ae-a361-77877c95348c'))

from datetime import datetime, timezone

ts = 1752141634
dt_utc = datetime.fromtimestamp(ts, timezone.utc)
print(dt_utc.strftime('%Y-%m-%d'))
# 输出示例：2025-08-09
print(datetime.now().isoformat())

a = {'text':2}
a.setdefault('text', 3)
print(a)