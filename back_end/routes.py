from flask import request, jsonify
from app import app, db
from models import User, Attendance
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# 用户注册
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(name=data['name'], account=data['account'], password=hashed_password, role=data['role'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

# 用户登录
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(account=data['account']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.user_id)
        return jsonify({'access_token': access_token}), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

# 用户打卡
@app.route('/attendance', methods=['POST'])
def attendance():
    data = request.get_json()
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    new_attendance = Attendance(user_id=user.user_id, clock_in_time=data['clock_in_time'], status='正常')
    db.session.add(new_attendance)
    db.session.commit()
    
    return jsonify({'message': 'Attendance recorded successfully'}), 201
