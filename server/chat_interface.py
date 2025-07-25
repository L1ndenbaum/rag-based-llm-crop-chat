from fastapi import Request, UploadFile, File, Form, Query, Response as FastAPIResponse, APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from dify_api_python import DifyClient
from typing import List, Tuple, Dict
import os, json, httpx

ALL_PROXY = os.getenv("ALL_PROXY")
USE_PROXY = ALL_PROXY is not None
DIFY_API_KEY = os.getenv('DIFY_API_KEY')
DIFY_BASE_URL = os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1')
PAGE_LIMIT = 20

chat_interface_router = APIRouter()
dify_client = DifyClient(api_key=DIFY_API_KEY, base_url=DIFY_BASE_URL)

def get_httpx_client(**kwargs) -> httpx.AsyncClient:
    proxy = None
    if USE_PROXY and ALL_PROXY:
        if ALL_PROXY.startswith("socks://"):
            proxy = ALL_PROXY.replace("socks://", "socks5://", 1).rstrip("/")
        else:
            proxy = ALL_PROXY.rstrip("/")
    return httpx.AsyncClient(proxy=proxy, **kwargs)


@chat_interface_router.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "").strip()
    username = data.get("username")
    conversation_id = data.get("conversation_id")
    file_ids = data.get("file_ids", [])

    if not message:
        return JSONResponse(status_code=400, content={"error": "消息内容不能为空"})

    files = [
        {
            "type": "image",
            "transfer_method": "local_file",
            "upload_file_id": file_id
        }
        for file_id in file_ids
    ]

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
            message_id = ""
            for chunk in resp:
                data = json.loads(chunk.data)
                if data.get('event') == 'message':
                    delta = data.get("answer")
                    message_id = data.get("message_id")
                    if delta:
                        buffer += delta
                        yield delta
                elif data.get('event') == 'message_end':
                    yield f"[MESSAGE_ID:{message_id}]"
        except Exception as error:
            yield f"[ERROR] AI服务异常: {error}"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@chat_interface_router.get("/api/chat/next_suggest/{message_id}")
async def get_next_problem_suggestion(message_id: str, username: str = Query(...)):
    url = f"{DIFY_BASE_URL}/messages/{message_id}/suggested"
    async with get_httpx_client() as client:
        try:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {DIFY_API_KEY}",
                    "Content-Type": "application/json"
                },
                params={"user": username}
            )
            response.raise_for_status()
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    return JSONResponse(content=response.json().get("data", []))


@chat_interface_router.get("/api/conversations/list/{username}")
async def list_conversations(username: str):
    data = dify_client.get_conversations(user=username, last_id=None, limit=20, pinned=None)["data"]
    conversations = [
        {
            "id": conversation["id"],
            "name": conversation["name"],
            "created_at": conversation["created_at"],
            "updated_at": conversation["updated_at"]
        } for conversation in data
    ]
    conversations.sort(key=lambda x: x["created_at"], reverse=True)
    return JSONResponse(content={"conversations": conversations})


@chat_interface_router.get("/api/conversations/{conversation_id}/history")
async def get_chat_history(conversation_id: str, username: str = Query(...)):
    async def fetch_messages(client: httpx.AsyncClient, first_id=None) -> Tuple[List[Dict], bool]:
        params = {
            "conversation_id": conversation_id,
            "user": username,
            "limit": PAGE_LIMIT
        }
        if first_id:
            params["first_id"] = first_id
        resp = await client.get(
            f"{DIFY_BASE_URL}/messages",
            headers={"Authorization": f"Bearer {DIFY_API_KEY}"},
            params=params
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"], data.get("has_more", False)

    async with get_httpx_client() as client:
        all_msgs = []
        first_id = None
        while True:
            messages_data, has_more = await fetch_messages(client, first_id)
            if not messages_data:
                break
            all_msgs = messages_data + all_msgs
            if not has_more:
                break
            first_id = messages_data[0]["id"]

    all_message_history = [
        {
            "query": message.get("query"),
            "answer": message.get("answer"),
            "message_files": message.get("message_files"),
            "created_at": message.get("created_at")
        } for message in all_msgs
    ]
    return JSONResponse(content=all_message_history)


@chat_interface_router.delete("/api/conversations/{conversation_id}/delete")
async def delete_conversation(conversation_id: str, username: str = Query(...)):
    async with get_httpx_client() as client:
        resp = await client.request(
            method='DELETE',
            url=f"{DIFY_BASE_URL}/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {DIFY_API_KEY}"},
            json={"user": username}
        )
    if resp.status_code == 204:
        return JSONResponse(content={"message": "对话已删除", "conversation_id": conversation_id})
    else:
        return JSONResponse(status_code=404, content={"error": "对话不存在"})


@chat_interface_router.post("/api/file/upload")
async def upload_files  (files: List[UploadFile] = File(...), username: str = Form(...)):
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}"}
    url = f"{DIFY_BASE_URL}/files/upload"
    file_ids = []
    async with get_httpx_client() as client:
        try:
            for file in files:
                content = await file.read()
                mime = file.content_type
                file_tuple = (file.filename, content, mime)
                response = await client.post(
                    url,
                    headers=headers,
                    files={"file": file_tuple},
                    data={"user": username}
                )
                response.raise_for_status()
                file_ids.append(response.json().get("id"))
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    return JSONResponse(content={"file_ids": file_ids})
