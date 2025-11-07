from flask import request, jsonify
from app import app, db, SHANGHAI_TZ
from models import User, Attendance, Face, FaceEnrollment
from flask_jwt_extended import jwt_required, get_jwt_identity
import face_recognition as fr
import numpy as np
import os
import uuid
from datetime import datetime
from sqlalchemy import func

# 人脸图片与特征存储目录
os.makedirs("FaceImage", exist_ok=True)
os.makedirs("FaceFeature", exist_ok=True)
os.makedirs("temp_images", exist_ok=True)

# 人脸识别打卡（上/下班）
@app.route("/face/<action>", methods=["POST"])  # action = checkin | checkout
@jwt_required()
def face_action(action):
    """
    人脸识别打卡接口
    action: checkin (上班打卡) | checkout (下班打卡)
    """
    try:
        # 参数验证
        if action not in ("checkin", "checkout"):
            return jsonify(ok=False, msg="无效的打卡类型"), 400
        if "file" not in request.files:
            return jsonify(ok=False, msg="请上传人脸照片"), 400
        if "user_id" not in request.form:
            return jsonify(ok=False, msg="用户信息缺失"), 400
        # 获取用户ID并验证
        try:
            user_id = int(request.form.get("user_id"))
        except (ValueError, TypeError):
            return jsonify(ok=False, msg="无效的用户ID"), 400
        # 验证JWT令牌中的用户ID与提交的用户ID是否一致
        current_user_id = get_jwt_identity()  # 从JWT中获取的用户ID
        user_id = int(request.form["user_id"])  # 从表单中获取的用户ID
        #print(f"JWT user_id: {current_user_id}, type: {type(current_user_id)}")
        #print(f"Form user_id: {user_id}, type: {type(user_id)}")
        if int(current_user_id) != user_id:
            return jsonify(ok=False, msg="用户身份验证失败"), 403
        # 验证用户是否存在且已录入人脸
        user = User.query.get(user_id)
        if not user:
            return jsonify(ok=False, msg="用户不存在"), 404
        face = Face.query.filter_by(user_id=user_id).first()
        if not face:
            return jsonify(ok=False, msg="请先录入人脸信息"), 404

        # 处理上传的图片
        file = request.files["file"]
        if file.filename == '':
            return jsonify(ok=False, msg="未选择文件"), 400
        # 保存临时图片并提取特征
        img_path = save_image(file)
        try:
            unknown = extract_feature(img_path)
        except Exception as e:
            os.remove(img_path)
            if "未检测到人脸" in str(e):
                return jsonify(ok=False, msg="未检测到人脸，请确保面部清晰可见"), 400
            else:
                app.logger.error(f"人脸特征提取失败: {str(e)}")
                return jsonify(ok=False, msg="人脸特征提取失败"), 500
        # 加载已存储的人脸特征并进行比对
        try:
            known = np.load(face.image_path)
        except Exception as e:
            os.remove(img_path)
            app.logger.error(f"人脸数据加载失败: {str(e)}")
            return jsonify(ok=False, msg="人脸数据加载失败，请重新录入"), 500
        # 计算特征距离
        dist = np.linalg.norm(known - unknown)
        os.remove(img_path)  # 删除临时文件
        # 人脸匹配阈值
        if dist > 0.4:
            return jsonify(ok=False, msg="人脸不匹配，请重试"), 403
        # 获取当前时间
        current_time = datetime.now(SHANGHAI_TZ)
        today = current_time.date()
        # 上班打卡逻辑
        if action == "checkin":
            return handle_checkin(user_id, current_time, today, user)
        # 下班打卡逻辑
        else:
            return handle_checkout(user_id, current_time, today, user)
    except Exception as e:
        # 记录错误日志
        app.logger.error(f"打卡处理异常: {str(e)}")
        return jsonify(ok=False, msg="系统异常，请稍后重试"), 500

def handle_checkin(user_id, current_time, today, user):
    """处理上班打卡"""
    # 检查今日是否已打卡
    exist = Attendance.query.filter(
        Attendance.user_id == user_id,
        func.date(Attendance.clock_in_time) == today
    ).first()
    if exist:
        return jsonify(ok=False, msg="今日已签到，请勿重复打卡"), 400
    # 检查打卡时间是否在允许范围内 (8:00 - 12:00)
    if current_time.hour < 8:
        return jsonify(ok=False, msg="上班打卡时间为 8:00 - 12:00"), 400
    if current_time.hour >= 12:
        return jsonify(ok=False, msg="上班打卡时间已过，请联系管理员"), 400
    # 判断是否迟到 (9:00 之后算迟到)
    if current_time.hour > 9 or (current_time.hour == 9 and current_time.minute > 0):
        status = "迟到"
    else:
        status = "正常"
    # 创建打卡记录
    att = Attendance(
        user_id=user_id,
        clock_in_time=current_time,
        status=status
    )
    db.session.add(att)
    db.session.commit()
    return jsonify(
        ok=True,
        username=user.name,
        time=current_time.strftime("%H:%M:%S"),
        status=status,
        message=f"{user.name}，上班打卡成功！"
    )

def handle_checkout(user_id, current_time, today, user):
    """处理下班打卡"""
    # 检查今日是否已签退
    already_checked_out = Attendance.query.filter(
        Attendance.user_id == user_id,
        func.date(Attendance.clock_in_time) == today,
        Attendance.clock_out_time.isnot(None),
    ).first()
    if already_checked_out:
        return jsonify(ok=False, msg="今日已签退，请勿重复打卡"), 400
    # 查找今日的上班记录
    att = Attendance.query.filter(
        Attendance.user_id == user_id,
        func.date(Attendance.clock_in_time) == today,
        Attendance.clock_out_time.is_(None),
    ).first()
    if not att:
        return jsonify(ok=False, msg="今日未签到，无法签退"), 404
    # 检查下班打卡时间是否在允许范围内 (17:00 - 21:00)
    if current_time.hour < 17:
        return jsonify(ok=False, msg="下班打卡时间为 17:00 - 21:00"), 400
    # 设置签退时间
    att.clock_out_time = current_time
    # 更新状态（如果早于18:00算早退）
    if current_time.hour < 18:
        if att.status == "正常":
            att.status = "早退"
        elif att.status == "迟到":
            att.status = "迟到+早退"
    # 18:00之后正常签退，保持原有状态
    db.session.commit()
    return jsonify(
        ok=True,
        username=user.name,
        time=current_time.strftime("%H:%M:%S"),
        status=att.status,
        message=f"{user.name}，下班打卡成功！"
    )

def save_image(file):
    """保存上传的图片文件"""
    # 创建临时目录（如果不存在）
    temp_dir = "temp_images"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    # 生成唯一文件名
    filename = f"face_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(temp_dir, filename)
    # 保存文件
    file.save(filepath)
    return filepath


def extract_feature(img_path):
    """
    使用face_recognition库从图片中提取人脸特征
    """
    try:
        # 加载图片
        image = fr.load_image_file(img_path)
        # 检测人脸位置
        face_locations = fr.face_locations(image)
        if not face_locations:
            raise Exception("未检测到人脸")
        # 提取人脸特征
        face_encodings = fr.face_encodings(image, face_locations)
        if not face_encodings:
            raise Exception("无法提取人脸特征")
        # 返回第一张人脸的特征
        return face_encodings[0]
    except Exception as e:
        raise e

# 人脸录入
# 人脸录入审核状态
ENROLLMENT_PENDING = 0
ENROLLMENT_APPROVED = 1
ENROLLMENT_REJECTED = 2


# 人脸录入（需要审核）
@app.post("/face/enroll")
@jwt_required()
def face_enroll():
    """
    人脸录入接口（需要审核）
    """
    try:
        # 参数验证
        if "file" not in request.files:
            return jsonify(ok=False, msg="请上传人脸照片"), 400
        if "user_id" not in request.form:
            return jsonify(ok=False, msg="用户信息缺失"), 400
        # 获取用户ID并验证
        try:
            user_id = int(request.form["user_id"])
        except (ValueError, TypeError):
            return jsonify(ok=False, msg="无效的用户ID"), 400
        # 验证JWT令牌中的用户ID与提交的用户ID是否一致
        current_user_id = get_jwt_identity()
        if int(current_user_id) != user_id:
            return jsonify(ok=False, msg="用户身份验证失败"), 403
        # 验证用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify(ok=False, msg="用户不存在"), 404
        # 检查是否已有人脸记录（无论是否审核通过）
        existing_face = Face.query.filter_by(user_id=user_id).first()
        if existing_face:
            return jsonify(
                ok=False,
                msg="已录入过人脸，无法重复录入"
            )
        # 检查是否有待审核的录入申请
        pending_enrollment = FaceEnrollment.query.filter_by(
            user_id=user_id,
            status=ENROLLMENT_PENDING
        ).first()
        if pending_enrollment:
            return jsonify(
                ok=False,
                msg="您已有人脸录入申请正在审核中，请等待审核结果"
            )
        # 处理上传的图片
        file = request.files["file"]
        if file.filename == '':
            return jsonify(ok=False, msg="未选择文件"), 400
        # 保存临时图片
        try:
            img_path = save_temp_image(file)
        except Exception as e:
            app.logger.error(f"图片保存失败: {str(e)}")
            return jsonify(ok=False, msg="图片保存失败"), 500
        # 看照片是否能正常编码，不保存
        try:
            unknown = extract_feature(img_path)
        except Exception as e:
            os.remove(img_path)
            if "未检测到人脸" in str(e):
                return jsonify(ok=False, msg="未检测到人脸，请确保面部清晰可见"), 400
            else:
                app.logger.error(f"人脸特征提取失败: {str(e)}")
                return jsonify(ok=False, msg="人脸特征提取失败"), 500
        # 创建待审核记录
        try:
            new_enrollment = FaceEnrollment(
                user_id=user_id,
                image_path=img_path,
                status=ENROLLMENT_PENDING,
                created_time=datetime.now(SHANGHAI_TZ)
            )
            db.session.add(new_enrollment)
            db.session.commit()
        except Exception as e:
            # 删除已保存的临时图片
            if os.path.exists(img_path):
                os.remove(img_path)
            app.logger.error(f"审核记录创建失败: {str(e)}")
            return jsonify(ok=False, msg="申请提交失败"), 500
        return jsonify(
            ok=True,
            msg="录入信息已发送给管理员审核，请等待审核通过",
            enrollment_id=new_enrollment.id
        )
    except Exception as e:
        # 全局异常处理
        app.logger.error(f"人脸录入申请异常: {str(e)}")
        return jsonify(ok=False, msg="系统异常，请稍后重试"), 500

def save_temp_image(file):
    """保存临时图片"""
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"enrollment_{uuid.uuid4().hex}.{ext}"
    path = os.path.join("temp_images", filename)
    file.save(path)
    return path
