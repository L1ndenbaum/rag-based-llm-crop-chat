from flask import jsonify, send_from_directory, request, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Users
import os

user_control_interface_bp = Blueprint('user_control_interface_bp', __name__)

@user_control_interface_bp.route('/api/user/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'message': '用户名和密码为必填项'}), 400

    if Users.query.filter_by(username=username).first():
        return jsonify({'message': '用户已存在'}), 400

    hashed_password = generate_password_hash(password)

    new_user = Users(username=username, password=hashed_password) # type: ignore
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': '用户注册成功！'}), 200


@user_control_interface_bp.route('/api/user/login', methods=['POST'])
def login():
    """
    登录检查,接收前端的POST JSON,检查用户信息
    Returns:
        用户不存在 -> 返回message JSON和状态码400\n
        用户存在且密码正确 -> 返回message username JSON和状态码200\n
        用户存在且密码错误 -> 返回message JSON和状态码401
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': '未提供用户名和密码'}), 400

    user = Users.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return jsonify({'message': '登录成功'}), 200
    else:
        return jsonify({'message': '密码错误'}), 401

@user_control_interface_bp.route('/api/user/user_info/<string:username>', methods=['GET'])
def get_user_info(username):
    """
    查询用户信息接口 不返回密码 仅返回用户名、年龄和头像URL
    Returs:
        用户不存在 -> error message JSON和状态码404
        用户存在 -> 用户信息 JSON 其中的url是一个接口访问地址 对此url发起http请求返回用户头像
    """
    user = Users.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': '用户不存在'}), 404

    return jsonify({
                    'code':200,
                    'message': '获取用户信息成功',
                    'data':{'username': user.username}
                    }), 200

@user_control_interface_bp.route('/auth/login')
def login_index():
    return send_from_directory('./static/out/auth', 'login.html')

@user_control_interface_bp.route('/auth/register')
def register_index():
    return send_from_directory('./static/out/auth', 'register.html')