from app import app, db, SHANGHAI_TZ
from flask import send_from_directory
from face import *
import os

# 人脸图片与特征存储目录
os.makedirs("FaceImage", exist_ok=True)
os.makedirs("FaceFeature", exist_ok=True)
os.makedirs("temp_images", exist_ok=True)

# 人脸录入审核状态
ENROLLMENT_PENDING = 0
ENROLLMENT_APPROVED = 1
ENROLLMENT_REJECTED = 2

# 图片存储目录
IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), "temp_images")


# 图片显示
@app.route("/temp_images/<filename>")
def get_image(filename):
    """提供图片静态文件服务"""
    try:
        return send_from_directory(IMAGE_FOLDER, filename)
    except FileNotFoundError:
        return {"error": "Image not found"}, 404


# 获取待审核的人脸录入列表
@app.route("/admin/face-enrollments/pending", methods=["GET"])
@jwt_required()
def get_pending_face_enrollments():
    """获取待审核的人脸录入申请列表"""
    try:
        # 验证管理员权限
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != "管理员":
            return jsonify(ok=False, msg="权限不足"), 403
        # 获取待审核的申请
        pending_enrollments = FaceEnrollment.query.filter_by(
            status=ENROLLMENT_PENDING
        ).all()
        result = []
        for enrollment in pending_enrollments:
            user = User.query.get(enrollment.user_id)
            result.append(
                {
                    "id": enrollment.id,
                    "user_id": enrollment.user_id,
                    "user_name": user.name if user else "未知用户",
                    "user_account": user.account if user else "未知账号",
                    "image_path": enrollment.image_path,
                    "created_time": enrollment.created_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if enrollment.created_time
                    else "",
                }
            )
        return jsonify(ok=True, enrollments=result)
    except Exception as e:
        app.logger.error(f"获取待审核列表失败: {str(e)}")
        return jsonify(ok=False, msg="获取数据失败"), 500


# 获取所有人脸录入记录（包括已审核的）
@app.route("/admin/face-enrollments/all", methods=["GET"])
@jwt_required()
def get_all_face_enrollments():
    """获取所有人脸录入记录"""
    try:
        # 验证管理员权限
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != "管理员":
            return jsonify(ok=False, msg="权限不足"), 403
        # 获取所有人脸录入记录，按创建时间倒序排列
        enrollments = FaceEnrollment.query.order_by(
            FaceEnrollment.created_time.desc()
        ).all()
        result = []
        for enrollment in enrollments:
            user = User.query.get(enrollment.user_id)
            status_text = {
                ENROLLMENT_PENDING: "待审核",
                ENROLLMENT_APPROVED: "已通过",
                ENROLLMENT_REJECTED: "已拒绝",
            }.get(enrollment.status, "未知")
            result.append(
                {
                    "id": enrollment.id,
                    "user_id": enrollment.user_id,
                    "user_name": user.name if user else "未知用户",
                    "user_account": user.account if user else "未知账号",
                    "image_path": enrollment.image_path,
                    "status": enrollment.status,
                    "status_text": status_text,
                    "created_time": enrollment.created_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if enrollment.created_time
                    else "",
                    "reviewed_time": enrollment.reviewed_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if enrollment.reviewed_time
                    else "",
                    "review_comment": enrollment.review_comment or "",
                }
            )
        return jsonify(ok=True, enrollments=result)
    except Exception as e:
        app.logger.error(f"获取人脸录入记录失败: {str(e)}")
        return jsonify(ok=False, msg="获取数据失败"), 500


# 审核人脸录入申请
@app.route("/admin/face-enrollments/<int:enrollment_id>/review", methods=["POST"])
@jwt_required()
def review_face_enrollment(enrollment_id):
    """审核人脸录入申请"""
    try:
        # 验证管理员权限
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != "管理员":
            return jsonify(ok=False, msg="权限不足"), 403
        # 获取审核申请
        enrollment = FaceEnrollment.query.get(enrollment_id)
        if not enrollment:
            return jsonify(ok=False, msg="申请不存在"), 404
        # 获取审核数据
        data = request.get_json()
        if not data:
            return jsonify(ok=False, msg="请求数据无效"), 400
        approve = data.get("approve", False)
        comment = data.get("comment", "")

        if approve:
            # 审核通过
            try:
                # 提取人脸特征
                feature = extract_feature(enrollment.image_path)
                if feature is None:
                    return jsonify(
                        ok=False,
                        msg="无法从图片中提取人脸特征，请确保照片清晰且包含正面人脸",
                    ), 400
                # 保存特征文件
                feature_path = os.path.join("FaceFeature", f"{enrollment.user_id}.npy")
                np.save(feature_path, feature)
                # 保存图片文件
                image_path = os.path.join("FaceImage", f"{enrollment.user_id}.jpg")
                with (
                    open(enrollment.image_path, "rb") as src,
                    open(image_path, "wb") as dst,
                ):
                    dst.write(src.read())
                # 删除temp_images里面的文件
                os.remove(enrollment.image_path)
                # 检查是否已存在人脸记录，如果存在则更新，否则创建
                existing_face = Face.query.filter_by(user_id=enrollment.user_id).first()
                if existing_face:
                    existing_face.image_path = feature_path
                    existing_face.rec_time = datetime.now(SHANGHAI_TZ)
                    existing_face.result = "已更新"
                else:
                    # 创建人脸记录
                    new_face = Face(
                        user_id=enrollment.user_id,
                        image_path=feature_path,
                        rec_time=datetime.now(SHANGHAI_TZ),
                        result="已录入",
                    )
                    db.session.add(new_face)
                # 更新审核记录
                enrollment.status = ENROLLMENT_APPROVED
                enrollment.reviewed_time = datetime.now(SHANGHAI_TZ)
                enrollment.review_comment = comment
                db.session.commit()
                return jsonify(ok=True, msg="审核通过，人脸录入成功")
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"人脸特征提取失败: {str(e)}")
                return jsonify(
                    ok=False, msg="人脸特征提取失败，请确保照片清晰且包含正面人脸"
                ), 400
        else:
            # 审核拒绝
            enrollment.status = ENROLLMENT_REJECTED
            enrollment.reviewed_time = datetime.now(SHANGHAI_TZ)
            enrollment.review_comment = comment
            # 删除上传的图片文件
            try:
                if os.path.exists(enrollment.image_path):
                    os.remove(enrollment.image_path)
            except Exception as e:
                app.logger.error(f"删除图片文件失败: {str(e)}")
            db.session.commit()
            return jsonify(ok=True, msg="审核已拒绝")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"审核操作失败: {str(e)}")
        return jsonify(ok=False, msg="审核操作失败"), 500
