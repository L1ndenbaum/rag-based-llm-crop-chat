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
static_dir = os.path.join(BASE_DIR, "static")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://101.43.131.195:4040", "http://h4886472.natappfree.cc"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_control_router)
app.include_router(chat_interface_router)

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "chatbot-backend"
    }


subsystems = {
    # subsystem_name : build_path
    "qa": "qa_out",
}
def create_serve_subsystem(path):
    async def serve():
        return FileResponse(os.path.join(path, "index.html"))
    return serve

# 为每个子系统挂载静态资源
for name, path in subsystems.items():
    subsystem_path = os.path.join(static_dir, "subsystem", path)
    if not os.path.isdir(subsystem_path):
        raise Exception(f"Directory {subsystem_path} does not exist!")

    # /subsystem/out_name -> static_files
    app.mount(f"/subsystem/{path}", StaticFiles(directory=subsystem_path, html=True), name=f"{name}_all")
    app.add_api_route(f"/subsystem/{name}", create_serve_subsystem(path), methods=["GET"])


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
