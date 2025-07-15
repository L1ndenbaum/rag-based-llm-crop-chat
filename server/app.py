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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user_control_router)
app.include_router(chat_interface_router)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

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