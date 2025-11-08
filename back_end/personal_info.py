from flask_jwt_extended import jwt_required, get_jwt_identity
from app import app, db
from flask import request, jsonify, send_from_directory
import os
from models import User, Face, FaceEnrollment
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

# 个人信息头像存储文件夹
os.makedirs("Profile", exist_ok=True)

@app.route('/user/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    try:
        current_user_id = get_jwt_identity()
        # 检查文件是否存在
        if 'avatar' not in request.files:
            return jsonify(ok=False, msg="没有选择文件"), 400
        file = request.files['avatar']
        if file.filename == '':
            return jsonify(ok=False, msg="没有选择文件"), 400
        # 创建 profile 目录
        profile_dir = 'Profile'
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        # 生成文件名：user_id.jpg
        filename = f"{current_user_id}.jpg"
        filepath = os.path.join(profile_dir, filename)
        # 保存文件
        file.save(filepath)
        return jsonify(ok=True, msg="头像上传成功", avatar=filename), 200
    except Exception as e:
        print(f"头像上传错误: {e}")
        return jsonify({'ok': False, 'message': '上传失败，请重试'}), 500


@app.route('/profile/avatar_pre')
@jwt_required()
def get_avatar():
    current_user_id = get_jwt_identity()
    filename = f"{current_user_id}.jpg"
    # 检查文件是否存在
    file_path = os.path.join('Profile', filename)
    if os.path.exists(file_path):
        # 文件存在，返回用户头像
        return send_from_directory('Profile', filename)
    else:
        # 文件不存在，返回默认头像
        return send_from_directory('Profile', 'temp.jpg')


@app.route('/user/profile/detailed', methods=['GET'])
@jwt_required()
def get_detailed_profile():
    """获取用户详细信息"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=current_user_id).first()
        if not user:
            return jsonify(ok=False, msg="用户不存在"), 404
        user_data = {
            'account': user.account,
            'name': user.name,
            'role': user.role,
            'security_question_1': user.security_question_1,
            'security_question_2': user.security_question_2,
            'security_question_3': user.security_question_3,
        }
        return jsonify(ok=True, profile=user_data), 200
    except Exception as e:
        print(f"获取用户详细信息错误: {e}")
        return jsonify(ok=False, msg="获取用户信息失败"), 500


@app.route('/user/profile/update', methods=['POST'])
@jwt_required()
def update_profile():
    """更新用户信息"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=current_user_id).first()
        if not user:
            return jsonify(ok=False, msg="用户不存在"), 404
        data = request.get_json()
        # 更新基本信息
        if 'name' in data:
            user.name = data['name']
        # 更新密保问题
        if 'security_question_1' in data:
            user.security_question_1 = data['security_question_1']
        if 'security_question_2' in data:
            user.security_question_2 = data['security_question_2']
        if 'security_question_3' in data:
            user.security_question_3 = data['security_question_3']
        db.session.commit()
        return jsonify(ok=True, msg="个人信息更新成功"), 200
    except Exception as e:
        db.session.rollback()
        print(f"更新用户信息错误: {e}")
        return jsonify(ok=False, msg="更新个人信息失败"), 500


@app.route('/user/update_password', methods=['POST'])
@jwt_required()
def update_password():
    """修改密码"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=current_user_id).first()
        if not user:
            return jsonify(ok=False, msg="用户不存在"), 404
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        if not old_password or not new_password:
            return jsonify(ok=False, msg="请输入原密码和新密码"), 400
        # 验证原密码
        if not bcrypt.check_password_hash(user.password, old_password):
            return jsonify(ok=False, msg="原密码错误"), 400
        # 更新密码
        user.password =  hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        db.session.commit()
        return jsonify(ok=True, msg="密码修改成功"), 200
    except Exception as e:
        db.session.rollback()
        print(f"修改密码错误: {e}")
        return jsonify(ok=False, msg="密码修改失败"), 500


@app.route('/user/update_security_answer', methods=['POST'])
@jwt_required()
def update_security_answer():
    """修改密保答案"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.filter_by(user_id=current_user_id).first()

        if not user:
            return jsonify(ok=False, msg="用户不存在"), 404

        data = request.get_json()
        question_index = data.get('question_index')  # 1, 2, 3
        answer = data.get('answer')

        if not question_index or not answer:
            return jsonify(ok=False, msg="请选择问题和输入答案"), 400

        # 更新对应的密保答案
        if question_index == 1:
            user.security_answer_1 = bcrypt.generate_password_hash(answer).decode("utf-8")
        elif question_index == 2:
            user.security_answer_2 = bcrypt.generate_password_hash(answer).decode("utf-8")
        elif question_index == 3:
            user.security_answer_3 = bcrypt.generate_password_hash(answer).decode("utf-8")
        else:
            return jsonify(ok=False, msg="无效的问题索引"), 400

        db.session.commit()

        return jsonify(ok=True, msg="密保答案修改成功"), 200

    except Exception as e:
        db.session.rollback()
        print(f"修改密保答案错误: {e}")
        return jsonify(ok=False, msg="密保答案修改失败"), 500


@app.route('/user/face_status', methods=['GET'])
@jwt_required()
def get_face_status():
    """获取用户人脸状态"""
    try:
        current_user_id = get_jwt_identity()
        # 检查是否有已录入的人脸
        face_record = Face.query.filter_by(user_id=current_user_id).first()
        if face_record and face_record.result == '已录入':
          return jsonify(ok=True, status="已录入", has_face=True), 200
        # 检查是否有待审核的人脸录入申请
        pending_enrollment = FaceEnrollment.query.filter_by(
            user_id=current_user_id,
            status=0  # ENROLLMENT_PENDING
        ).first()
        if pending_enrollment:
            return jsonify(ok=True, status="待审核", has_face=False), 200
        # 既没有录入也没有待审核
        return jsonify(ok=True, status="未录入", has_face=False), 200
    except Exception as e:
        print(f"获取人脸状态错误: {e}")
        return jsonify(ok=False, msg="获取人脸状态失败"), 500


@app.route('/user/face_re_enroll', methods=['POST'])
@jwt_required()
def re_enroll_face():
    """申请重新录入人脸 - 将face里面的状态改为未录入"""
    try:
        current_user_id = get_jwt_identity()
        existing_face = Face.query.filter_by(user_id=current_user_id).first()
        if existing_face:
            existing_face.result = "未录入"
            db.session.commit()
            return jsonify(ok=True, msg="申请成功"), 200
        else:
            return jsonify(ok=False, msg="申请失败"), 500
    except Exception as e:
        print(f"申请重新录入人脸错误: {e}")
        return jsonify(ok=False, msg="申请失败"), 500
