from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from models import Users
from db_config import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static", "out")
user_control_router = APIRouter()

# 注册接口
@user_control_router.post("/api/user/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码为必填项")

    existing_user = db.query(Users).filter_by(username=username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户已存在")

    hashed_password = generate_password_hash(password)
    new_user = Users(username=username, password=hashed_password)  # type: ignore
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return JSONResponse(content={"message": "用户注册成功！"}, status_code=200)

# 登录接口
@user_control_router.post("/api/user/login")
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    data = await request.json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        raise HTTPException(status_code=400, detail="未提供用户名和密码")

    user = db.query(Users).filter_by(username=username).first()
    if user and check_password_hash(user.password, password): # type: ignore
        return JSONResponse(content={"message": "登录成功"}, status_code=200)
    else:
        raise HTTPException(status_code=401, detail="密码错误")

# 查询用户信息接口
@user_control_router.get("/api/user/user_info/{username}")
def get_user_info(username: str, db: Session = Depends(get_db)):
    user = db.query(Users).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "code": 200,
        "message": "获取用户信息成功",
        "data": {
            "username": user.username,
        }
    }

@user_control_router.get('/auth/login')
async def serve_login():
    return FileResponse(os.path.join(static_dir, 'auth', "login.html"))

@user_control_router.get('/auth/login.txt')
async def serve_login_txt():
    return FileResponse(os.path.join(static_dir, 'auth', "login.txt"))

@user_control_router.get('/auth/register')
async def serve_register():
    return FileResponse(os.path.join(static_dir, 'auth', "register.html"))

@user_control_router.get('/auth/register.txt')
async def serve_register_txt():
    return FileResponse(os.path.join(static_dir, 'auth', "register.txt"))