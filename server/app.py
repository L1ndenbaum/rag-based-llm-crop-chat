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
    allow_origins=["http://101.43.131.195:4040"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_control_router)
app.include_router(chat_interface_router)

app.mount("/_next", StaticFiles(directory=os.path.join(static_dir, "_next")), name="next")
app.mount("/images", StaticFiles(directory=os.path.join(static_dir, "images")), name="images")

@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join(static_dir, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return JSONResponse({"error": "favicon not found"}, status_code=404)

# 健康检查接口
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "chatbot-backend"
    }

# catch-all 路由：处理其他路径，返回对应 HTML 或 index.html fallback
@app.get("/{full_path:path}")
async def serve_html(full_path: str):
    # 排除 Next.js 和静态资源目录路径
    if full_path.startswith(("_next/", "images/", "static/")):
        return JSONResponse({"error": "Static resource not found"}, status_code=404)

    # 支持直接访问 HTML 文件或目录对应的 HTML 文件（如 /auth/login → auth/login.html）
    file_path = os.path.join(static_dir, full_path)
    if os.path.exists(file_path) and file_path.endswith(".html"):
        return FileResponse(file_path)

    html_fallback = file_path + ".html"
    if os.path.exists(html_fallback):
        return FileResponse(html_fallback)

    # fallback 到首页 index.html
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    # 404 页面
    error_404 = os.path.join(static_dir, "404.html")
    if os.path.exists(error_404):
        return FileResponse(error_404, status_code=404)

    return JSONResponse({"error": "Page not found"}, status_code=404)

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
