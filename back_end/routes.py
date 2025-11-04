from flask import request, jsonify
from app import app, db, SHANGHAI_TZ
from models import User, Attendance, Face
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from datetime import datetime, date
from sqlalchemy import func, and_, extract
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import face_recognition as fr
import numpy as np
import os
from models import Absence
from datetime import timedelta
import uuid
import re

bcrypt = Bcrypt(app)
jwt = JWTManager(app)


# JWT错误处理
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"message": "Token has expired"}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"message": "Invalid token"}), 422


@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({"message": "Authorization header is expected"}), 401


# 用户注册
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # 检查工号格式是否为五位小写英文+三位数字
    account_pattern = r"^[a-z]{5}\d{3}$"
    if not re.match(account_pattern, data["account"]):
        return (
            jsonify({"message": "工号格式错误，请使用五位小写英文+三位数字的格式"}),
            400,
        )

    # 检查账号是否已存在
    existing_user = User.query.filter_by(account=data["account"]).first()
    if existing_user:
        return jsonify({"message": "账号已存在，请使用其他账号"}), 400

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    new_user = User(
        name=data["name"],
        account=data["account"],
        password=hashed_password,
        role=data["role"],
    )

    db.session.add(new_user)
    db.session.commit()

    # 创建token并返回用户信息
    access_token = create_access_token(identity=str(new_user.user_id))
    return (
        jsonify(
            {
                "access_token": access_token,
                "message": "User created successfully",
                "user": {
                    "user_id": new_user.user_id,
                    "name": new_user.name,
                    "account": new_user.account,
                    "role": new_user.role,
                },
            }
        ),
        201,
    )


# 用户登录
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(account=data["account"]).first()

    if user and bcrypt.check_password_hash(user.password, data["password"]):
        # 创建token时使用字符串作为identity
        access_token = create_access_token(identity=str(user.user_id))
        return (
            jsonify(
                {
                    "access_token": access_token,
                    "user": {
                        "user_id": user.user_id,
                        "name": user.name,
                        "account": user.account,
                        "role": user.role,
                    },
                }
            ),
            200,
        )

    return jsonify({"message": "Invalid credentials"}), 401


# 用户打卡
@app.route("/attendance", methods=["POST"])
@jwt_required()
def attendance():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    # 判断打卡类型（上班/下班）
    attendance_type = data.get("type", "clock_in")  # clock_in 或 clock_out
    current_time = datetime.now(SHANGHAI_TZ)
    today = current_time.date()

    if attendance_type == "clock_in":
        # 检查是否已签到
        existing_checkin = Attendance.query.filter(
            and_(
                Attendance.user_id == current_user_id,
                func.date(Attendance.clock_in_time) == today,
            )
        ).first()

        if existing_checkin:
            return jsonify({"message": "今日已签到，请勿重复签到"}), 400

        # 上班打卡
        status = "正常"
        # 判断是否迟到（假设9:00为上班时间）
        if current_time.hour > 9 or (
            current_time.hour == 9 and current_time.minute > 0
        ):
            status = "迟到"

        new_attendance = Attendance(
            user_id=current_user_id, clock_in_time=current_time, status=status
        )
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({"message": "Clock-in recorded successfully"}), 201
    else:
        # 下班打卡 - 更新现有记录
        today_attendance = Attendance.query.filter(
            and_(
                Attendance.user_id == current_user_id,
                func.date(Attendance.clock_in_time) == today,
                Attendance.clock_out_time.is_(None),
            )
        ).first()

        if not today_attendance:
            # 检查是否已签退
            already_checked_out = Attendance.query.filter(
                and_(
                    Attendance.user_id == current_user_id,
                    func.date(Attendance.clock_in_time) == today,
                    Attendance.clock_out_time.isnot(None),
                )
            ).first()

            if already_checked_out:
                return jsonify({"message": "今日已签退，请勿重复签退"}), 400
            else:
                return jsonify({"message": "今日未签到，无法签退"}), 404

        today_attendance.clock_out_time = current_time
        # 判断是否早退（假设18:00为下班时间）
        if current_time.hour < 18:
            today_attendance.status = "早退"
        elif current_time.hour < 19:
            # 18:00-18:59之间的签退显示为正常
            today_attendance.status = "正常"
        else:
            # 19:00及之后的签退显示为加班
            today_attendance.status = "加班"

        db.session.commit()
        return jsonify({"message": "Clock-out recorded successfully"}), 200


# 获取用户信息
@app.route("/user/profile", methods=["GET"])
@jwt_required()
def get_user_profile():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    return (
        jsonify(
            {
                "user_id": user.user_id,
                "name": user.name,
                "account": user.account,
                "role": user.role,
            }
        ),
        200,
    )


# 若已签到但未签退且非请假，记为"未签退"
def mark_unclocked_out_employees():
    """标记未签退员工"""
    today = datetime.now(SHANGHAI_TZ).date()

    # 查询所有员工，实时标记未签退
    employees = User.query.filter_by(role="员工").all()
    for u in employees:
        approved_leave = Absence.query.filter(
            Absence.user_id == u.user_id,
            Absence.status == 2,
            func.date(Absence.start_time) <= today,
            func.date(Absence.end_time) >= today,
        ).first()
        if approved_leave:
            continue
        att = Attendance.query.filter(
            Attendance.user_id == u.user_id,
            func.date(Attendance.clock_in_time) == today,
        ).first()
        if att and att.clock_out_time is None and att.status != "请假":
            att.status = "未签退"
    db.session.commit()


@app.route("/attendance/personal", methods=["GET"])
@jwt_required()
def get_personal_attendance():
    current_user_id = int(get_jwt_identity())
    mark_unclocked_out_employees()

    now = datetime.now(SHANGHAI_TZ)
    today = date.today()
    current_month = now.month
    current_year = now.year

    # 总出勤天数
    total_days = (
        db.session.query(func.count(Attendance.attendance_id))
        .filter(
            and_(
                Attendance.user_id == current_user_id,
                extract("month", Attendance.clock_in_time) == current_month,
                extract("year", Attendance.clock_in_time) == current_year,
                func.date(Attendance.clock_in_time) <= today,
            )
        )
        .scalar()
        or 0
    )

    # 迟到次数
    late_count = (
        db.session.query(func.count(Attendance.attendance_id))
        .filter(
            and_(
                Attendance.user_id == current_user_id,
                extract("month", Attendance.clock_in_time) == current_month,
                extract("year", Attendance.clock_in_time) == current_year,
                Attendance.status == "迟到",
                func.date(Attendance.clock_in_time) <= today,
            )
        )
        .scalar()
        or 0
    )

    # 早退次数
    early_leave_count = (
        db.session.query(func.count(Attendance.attendance_id))
        .filter(
            and_(
                Attendance.user_id == current_user_id,
                extract("month", Attendance.clock_in_time) == current_month,
                extract("year", Attendance.clock_in_time) == current_year,
                Attendance.status == "早退",
                func.date(Attendance.clock_in_time) <= today,
            )
        )
        .scalar()
        or 0
    )

    # 正常次数
    normal_count = (
        db.session.query(func.count(Attendance.attendance_id))
        .filter(
            and_(
                Attendance.user_id == current_user_id,
                extract("month", Attendance.clock_in_time) == current_month,
                extract("year", Attendance.clock_in_time) == current_year,
                Attendance.status == "正常",
                func.date(Attendance.clock_in_time) <= today,
            )
        )
        .scalar()
        or 0
    )

    # 最近记录
    recent_records = (
        Attendance.query.filter(
            and_(
                Attendance.user_id == current_user_id,
                func.date(Attendance.clock_in_time) <= today,
            )
        )
        .order_by(Attendance.clock_in_time.desc())
        .limit(10)
        .all()
    )

    # 将处于通过的请假区间内的记录标记为“请假”，并隐藏打卡时间
    approved_leaves = Absence.query.filter(
        and_(Absence.user_id == current_user_id, Absence.status == 2)
    ).all()

    def in_leave(dt):
        if not dt:
            return False
        for lv in approved_leaves:
            if lv.start_time <= dt <= lv.end_time:
                return True
        return False

    def covers_workday(day):
        if not day:
            return False
        work_start = datetime(day.year, day.month, day.day, 8, 0, 0)
        work_end = datetime(day.year, day.month, day.day, 18, 0, 0)
        for lv in approved_leaves:
            if lv.start_time <= work_start and lv.end_time >= work_end:
                return True
        return False

    records_list = []
    for record in recent_records:
        is_leave = in_leave(record.clock_in_time) or in_leave(record.clock_out_time)
        day = (
            record.clock_in_time.date()
            if record.clock_in_time
            else (record.clock_out_time.date() if record.clock_out_time else None)
        )
        if covers_workday(day):
            is_leave = True
        records_list.append(
            {
                "attendance_id": record.attendance_id,
                "clock_in_time": (
                    record.clock_in_time.strftime("%Y-%m-%d %H:%M:%S")
                    if record.clock_in_time
                    else None
                ),
                "clock_out_time": (
                    record.clock_out_time.strftime("%Y-%m-%d %H:%M:%S")
                    if record.clock_out_time
                    else None
                ),
                "status": ("请假" if is_leave else record.status),
            }
        )

    # 动态补充今日未出勤的虚拟记录（18:00后、当天无打卡、且非请假；不写入数据库）
    on_leave_today = (
        Absence.query.filter(
            and_(
                Absence.user_id == current_user_id,
                Absence.status == 2,
                func.date(Absence.start_time) <= today,
                func.date(Absence.end_time) >= today,
            )
        ).first()
        is not None
    )
    has_any_att_today = (
        db.session.query(func.count(Attendance.attendance_id))
        .filter(
            and_(
                Attendance.user_id == current_user_id,
                func.date(Attendance.clock_in_time) == today,
            )
        )
        .scalar()
        or 0
    )
    if has_any_att_today == 0 and not on_leave_today:
        anchor_time = datetime(today.year, today.month, today.day, 0, 0, 0)
        records_list.insert(
            0,
            {
                "attendance_id": f'virtual-{today.strftime("%Y%m%d")}',
                "clock_in_time": anchor_time.strftime("%Y-%m-%d %H:%M:%S"),
                "clock_out_time": None,
                "status": "未出勤",
            },
        )

    return (
        jsonify(
            {
                "monthly_stats": {
                    "total_days": total_days,
                    "late_count": late_count,
                    "early_leave_count": early_leave_count,
                    "normal_count": normal_count,
                    "should_attend": 22,  # 假设每月应出勤22天
                },
                "recent_records": records_list,
            }
        ),
        200,
    )


# 管理员查看当天考勤总体情况
@app.route("/admin/attendance/daily", methods=["GET"])
@jwt_required()
def get_daily_attendance_overview():
    mark_unclocked_out_employees()
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    # 检查是否为管理员
    if not user or user.role != "管理员":
        return jsonify({"message": "Access denied. Admin role required."}), 403

    today = date.today()

    # 当天考勤统计 - 使用分别查询的方式
    actual_attendance = (
        db.session.query(func.count(func.distinct(Attendance.user_id)))
        .filter(
            and_(
                func.date(Attendance.clock_in_time) == today,
                Attendance.status.notin_(["请假", "缺勤"]),
            )
        )
        .scalar()
        or 0
    )

    late_count = (
        db.session.query(func.count(Attendance.attendance_id))
        .filter(
            and_(
                func.date(Attendance.clock_in_time) == today,
                Attendance.status == "迟到",
            )
        )
        .scalar()
        or 0
    )

    early_leave_count = (
        db.session.query(func.count(Attendance.attendance_id))
        .filter(
            and_(
                func.date(Attendance.clock_in_time) == today,
                Attendance.status == "早退",
            )
        )
        .scalar()
        or 0
    )

    normal_count = (
        db.session.query(func.count(Attendance.attendance_id))
        .filter(
            and_(
                func.date(Attendance.clock_in_time) == today,
                Attendance.status == "正常",
            )
        )
        .scalar()
        or 0
    )

    # 总员工数
    total_employees = User.query.filter_by(role="员工").count()

    return (
        jsonify(
            {
                "date": today.strftime("%Y-%m-%d"),
                "should_attend": total_employees,
                "actual_attendance": actual_attendance,
                "late_count": late_count,
                "early_leave_count": early_leave_count,
                "normal_count": normal_count,
            }
        ),
        200,
    )


# 管理员查看所有员工考勤情况
@app.route("/admin/attendance/employees", methods=["GET"])
@jwt_required()
def get_employees_attendance():
    # 应用未签退标记规则
    mark_unclocked_out_employees()
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    # 检查是否为管理员
    if not user or user.role != "管理员":
        return jsonify({"message": "Access denied. Admin role required."}), 403

    # 获取排序参数
    sort_by = request.args.get(
        "sort_by", "name"
    )  # name, late_count, early_leave_count, normal_count, leave_count
    sort_order = request.args.get("sort_order", "asc")  # asc, desc

    now = datetime.now(SHANGHAI_TZ)
    current_month = now.month
    current_year = now.year
    today = date.today()

    # 获取所有员工
    employees = User.query.filter_by(role="员工").all()
    employees_list = []

    for user in employees:
        # 是否当天请假
        on_leave_today = (
            Absence.query.filter(
                and_(
                    Absence.user_id == user.user_id,
                    Absence.status == 2,
                    func.date(Absence.start_time) <= today,
                    func.date(Absence.end_time) >= today,
                )
            ).first()
            is not None
        )

        # 当天是否存在任何考勤记录
        has_any_att_today = (
            db.session.query(func.count(Attendance.attendance_id))
            .filter(
                and_(
                    Attendance.user_id == user.user_id,
                    func.date(Attendance.clock_in_time) == today,
                )
            )
            .scalar()
            or 0
        )

        # 今日出勤（排除请假、缺勤）
        today_attendance = (
            db.session.query(func.count(Attendance.attendance_id))
            .filter(
                and_(
                    Attendance.user_id == user.user_id,
                    func.date(Attendance.clock_in_time) == today,
                    Attendance.status.notin_(["请假", "缺勤"]),
                )
            )
            .scalar()
            or 0
        )

        # 18:00后，无任何打卡且非请假 → 明确标记为缺勤（实时显示）
        is_absent_today = has_any_att_today == 0 and not on_leave_today

        # 本月总出勤（不计未来日期）
        monthly_total = (
            db.session.query(func.count(Attendance.attendance_id))
            .filter(
                and_(
                    Attendance.user_id == user.user_id,
                    extract("month", Attendance.clock_in_time) == current_month,
                    extract("year", Attendance.clock_in_time) == current_year,
                    func.date(Attendance.clock_in_time) <= today,
                )
            )
            .scalar()
            or 0
        )

        # 本月迟到次数（不计未来日期）
        monthly_late = (
            db.session.query(func.count(Attendance.attendance_id))
            .filter(
                and_(
                    Attendance.user_id == user.user_id,
                    extract("month", Attendance.clock_in_time) == current_month,
                    extract("year", Attendance.clock_in_time) == current_year,
                    Attendance.status == "迟到",
                    func.date(Attendance.clock_in_time) <= today,
                )
            )
            .scalar()
            or 0
        )

        # 本月早退次数（不计未来日期）
        monthly_early_leave = (
            db.session.query(func.count(Attendance.attendance_id))
            .filter(
                and_(
                    Attendance.user_id == user.user_id,
                    extract("month", Attendance.clock_in_time) == current_month,
                    extract("year", Attendance.clock_in_time) == current_year,
                    Attendance.status == "早退",
                    func.date(Attendance.clock_in_time) <= today,
                )
            )
            .scalar()
            or 0
        )

        # 本月正常次数（不计未来日期）
        monthly_normal = (
            db.session.query(func.count(Attendance.attendance_id))
            .filter(
                and_(
                    Attendance.user_id == user.user_id,
                    extract("month", Attendance.clock_in_time) == current_month,
                    extract("year", Attendance.clock_in_time) == current_year,
                    Attendance.status == "正常",
                    func.date(Attendance.clock_in_time) <= today,
                )
            )
            .scalar()
            or 0
        )

        # 本月请假次数（不计未来日期，统计通过的请假申请次数）
        monthly_leave = (
            db.session.query(func.count(Absence.id))
            .filter(
                and_(
                    Absence.user_id == user.user_id,
                    Absence.status == 2,
                    extract("month", Absence.start_time) == current_month,
                    extract("year", Absence.start_time) == current_year,
                    func.date(Absence.start_time) <= today,
                )
            )
            .scalar()
            or 0
        )

        # 本月未签退次数（不计未来日期）
        monthly_not_checked_out = (
            db.session.query(func.count(Attendance.attendance_id))
            .filter(
                and_(
                    Attendance.user_id == user.user_id,
                    extract("month", Attendance.clock_in_time) == current_month,
                    extract("year", Attendance.clock_in_time) == current_year,
                    Attendance.status == "未签退",
                    func.date(Attendance.clock_in_time) <= today,
                )
            )
            .scalar()
            or 0
        )

        employees_list.append(
            {
                "user_id": user.user_id,
                "name": user.name,
                "account": user.account,
                "today_attendance": today_attendance,
                "is_absent_today": is_absent_today,
                "on_leave_today": on_leave_today,
                "monthly_stats": {
                    "total_days": monthly_total,
                    "late_count": monthly_late,
                    "early_leave_count": monthly_early_leave,
                    "normal_count": monthly_normal,
                    "leave_count": monthly_leave,
                    "not_checked_out_count": monthly_not_checked_out,
                    "should_attend": 22,
                },
            }
        )

    if sort_by == "late_count":
        employees_list.sort(
            key=lambda x: x["monthly_stats"]["late_count"],
            reverse=(sort_order == "desc"),
        )
    elif sort_by == "early_leave_count":
        employees_list.sort(
            key=lambda x: x["monthly_stats"]["early_leave_count"],
            reverse=(sort_order == "desc"),
        )
    elif sort_by == "normal_count":
        employees_list.sort(
            key=lambda x: x["monthly_stats"]["normal_count"],
            reverse=(sort_order == "desc"),
        )
    elif sort_by == "leave_count":
        employees_list.sort(
            key=lambda x: x["monthly_stats"]["leave_count"],
            reverse=(sort_order == "desc"),
        )
    elif sort_by == "not_checked_out_count":
        employees_list.sort(
            key=lambda x: x["monthly_stats"]["not_checked_out_count"],
            reverse=(sort_order == "desc"),
        )
    else:  # 默认按姓名排序
        employees_list.sort(key=lambda x: x["name"], reverse=(sort_order == "desc"))

    return (
        jsonify(
            {"employees": employees_list, "sort_by": sort_by, "sort_order": sort_order}
        ),
        200,
    )


# 人脸图片与特征存储目录
os.makedirs("FaceImage", exist_ok=True)
os.makedirs("FaceFeature", exist_ok=True)


# 保存上传的人脸图片
def save_image(file):
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join("FaceImage", name)
    file.save(path)
    return path


# 从图片中提取人脸特征
def extract_feature(image_path):
    img = fr.load_image_file(image_path)
    encodings = fr.face_encodings(img)
    if not encodings:
        raise IndexError("No face")
    return encodings[0]


# 人脸录入（注册后调用，不要求登录态）
@app.post("/face/enroll")
def face_enroll():
    if "file" not in request.files or "user_id" not in request.form:
        return jsonify(ok=False, msg="缺少文件或user_id"), 400
    user_id = int(request.form["user_id"])
    exist = Face.query.filter_by(user_id=user_id).first()
    if exist:
        return jsonify(ok=True, alreadyExists=True, msg="该人脸已录入过！")
    img_path = save_image(request.files["file"])
    try:
        feature = extract_feature(img_path)
    except IndexError:
        os.remove(img_path)
        return jsonify(ok=False, msg="未检测到人脸"), 400

    feature_path = os.path.join("FaceFeature", f"{user_id}.npy")
    np.save(feature_path, feature)
    new_face = Face(
        user_id=user_id,
        image_path=feature_path,
        rec_time=datetime.now(SHANGHAI_TZ),
        result="已录入",
    )
    db.session.add(new_face)
    db.session.commit()
    return jsonify(ok=True, alreadyExists=False, msg="人脸录入成功！")


# 人脸识别打卡（上/下班）
@app.post("/face/<action>")  # action = checkin | checkout
def face_action(action):
    if action not in ("checkin", "checkout"):
        return jsonify(ok=False, msg="非法动作"), 404
    if "file" not in request.files or "user_id" not in request.form:
        return jsonify(ok=False, msg="缺少文件或user_id"), 400

    user_id = int(request.form.get("user_id"))
    face = Face.query.filter_by(user_id=user_id).first()
    if not face:
        return jsonify(ok=False, msg="人脸未录入，请先录入"), 404

    img_path = save_image(request.files["file"])
    try:
        unknown = extract_feature(img_path)
    except IndexError:
        os.remove(img_path)
        return jsonify(ok=False, msg="未检测到人脸"), 400

    known = np.load(face.image_path)
    dist = np.linalg.norm(known - unknown)
    os.remove(img_path)
    if dist > 0.4:
        return jsonify(ok=False, msg="人脸不匹配"), 403

    current_time = datetime.now(SHANGHAI_TZ)
    today = current_time.date()

    if action == "checkin":
        exist = Attendance.query.filter(
            Attendance.user_id == user_id, func.date(Attendance.clock_in_time) == today
        ).first()
        if exist:
            return jsonify(ok=False, msg="今日已签到，请勿重复签到"), 400
        # 移除时间限制，任何时间都可以签到
        att = Attendance(user_id=user_id, clock_in_time=current_time, status="正常")
        db.session.add(att)
    else:  
        already_checked_out = Attendance.query.filter(
            Attendance.user_id == user_id,
            func.date(Attendance.clock_in_time) == today,
            Attendance.clock_out_time.isnot(None),
        ).first()
        if already_checked_out:
            return jsonify(ok=False, msg="今日已签退，请勿重复签退"), 400
        att = Attendance.query.filter(
            Attendance.user_id == user_id,
            func.date(Attendance.clock_in_time) == today,
            Attendance.clock_out_time.is_(None),
        ).first()
        if not att:
            return jsonify(ok=False, msg="今日未签到，无法签退"), 404
        att.clock_out_time = current_time

    db.session.commit()
    user = User.query.get(user_id)
    return jsonify(ok=True, username=user.name, time=current_time.strftime("%H:%M:%S"))


# 请假申请：用户提交
@app.route("/absence", methods=["POST"])
@jwt_required()
def create_absence():
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        start_time_str = data.get("start_time")
        end_time_str = data.get("end_time")
        reason = (data.get("reason") or "").strip()
        absence_type = data.get("absence_type", 0)  # 默认值为0（病假）
        if not start_time_str or not end_time_str or not reason:
            return jsonify(message="参数不完整"), 400

        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except Exception:
            return jsonify(message="时间格式不正确"), 400
        if end_time <= start_time:
            return jsonify(message="结束时间必须大于开始时间"), 400
        absence = Absence(
            user_id=current_user_id,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
            status=0,  # 未读
            absence_type=absence_type  # 保存请假类型
        )
        db.session.add(absence)
        db.session.commit()
        return jsonify(message="请假申请已提交", id=absence.id), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f"服务器错误: {str(e)}"), 500


# 个人请假申请列表
@app.route("/absence/personal", methods=["GET"])
@jwt_required()
def get_personal_absences():
    current_user_id = int(get_jwt_identity())
    absences = (
        Absence.query.filter_by(user_id=current_user_id)
        .order_by(Absence.start_time.desc())
        .all()
    )
    res = [
        {
            "id": a.id,
            "user_id": a.user_id,
            "start_time": (
                a.start_time.strftime("%Y-%m-%d %H:%M:%S") if a.start_time else None
            ),
            "end_time": (
                a.end_time.strftime("%Y-%m-%d %H:%M:%S") if a.end_time else None
            ),
            "reason": a.reason,
            "status": a.status,
            "absence_type": a.absence_type  # 添加请假类型
        }
        for a in absences
    ]
    return jsonify(absences=res), 200


# 管理员查看请假申请列表（processed=true 查看已处理，否则查看未读）
@app.route("/admin/absence", methods=["GET"])
@jwt_required()
def admin_list_absences():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role != "管理员":
        return jsonify(message="Access denied. Admin role required."), 403
    processed = request.args.get("processed", "false").lower() == "true"
    query = Absence.query
    if processed:
        query = query.filter(Absence.status.in_([1, 2]))
    else:
        query = query.filter(Absence.status == 0)
    absences = query.order_by(Absence.start_time.desc()).all()
    res = [
        {
            "id": a.id,
            "name": (
                User.query.get(a.user_id).name if User.query.get(a.user_id) else None
            ),
            "account": (
                User.query.get(a.user_id).account if User.query.get(a.user_id) else None
            ),
            "user_id": a.user_id,
            "start_time": (
                a.start_time.strftime("%Y-%m-%d %H:%M:%S") if a.start_time else None
            ),
            "end_time": (
                a.end_time.strftime("%Y-%m-%d %H:%M:%S") if a.end_time else None
            ),
            "reason": a.reason,
            "status": a.status,
            "absence_type": a.absence_type  # 添加请假类型
        }
        for a in absences
    ]
    return jsonify(absences=res), 200


# 管理员审核请假申请
@app.route("/admin/absence/<int:absence_id>", methods=["PATCH"])
@jwt_required()
def admin_review_absence(absence_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role != "管理员":
        return jsonify(message="Access denied. Admin role required."), 403
    data = request.get_json() or {}
    decision = data.get("decision")
    if decision not in ("approve", "reject"):
        return jsonify(message="非法操作"), 400
    absence = Absence.query.get(absence_id)
    if not absence:
        return jsonify(message="记录不存在"), 404
    absence.status = 2 if decision == "approve" else 1
    db.session.commit()
    return jsonify(message="操作成功", id=absence.id, status=absence.status), 200
