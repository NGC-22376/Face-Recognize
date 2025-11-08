from flask import request, jsonify
from app import app, db, SHANGHAI_TZ
from models import User, Attendance, Face, Absence
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, extract
import face_recognition as fr
import numpy as np
import os
import uuid
from sqlalchemy.sql.expression import case
from pypinyin import lazy_pinyin
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Absence
from datetime import timedelta
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
    import re

    data = request.get_json()

    # 新增：检查密保问题和答案是否为空
    required_fields = [
        "name",
        "account",
        "password",
        "security_question_1",
        "security_answer_1",
        "security_question_2",
        "security_answer_2",
        "security_question_3",
        "security_answer_3",
    ]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "所有字段（包括密保问题和答案）都不能为空"}), 400

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

    # 哈希密码和所有密保答案
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    hashed_answer_1 = bcrypt.generate_password_hash(data["security_answer_1"]).decode(
        "utf-8"
    )
    hashed_answer_2 = bcrypt.generate_password_hash(data["security_answer_2"]).decode(
        "utf-8"
    )
    hashed_answer_3 = bcrypt.generate_password_hash(data["security_answer_3"]).decode(
        "utf-8"
    )

    # 创建 User 对象时加入密保信息
    new_user = User(
        name=data["name"],
        account=data["account"],
        password=hashed_password,
        role=data.get("role", "员工"),
        security_question_1=data["security_question_1"],
        security_answer_1=hashed_answer_1,
        security_question_2=data["security_question_2"],
        security_answer_2=hashed_answer_2,
        security_question_3=data["security_question_3"],
        security_answer_3=hashed_answer_3,
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


@app.route("/password-recovery/get-questions", methods=["POST"])
def get_security_questions():
    data = request.get_json()
    account = data.get("account")
    if not account:
        return jsonify({"message": "账号不能为空"}), 400
    user = User.query.filter_by(account=account).first()
    if not user:
        return jsonify({"message": "账号不存在"}), 404
    # 从User模型中直接获取问题
    questions = [
        {"id": 1, "text": user.security_question_1},
        {"id": 2, "text": user.security_question_2},
        {"id": 3, "text": user.security_question_3},
    ]

    # 随机选择一个问题返回，增加安全性
    import random

    selected_question = random.choice(questions)
    return jsonify({"question": selected_question}), 200


# 验证密保答案
@app.route("/password-recovery/verify-answer", methods=["POST"])
def verify_security_answer():
    data = request.get_json()
    account = data.get("account")
    question_id = data.get("question_id")
    answer = data.get("answer")
    if not all([account, question_id, answer]):
        return jsonify({"message": "请求参数不完整"}), 400
    user = User.query.filter_by(account=account).first()
    if not user:
        return jsonify({"message": "账号不存在"}), 404
    # 根据 question_id 获取对应的密保答案哈希值
    correct_answer_hash = None
    if question_id == 1:
        correct_answer_hash = user.security_answer_1
    elif question_id == 2:
        correct_answer_hash = user.security_answer_2
    elif question_id == 3:
        correct_answer_hash = user.security_answer_3

    if not correct_answer_hash:
        return jsonify({"message": "无效的问题ID或用户未设置此问题"}), 400
    # 使用 bcrypt 校验答案
    if bcrypt.check_password_hash(correct_answer_hash, answer):
        # 验证成功，生成一个有时效性的临时token
        expires = timedelta(minutes=10)
        reset_token = create_access_token(
            identity=str(user.user_id),
            expires_delta=expires,
            additional_claims={"purpose": "password_reset"},
        )
        return jsonify({"message": "验证成功", "reset_token": reset_token}), 200
    else:
        return jsonify({"message": "密保答案错误"}), 401


# 使用临时token重置密码
@app.route("/password-recovery/reset-password", methods=["POST"])
@jwt_required()
def reset_password_with_token():
    jwt_claims = get_jwt()
    if jwt_claims.get("purpose") != "password_reset":
        return jsonify({"message": "无效的Token，请重新验证"}), 403
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    new_password = data.get("new_password")
    if not new_password or len(new_password) < 6:
        return jsonify({"message": "新密码格式不正确"}), 400
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "用户不存在"}), 404
    # 更新密码
    hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
    user.password = hashed_password
    db.session.commit()
    return jsonify({"message": "密码重置成功"}), 200


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
        # 早于 07:00 的签到不允许
        if current_time.hour < 7:
            return jsonify({"message": "当前不在打卡时间范围内"}), 400
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
        # 晚于 18:00 的签退不允许（仅允许 18:00:00）
        if (current_time.hour > 18) or (
            current_time.hour == 18
            and (
                current_time.minute > 0
                or current_time.second > 0
                or current_time.microsecond > 0
            )
        ):
            return jsonify({"message": "当前不在打卡时间范围内"}), 400
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
        else:
            # 18:00 之后（等于18:00）签退，统一显示为正常
            today_attendance.status = "正常"

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


# 若已签到但未签退且非请假，记为“未签退”
# 不自动创建缺勤记录（无打卡用户不生成记录）
def apply_end_of_day_rules():
    now = datetime.now(SHANGHAI_TZ)
    today = now.date()
    if now.hour < 18:
        return
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


# 计算指定用户在某月应出勤的天数（截至today）
def calculate_should_attend_days(user_id, year, month, today):
    # 1. 计算从本月1号到今天为止，总共有多少个工作日
    workdays_upto_today = 0
    first_day_of_month = date(year, month, 1)
    current_day = first_day_of_month
    while current_day <= today:
        if current_day.weekday() < 5:  # 0-4 是周一到周五
            workdays_upto_today += 1
        current_day += timedelta(days=1)

    # 2. 计算本月到今天为止，已批准的请假覆盖了多少个工作日
    approved_leaves_this_month = Absence.query.filter(
        Absence.user_id == user_id,
        Absence.status == 2,
        func.date(Absence.start_time) <= today,
        func.date(Absence.end_time) >= first_day_of_month,
    ).all()

    leave_workdays = set()
    for leave in approved_leaves_this_month:
        start_date = max(leave.start_time.date(), first_day_of_month)
        end_date = min(leave.end_time.date(), today)
        d = start_date
        while d <= end_date:
            if d.weekday() < 5:
                leave_workdays.add(d)
            d += timedelta(days=1)

    leave_day_count = len(leave_workdays)

    # 3. 返回最终结果
    return workdays_upto_today - leave_day_count


# 获取个人考勤记录和统计
@app.route("/attendance/personal", methods=["GET"])
@jwt_required()
def get_personal_attendance():
    current_user_id = int(get_jwt_identity())
    apply_end_of_day_rules()

    now = datetime.now(SHANGHAI_TZ)
    today = date.today()
    current_month = now.month
    current_year = now.year

    # 总出勤天数（不计未来日期）
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

    # 迟到次数（不计未来日期）
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

    # 早退次数（不计未来日期）
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

    # 正常次数（不计未来日期）
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

    # 应出勤天数计算（不计未来日期）
    should_attend_days = calculate_should_attend_days(
        current_user_id, current_year, current_month, today
    )

    # 最近记录（不含未来日期）
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

    records_list = []
    for record in recent_records:
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
                "status": record.status,
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
    if (
        datetime.now(SHANGHAI_TZ).hour >= 18
        and has_any_att_today == 0
        and not on_leave_today
    ):
        anchor_time = datetime(today.year, today.month, today.day, 0, 0, 0)
        records_list.insert(
            0,
            {
                "attendance_id": f"virtual-{today.strftime('%Y%m%d')}",
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
                    "should_attend": should_attend_days,
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
    # 应用18:00后的规则更新
    apply_end_of_day_rules()
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


# 管理员查看阶段考勤统计
@app.route("/admin/attendance/period", methods=["GET"])
@jwt_required()
def get_period_attendance_stats():
    # 应用18:00后的规则更新
    apply_end_of_day_rules()
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    # 检查是否为管理员
    if not user or user.role != "管理员":
        return jsonify({"message": "Access denied. Admin role required."}), 403

    # 获取查询参数
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    # 如果没有提供日期参数，使用默认近一个月
    if not start_date_str or not end_date_str:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    else:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "日期格式不正确，应为 YYYY-MM-DD"}), 400

    # 确保结束日期不早于开始日期
    if end_date < start_date:
        return jsonify({"message": "结束日期不能早于开始日期"}), 400

    # 计算三个阶段的时间范围 (按照1:2:1的比例)
    total_days = (end_date - start_date).days + 1
    # 第一阶段和第三阶段各占1/4，第二阶段占1/2
    phase1_days = total_days // 4
    phase2_days = total_days // 2
    phase3_days = total_days - phase1_days - phase2_days  # 剩余天数给第三阶段

    phase1_end = start_date + timedelta(days=phase1_days - 1)
    phase2_end = phase1_end + timedelta(days=phase2_days)
    phase3_end = end_date

    # 获取请假统计（按阶段）
    def get_absence_stats_by_phase():
        absence_stats = []
        
        # 定义阶段
        phases = [
            ("第一阶段", start_date, phase1_end),
            ("第二阶段", phase1_end + timedelta(days=1), phase2_end),
            ("第三阶段", phase2_end + timedelta(days=1), phase3_end)
        ]
        
        for phase_name, phase_start, phase_end in phases:
            # 病假 (absence_type = 0)
            sick_leave = db.session.query(func.count(Absence.id)).filter(
                and_(
                    Absence.absence_type == 0,
                    Absence.status == 2,  # 已批准
                    func.date(Absence.start_time) <= phase_end,
                    func.date(Absence.end_time) >= phase_start
                )
            ).scalar() or 0
            
            # 私事请假 (absence_type = 1)
            personal_leave = db.session.query(func.count(Absence.id)).filter(
                and_(
                    Absence.absence_type == 1,
                    Absence.status == 2,  # 已批准
                    func.date(Absence.start_time) <= phase_end,
                    func.date(Absence.end_time) >= phase_start
                )
            ).scalar() or 0
            
            # 公事请假 (absence_type = 2)
            official_leave = db.session.query(func.count(Absence.id)).filter(
                and_(
                    Absence.absence_type == 2,
                    Absence.status == 2,  # 已批准
                    func.date(Absence.start_time) <= phase_end,
                    func.date(Absence.end_time) >= phase_start
                )
            ).scalar() or 0
            
            absence_stats.append({
                "phase": phase_name,
                "sick_leave": sick_leave,      # 病假
                "personal_leave": personal_leave,  # 私事请假
                "official_leave": official_leave   # 公事请假
            })
            
        return absence_stats

    # 获取出勤统计（按阶段）
    def get_attendance_stats_by_phase():
        attendance_stats = []
        
        # 定义阶段
        phases = [
            ("第一阶段", start_date, phase1_end),
            ("第二阶段", phase1_end + timedelta(days=1), phase2_end),
            ("第三阶段", phase2_end + timedelta(days=1), phase3_end)
        ]
        
        for phase_name, phase_start, phase_end in phases:
            # 正常出勤
            normal = db.session.query(func.count(Attendance.attendance_id)).filter(
                and_(
                    func.date(Attendance.clock_in_time) >= phase_start,
                    func.date(Attendance.clock_in_time) <= phase_end,
                    Attendance.status == "正常"
                )
            ).scalar() or 0
            
            # 迟到
            late = db.session.query(func.count(Attendance.attendance_id)).filter(
                and_(
                    func.date(Attendance.clock_in_time) >= phase_start,
                    func.date(Attendance.clock_in_time) <= phase_end,
                    Attendance.status == "迟到"
                )
            ).scalar() or 0
            
            # 早退
            early = db.session.query(func.count(Attendance.attendance_id)).filter(
                and_(
                    func.date(Attendance.clock_in_time) >= phase_start,
                    func.date(Attendance.clock_in_time) <= phase_end,
                    Attendance.status == "早退"
                )
            ).scalar() or 0
            
            # 加班（这里假设加班是指正常工作时间外的打卡）
            # 为了简化，我们可以通过 clock_out_time 晚于 18:00 来判断加班
            overtime = db.session.query(func.count(Attendance.attendance_id)).filter(
                and_(
                    func.date(Attendance.clock_in_time) >= phase_start,
                    func.date(Attendance.clock_in_time) <= phase_end,
                    Attendance.clock_out_time.isnot(None),
                    extract('hour', Attendance.clock_out_time) > 18
                )
            ).scalar() or 0
            
            attendance_stats.append({
                "phase": phase_name,
                "normal": normal,      # 正常
                "late": late,          # 迟到
                "early": early,        # 早退
                "overtime": overtime   # 加班
            })
            
        return attendance_stats

    # 获取统计数据
    absence_stats = get_absence_stats_by_phase()
    attendance_stats = get_attendance_stats_by_phase()

    # 添加阶段的具体时间范围
    phase_ranges = {
        "第一阶段": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": phase1_end.strftime("%Y-%m-%d")
        },
        "第二阶段": {
            "start": (phase1_end + timedelta(days=1)).strftime("%Y-%m-%d"),
            "end": phase2_end.strftime("%Y-%m-%d")
        },
        "第三阶段": {
            "start": (phase2_end + timedelta(days=1)).strftime("%Y-%m-%d"),
            "end": phase3_end.strftime("%Y-%m-%d")
        }
    }

    return (
        jsonify({
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "phase_ranges": phase_ranges,
            "absence_stats": absence_stats,
            "attendance_stats": attendance_stats
        }),
        200
    )


# 管理员查看所有员工考勤情况
@app.route("/admin/attendance/employees", methods=["GET"])
@jwt_required()
def get_employees_attendance():
    # 应用18:00后的规则更新
    apply_end_of_day_rules()
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    # 检查是否为管理员
    if not user or user.role != "管理员":
        return jsonify({"message": "Access denied. Admin role required."}), 403

    today = date.today()

    # 获取排序参数
    sort_by = request.args.get(
        "sort_by", "account"
    )  # name, late_count, early_leave_count, normal_count, leave_count
    sort_order = request.args.get("sort_order", "asc")  # asc, desc
    # 安全地获取和转换分页参数
    page_param = request.args.get("page", 1)
    page_size_param = request.args.get("page_size", 10)

    # 处理可能为'undefined'或其他非数字值的情况
    try:
        page = int(page_param)
    except (ValueError, TypeError):
        page = 1

    try:
        page_size = int(page_size_param)
    except (ValueError, TypeError):
        page_size = 10

    # 验证页码和每页大小
    if page < 1:
        return jsonify({"message": "页码必须大于等于1"}), 400
    if page_size < 1:
        return jsonify({"message": "每页大小必须大于等于1"}), 400

    # 动态计算统计数据并排序
    subquery = (
        db.session.query(
            User.user_id,
            User.name,
            User.account,
            func.count(Attendance.attendance_id).label("total_days"),
            func.sum(case((Attendance.status == "迟到", 1), else_=0)).label(
                "late_count"
            ),
            func.sum(case((Attendance.status == "早退", 1), else_=0)).label(
                "early_leave_count"
            ),
            func.sum(case((Attendance.status == "正常", 1), else_=0)).label(
                "normal_count"
            ),
            func.sum(case((Absence.status == 2, 1), else_=0)).label("leave_count"),
        )
        .outerjoin(Attendance, Attendance.user_id == User.user_id)
        .outerjoin(Absence, Absence.user_id == User.user_id)
        .filter(User.role == "员工")
        .group_by(User.user_id)
        .subquery()
    )

    query = db.session.query(subquery)

    # 获取查询结果
    employees = query.all()

    # 如果按姓名排序，使用拼音排序
    if sort_by == "name":
        employees = sorted(
            employees,
            key=lambda x: "".join(lazy_pinyin(x.name)),
            reverse=(sort_order == "desc"),
        )
    else:
        # 其他字段排序
        employees = sorted(
            employees,
            key=lambda x: getattr(x, sort_by),
            reverse=(sort_order == "desc"),
        )

    # 分页
    total = len(employees)
    employees = employees[(page - 1) * page_size : page * page_size]

    employees_list = []
    for row in employees:
        employees_list.append(
            {
                "user_id": row.user_id,
                "name": row.name,
                "account": row.account,
                "monthly_stats": {
                    "total_days": row.total_days,
                    "late_count": row.late_count,
                    "early_leave_count": row.early_leave_count,
                    "normal_count": row.normal_count,
                    "leave_count": row.leave_count,
                },
                "on_leave_today": db.session.query(func.count(Absence.id))
                .filter(
                    Absence.user_id == row.user_id,
                    Absence.status == 2,
                    func.date(Absence.start_time) <= today,
                    func.date(Absence.end_time) >= today,
                )
                .scalar()
                > 0,
                "is_absent_today": db.session.query(
                    func.count(Attendance.attendance_id)
                )
                .filter(
                    Attendance.user_id == row.user_id,
                    func.date(Attendance.clock_in_time) == today,
                )
                .scalar()
                == 0,
                "today_attendance": db.session.query(
                    func.count(Attendance.attendance_id)
                )
                .filter(
                    Attendance.user_id == row.user_id,
                    func.date(Attendance.clock_in_time) == today,
                )
                .scalar(),
            }
        )

    return (
        jsonify(
            {
                "employees": employees_list,
                "total": total,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "current_page": page,
                "page_size": page_size,
            }
        ),
        200,
    )


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

        # 检查absence_type是否在请求数据中
        if "absence_type" not in data:
            return jsonify(message="您未选择请假类型"), 400

        absence_type = data.get("absence_type", 0)  # 默认值为0（病假）

        # 检查其他必要参数
        if not start_time_str:
            return jsonify(message="请填写/选择请假开始时间"), 400

        if not end_time_str:
            return jsonify(message="请填写/选择请假结束时间"), 400

        if not reason:
            return jsonify(message="请填写请假原因"), 400

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
            absence_type=absence_type,  # 保存请假类型
        )
        db.session.add(absence)
        db.session.commit()
        return jsonify(message="请假申请已提交", id=absence.id), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f"服务器错误: {str(e)}"), 500


# 个人请假申请列表（支持分页，每页5条）
@app.route("/absence/personal", methods=["GET"])
@jwt_required()
def get_personal_absences():
    current_user_id = int(get_jwt_identity())
    # 获取分页参数，默认为第1页
    page = request.args.get("page", 1, type=int)
    per_page = 5
    # 获取状态过滤参数
    status = request.args.get("status", type=int)
    # 获取排序参数
    sort_by = request.args.get("sort_by", "start_time")  # 默认按起始时间排序
    order = request.args.get("order", "desc")  # 默认倒序

    # 构建查询
    query = Absence.query.filter_by(user_id=current_user_id)

    # 如果提供了状态参数，则按状态过滤
    if status is not None:
        query = query.filter(Absence.status == status)

    # 确定排序字段
    if sort_by == "end_time":
        sort_field = Absence.end_time
    else:
        sort_field = Absence.start_time

    # 确定排序方向
    if order == "asc":
        sort_field = sort_field.asc()
    else:
        sort_field = sort_field.desc()

    # 使用paginate进行分页查询
    pagination = query.order_by(sort_field).paginate(
        page=page, per_page=per_page, error_out=False
    )

    absences = pagination.items
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
            "absence_type": a.absence_type,  # 添加请假类型
        }
        for a in absences
    ]

    # 返回分页信息和数据
    return (
        jsonify(
            {
                "absences": res,
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": pagination.page,
                "per_page": per_page,
            }
        ),
        200,
    )


# 管理员查看请假申请列表（支持分页）
@app.route("/admin/absence", methods=["GET"])
@jwt_required()
def admin_list_absences():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role != "管理员":
        return jsonify(message="Access denied. Admin role required."), 403

    processed = request.args.get("processed", "false").lower() == "true"
    # 获取具体状态参数（用于已通过/已拒绝分离显示）
    specific_status = request.args.get("status", type=int)
    # 获取分页参数，默认为第1页
    page = request.args.get("page", 1, type=int)
    # 获取每页记录数，默认为5条，最大不超过1000条
    per_page = min(request.args.get("page_size", 5, type=int), 1000)

    # 获取过滤参数
    name_filter = request.args.get("name")
    absence_type_filter = request.args.get("absence_type", type=int)

    query = Absence.query
    if specific_status is not None:
        # 如果提供了具体状态参数，按具体状态过滤
        query = query.filter(Absence.status == specific_status)
    elif processed:
        # 如果只提供了processed=true，按已处理状态过滤（兼容旧接口）
        query = query.filter(Absence.status.in_([1, 2]))
    else:
        # 未处理状态
        query = query.filter(Absence.status == 0)

    # 应用姓名过滤
    if name_filter:
        # 通过用户表关联过滤
        query = query.join(User).filter(User.name.ilike(f"%{name_filter}%"))

    # 应用请假类型过滤
    if absence_type_filter is not None:
        query = query.filter(Absence.absence_type == absence_type_filter)

    # 使用paginate进行分页查询
    pagination = query.order_by(Absence.start_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    absences = pagination.items

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
            "absence_type": a.absence_type,  # 添加请假类型
        }
        for a in absences
    ]

    # 返回分页信息和数据
    return (
        jsonify(
            {
                "absences": res,
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": pagination.page,
                "per_page": per_page,
            }
        ),
        200,
    )


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


# 管理员批量审核请假申请
@app.route("/admin/absence/batch", methods=["PATCH"])
@jwt_required()
def admin_batch_review_absence():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role != "管理员":
        return jsonify(message="Access denied. Admin role required."), 403

    data = request.get_json() or {}
    decision = data.get("decision")
    absence_ids = data.get("absence_ids", [])

    if decision not in ("approve", "reject"):
        return jsonify(message="非法操作"), 400

    if not absence_ids:
        return jsonify(message="请选择要处理的请假申请"), 400

    success_count = 0
    failed_ids = []

    for absence_id in absence_ids:
        try:
            absence = Absence.query.get(absence_id)
            if absence and absence.status == 0:  # 只处理未处理的申请
                absence.status = 2 if decision == "approve" else 1
                success_count += 1
            else:
                failed_ids.append(absence_id)
        except Exception as e:
            failed_ids.append(absence_id)
            print(f"处理请假申请 {absence_id} 时出错: {e}")

    db.session.commit()

    if failed_ids:
        return jsonify(
            message=f"成功处理 {success_count} 条申请，失败 {len(failed_ids)} 条",
            failed_ids=failed_ids,
            success_count=success_count,
        ), 207  # Multi-Status

    return jsonify(
        message=f"成功处理 {success_count} 条申请", success_count=success_count
    ), 200
