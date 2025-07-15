from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from user_control_interface import user_control_router
from chat_interface import chat_interface_router
from datetime import datetime
import os, uvicorn, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static", "out")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://101.43.131.195:4040/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user_control_router)
app.include_router(chat_interface_router)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/{full_path:path}")
async def serve_html(full_path: str):
    file_path = os.path.join(static_dir, full_path)
    if os.path.exists(file_path) and file_path.endswith(".html"):
        return FileResponse(file_path)
    else:
        # fallback to index.html 或返回 404
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Page not found"}

# 健康检查接口
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "chatbot-backend"
    }

# 404 异常处理
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"error": "接口不存在"})

# 500 异常处理
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(status_code=500, content={"error": "服务器内部错误"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)