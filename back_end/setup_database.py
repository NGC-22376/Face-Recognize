import glob
import pymysql
import os
import random
from datetime import datetime, timedelta, date, time  # 新增 time 和 date 模块
import pytz
from app import app, db
from flask_bcrypt import Bcrypt
from sqlalchemy import text
from models import (
    User,
    Attendance,
    Absence,
    Face,
    FaceEnrollment,
    MonthlyAttendanceStats,
)

# 创建中国时区对象（UTC+8）
SHANGHAI_TZ = pytz.timezone("Asia/Shanghai")

# 数据库连接配置
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASS", "456729")  # 请确保替换为你的密码
DB_NAME = "face_rec"

# 初始化bcrypt
bcrypt = Bcrypt(app)


def create_database():
    """创建数据库 (如果不存在)"""
    try:
        connection = pymysql.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, charset="utf8mb4"
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.close()
        print(f"数据库 '{DB_NAME}' 创建成功或已存在。")
        return True
    except pymysql.MySQLError as e:
        print(f"创建数据库失败: {e}")
        return False


def create_tables_with_sqlalchemy():
    """使用 SQLAlchemy 创建所有表"""
    """使用 SQLAlchemy 创建所有表"""
    try:
        with app.app_context():
            print("正在删除旧表并创建新表...")
            db.drop_all()  # 删除所有旧表，确保结构最新
            db.create_all()  # 根据 models.py 创建所有新表
            print("使用 SQLAlchemy 创建表成功！")
            return True
    except Exception as e:
        print(f"使用 SQLAlchemy 创建表失败: {e}")
        print(f"使用 SQLAlchemy 创建表失败: {e}")
        return False


def insert_test_data():
    """插入用户测试数据"""
    with app.app_context():
        try:
            print("正在预计算哈希值...")
            admin_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
            common_password = bcrypt.generate_password_hash("123456").decode("utf-8")
            employee_answer_1_hashed = bcrypt.generate_password_hash("000000").decode(
                "utf-8"
            )
            employee_answer_2_hashed = bcrypt.generate_password_hash("技术部").decode(
                "utf-8"
            )
            employee_answer_3_hashed = bcrypt.generate_password_hash("软件工程").decode(
                "utf-8"
            )

            common_password = bcrypt.generate_password_hash("123456").decode("utf-8")
            employee_answer_1_hashed = bcrypt.generate_password_hash("000000").decode(
                "utf-8"
            )
            employee_answer_2_hashed = bcrypt.generate_password_hash("技术部").decode(
                "utf-8"
            )
            employee_answer_3_hashed = bcrypt.generate_password_hash("软件工程").decode(
                "utf-8"
            )

            admin_user = User(
                account="admin",
                name="管理员",
                password=admin_password,
                role="管理员",
                security_question_1="我的职责是什么？",
                security_answer_1=bcrypt.generate_password_hash("管理员").decode(
                    "utf-8"
                ),
                security_question_2="系统名称是什么？",
                security_answer_2=bcrypt.generate_password_hash("face_rec").decode(
                    "utf-8"
                ),
                security_question_3="我的出生城市是哪里？",
                security_answer_3=bcrypt.generate_password_hash("系统").decode("utf-8"),
            )
            db.session.add(admin_user)
            print("管理员用户创建成功。")

            print("正在生成100条员工数据...")
            surnames = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴"]
            given_name_chars = [
                "伟",
                "芳",
                "娜",
                "敏",
                "静",
                "丽",
                "强",
                "磊",
                "军",
                "洋",
            ]

            
                
            users_to_add = []
            for i in range(1, 101):
                account = f"empid{i:03d}"
                name = random.choice(surnames) + "".join(
                    random.sample(given_name_chars, random.randint(1, 2))
                )
                employee = User(
                    account=account,
                    name=name,
                    password=common_password,
                    role="员工",
                    security_question_1="您的身份证号码后六位是多少？",
                    security_answer_1=employee_answer_1_hashed,
                    security_question_2="您所在部门的全称是什么？",
                    security_answer_2=employee_answer_2_hashed,
                    security_question_3="您大学时期的专业全称是什么？",
                    security_answer_3=employee_answer_3_hashed,
                )
                users_to_add.append(employee)


            db.session.add_all(users_to_add)
            print("100名员工及专业密保创建成功！")

            # 提交以生成user_id
            db.session.commit()
            image_folder = os.path.join(os.path.dirname(__file__), "static")
            image_files = glob.glob(os.path.join(image_folder, "*.jpg")) + glob.glob(os.path.join(image_folder, "*.png"))
            image_files = [os.path.relpath(f, start=os.path.dirname(__file__)) for f in image_files]
            if not image_files:
                print("static 文件夹下没有找到图片，无法分配人脸图像。")
                return False

            # 为每个员工添加人脸图像（face.jpg）
            print("为每个员工添加人脸图像...")
            employees = User.query.filter(User.role == "员工").all()
            faces_to_add = []
            for emp in employees:
                face_image_path = random.choice(image_files)
                face = Face(
                    user_id=emp.user_id,
                    image_path=face_image_path,
                )
                faces_to_add.append(face)
            db.session.add_all(faces_to_add)
            print(f"已为{len(faces_to_add)}名员工随机分配人脸图像。")

            db.session.commit()
            print("用户数据事务已提交。")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"插入用户数据时发生错误: {e}")
            return False


def insert_attendance_data():
    """为所有员工生成从本月第一天到今天的考勤数据"""
    with app.app_context():
        try:
            print("\n正在生成考勤测试数据...")

            # 1. 定义考勤规则
            WORK_START_TIME = time(9, 0, 0)
            WORK_END_TIME = time(18, 0, 0)

            # 2. 获取日期范围
            today = datetime.now(SHANGHAI_TZ).date()
            start_date = today.replace(day=1)
            delta = today - start_date

            # 3. 获取所有员工 (user_id > 1)
            # 假设管理员ID为1，员工ID从2开始
            employee_ids = [
                user.user_id for user in User.query.filter(User.role == "员工").all()
            ]
            if not employee_ids:
                print("未找到员工用户，跳过考勤数据生成。")
                return True

            attendance_records = []

            # 4. 遍历每一天
            for i in range(delta.days + 1):
                current_date = start_date + timedelta(days=i)

                # 跳过周末 (周六是5, 周日是6)
                if current_date.weekday() >= 5:
                    continue

                # 5. 为每个员工生成当天的考勤记录
                for user_id in employee_ids:
                    # 检查是否有请假记录覆盖当天
                    has_leave = Absence.query.filter(
                        Absence.user_id == user_id,
                        Absence.status == 2,  # 已批准的请假
                        db.func.date(Absence.start_time) <= current_date,
                        db.func.date(Absence.end_time) >= current_date,
                    ).first()

                    if has_leave:
                        # 创建请假状态的考勤记录
                        record = Attendance(
                            user_id=user_id, work_date=current_date, status="请假"
                        )
                        attendance_records.append(record)
                        continue

                    # 模拟10%的未出勤（未打卡）
                    if random.random() < 0.1:
                        record = Attendance(
                            user_id=user_id, work_date=current_date, status="未出勤"
                        )
                        attendance_records.append(record)
                        continue

                    # --- 生成上班打卡时间 ---
                    base_in_time = datetime.combine(
                        current_date, WORK_START_TIME, tzinfo=SHANGHAI_TZ
                    )
                    # 模拟20%的迟到率
                    if random.random() < 0.2:
                        # 迟到 1 到 59 分钟
                        delay = timedelta(minutes=random.randint(1, 59))
                        clock_in = base_in_time + delay
                        clock_in_status = "迟到"
                    else:
                        # 正常/早到: 提前 0 到 30 分钟
                        early_arrival = timedelta(minutes=random.randint(0, 30))
                        clock_in = base_in_time - early_arrival
                        clock_in_status = "正常"

                    # 模拟15%的未签退情况
                    if random.random() < 0.15:
                        # 只打卡上班，不打卡下班
                        record = Attendance(
                            user_id=user_id,
                            clock_in_time=clock_in,
                            work_date=current_date,
                            status="未签退",
                            clock_in_status=clock_in_status,
                            clock_out_status="未签退",
                        )
                        attendance_records.append(record)
                        continue

                    # --- 生成下班打卡时间 ---
                    base_out_time = datetime.combine(
                        current_date, WORK_END_TIME, tzinfo=SHANGHAI_TZ
                    )
                    # 模拟20%的早退率
                    if random.random() < 0.2:
                        # 早退 1 到 59 分钟
                        early_departure = timedelta(minutes=random.randint(1, 59))
                        clock_out = base_out_time - early_departure
                        clock_out_status = "早退"
                        final_status = "早退"
                    elif random.random() < 0.2:  # 模拟20%的加班率
                        # 加班 1 到 120 分钟
                        overtime = timedelta(minutes=random.randint(1, 120))
                        clock_out = base_out_time + overtime
                        clock_out_status = "加班"
                        final_status = "加班"
                    else:
                        # 正常下班
                        clock_out = base_out_time
                        clock_out_status = "正常"
                        final_status = "正常"

                    # 如果上班迟到，最终状态需要包含迟到信息
                    if clock_in_status == "迟到":
                        if final_status != "正常":
                            final_status = "迟到、" + final_status
                        else:
                            final_status = "迟到"

                    # 创建考勤对象
                    record = Attendance(
                        user_id=user_id,
                        clock_in_time=clock_in,
                        clock_out_time=clock_out,
                        work_date=current_date,
                        status=final_status,
                        clock_in_status=clock_in_status,
                        clock_out_status=clock_out_status,
                    )
                    attendance_records.append(record)

            # 6. 批量插入数据库
            if attendance_records:
                db.session.add_all(attendance_records)
                db.session.commit()
                print(f"成功生成并插入了 {len(attendance_records)} 条考勤记录。")
            else:
                print("没有生成任何考勤记录。")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"插入考勤数据时发生错误: {e}")
            return False


def initialize_monthly_attendance_stats():
    """初始化月度考勤统计数据"""
    with app.app_context():
        try:
            print("\n正在初始化月度考勤统计数据...")

            # 获取当前年月
            now = datetime.now(SHANGHAI_TZ)
            current_year = now.year
            current_month = now.month

            # 获取所有员工
            employees = User.query.filter(User.role == "员工").all()

            # 为每个员工生成当前月的统计记录
            stats_records = []
            for employee in employees:
                # 检查是否已存在该员工本月的统计记录
                existing_stats = MonthlyAttendanceStats.query.filter(
                    MonthlyAttendanceStats.user_id == employee.user_id,
                    MonthlyAttendanceStats.year == current_year,
                    MonthlyAttendanceStats.month == current_month,
                ).first()

                # 如果不存在，则创建新的统计记录
                if not existing_stats:
                    # 获取该员工本月的所有考勤记录
                    attendance_records = Attendance.query.filter(
                        Attendance.user_id == employee.user_id,
                        db.extract("year", Attendance.clock_in_time) == current_year,
                        db.extract("month", Attendance.clock_in_time) == current_month,
                    ).all()

                    # 计算最早和最晚打卡时间
                    earliest_clock_in = None
                    latest_clock_in = None
                    earliest_clock_out = None
                    latest_clock_out = None

                    for record in attendance_records:
                        if record.clock_in_time:
                            clock_in_time = record.clock_in_time.time()
                            if (
                                not earliest_clock_in
                                or clock_in_time < earliest_clock_in
                            ):
                                earliest_clock_in = clock_in_time
                            if not latest_clock_in or clock_in_time > latest_clock_in:
                                latest_clock_in = clock_in_time

                        if record.clock_out_time:
                            clock_out_time = record.clock_out_time.time()
                            if (
                                not earliest_clock_out
                                or clock_out_time < earliest_clock_out
                            ):
                                earliest_clock_out = clock_out_time
                            if (
                                not latest_clock_out
                                or clock_out_time > latest_clock_out
                            ):
                                latest_clock_out = clock_out_time

                    # 创建月度统计记录
                    monthly_stats = MonthlyAttendanceStats(
                        user_id=employee.user_id,
                        year=current_year,
                        month=current_month,
                        earliest_clock_in=earliest_clock_in,
                        latest_clock_in=latest_clock_in,
                        earliest_clock_out=earliest_clock_out,
                        latest_clock_out=latest_clock_out,
                        normal_count=0,
                        late_count=0,
                        early_leave_count=0,
                        overtime_count=0,
                        no_checkout_count=0,
                        absence_count=0,
                        leave_count=0,
                    )
                    stats_records.append(monthly_stats)

            # 批量插入统计记录
            if stats_records:
                db.session.add_all(stats_records)
                db.session.commit()
                print(f"成功初始化 {len(stats_records)} 条月度考勤统计记录。")
            else:
                print("没有需要初始化的月度考勤统计记录。")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"初始化月度考勤统计数据时发生错误: {e}")
            return False


def generate_historical_monthly_stats():
    """为员工生成过去几个月的模拟月度考勤统计数据"""
    with app.app_context():
        try:
            print("\n正在生成历史月度考勤统计数据...")

            # 获取当前年月
            now = datetime.now(SHANGHAI_TZ)
            current_year = now.year
            current_month = now.month

            # 获取所有员工
            employees = User.query.filter(User.role == "员工").all()

            # 生成过去6个月的数据
            stats_records = []
            for i in range(1, 7):  # 生成过去6个月的数据
                # 计算目标年月
                if current_month - i <= 0:
                    target_year = current_year - 1
                    target_month = 12 + (current_month - i)
                else:
                    target_year = current_year
                    target_month = current_month - i

                for employee in employees:
                    # 检查是否已存在该员工该月的统计记录
                    existing_stats = MonthlyAttendanceStats.query.filter(
                        MonthlyAttendanceStats.user_id == employee.user_id,
                        MonthlyAttendanceStats.year == target_year,
                        MonthlyAttendanceStats.month == target_month,
                    ).first()

                    # 如果不存在，则创建新的统计记录
                    if not existing_stats:
                        # 模拟生成该月的统计数据
                        # 生成随机的时间数据来模拟最早和最晚打卡时间
                        # 上班时间通常在8:00-10:00之间
                        earliest_clock_in_hour = random.randint(8, 9)
                        earliest_clock_in_minute = random.randint(0, 59)
                        earliest_clock_in = time(
                            earliest_clock_in_hour, earliest_clock_in_minute
                        )

                        latest_clock_in_hour = random.randint(9, 10)
                        latest_clock_in_minute = random.randint(0, 59)
                        latest_clock_in = time(
                            latest_clock_in_hour, latest_clock_in_minute
                        )

                        # 下班时间通常在17:00-19:00之间
                        earliest_clock_out_hour = random.randint(17, 18)
                        earliest_clock_out_minute = random.randint(0, 59)
                        earliest_clock_out = time(
                            earliest_clock_out_hour, earliest_clock_out_minute
                        )

                        latest_clock_out_hour = random.randint(18, 19)
                        latest_clock_out_minute = random.randint(0, 59)
                        latest_clock_out = time(
                            latest_clock_out_hour, latest_clock_out_minute
                        )

                        # 创建月度统计记录
                        monthly_stats = MonthlyAttendanceStats(
                            user_id=employee.user_id,
                            year=target_year,
                            month=target_month,
                            earliest_clock_in=earliest_clock_in,
                            latest_clock_in=latest_clock_in,
                            earliest_clock_out=earliest_clock_out,
                            latest_clock_out=latest_clock_out,
                            normal_count=random.randint(0, 20),
                            late_count=random.randint(0, 5),
                            early_leave_count=random.randint(0, 3),
                            overtime_count=random.randint(0, 10),
                            no_checkout_count=0,
                            absence_count=random.randint(0, 2),
                            leave_count=random.randint(0, 3),
                        )
                        stats_records.append(monthly_stats)

            # 批量插入统计记录
            if stats_records:
                db.session.add_all(stats_records)
                db.session.commit()
                print(f"成功生成并插入了 {len(stats_records)} 条历史月度考勤统计记录。")
            else:
                print("没有生成任何历史月度考勤统计记录。")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"生成历史月度考勤统计数据时发生错误: {e}")
            return False


def insert_absence_data():
    """为部分员工生成模拟请假数据，涵盖各种类型和状态"""
    with app.app_context():
        try:
            print("\n正在生成模拟请假数据...")

            # 获取当前日期
            now = datetime.now(SHANGHAI_TZ)
            today = now.date()

            # 获取所有员工
            employees = User.query.filter(User.role == "员工").all()

            # 生成100条请假记录
            absence_records = []

            # 定义请假类型和对应的中文描述
            absence_types = [(0, "病假"), (1, "私事请假"), (2, "公事请假")]

            # 定义请假状态
            absence_statuses = [(0, "未审批"), (1, "已拒绝"), (2, "已通过")]

            # 确保每种类型和状态都有足够的数据
            # 生成100条记录，其中：
            # - 30条病假（包含各种状态）
            # - 30条私事请假（包含各种状态）
            # - 30条公事请假（包含各种状态）
            # - 10条随机类型（用于补充）

            for type_id, type_name in absence_types:
                # 为每种类型生成30条记录
                for i in range(30):
                    # 随机选择一个员工
                    employee = random.choice(employees)

                    # 根据索引确定状态分布，确保每种状态都有覆盖
                    if i < 10:
                        status_id, status_name = absence_statuses[0]  # 未审批
                    elif i < 20:
                        status_id, status_name = absence_statuses[1]  # 已拒绝
                    else:
                        status_id, status_name = absence_statuses[2]  # 已通过

                    # 生成不同时间段的请假日期
                    # 前10条：过去一个月内的请假
                    # 中间10条：当前日期附近的请假
                    # 后10条：未来一个月内的请假
                    if i < 10:
                        # 过去一个月
                        days_offset = random.randint(-30, -1)
                    elif i < 20:
                        # 当前日期附近
                        days_offset = random.randint(-5, 5)
                    else:
                        # 未来一个月
                        days_offset = random.randint(1, 30)

                    start_date = today + timedelta(days=days_offset)
                    end_date = start_date + timedelta(days=random.randint(1, 10))

                    # 生成针对不同类型请假的原因
                    reason_templates = {
                        0: [  # 病假原因
                            "感冒发烧，需要休息治疗",
                            "肠胃不适，去医院检查",
                            "头痛严重，需要就医",
                            "牙痛难忍，预约看牙医",
                            "腰椎疼痛，需要理疗",
                            "眼部不适，眼科复查",
                            "皮肤过敏，需要药物治疗",
                            "血压偏高，定期检查",
                            "呼吸道感染，需要输液",
                            "身体疲劳，需要调养",
                        ],
                        1: [  # 私事请假原因
                            "家中有事，需要处理",
                            "家庭聚会，庆祝生日",
                            "个人事务处理",
                            "朋友婚礼，需要出席",
                            "搬家整理，需要时间",
                            "家人手术，需要陪护",
                            "孩子学校家长会",
                            "房屋维修，需要监督",
                            "银行办理重要业务",
                            "照顾生病家属",
                        ],
                        2: [  # 公事请假原因
                            "参加重要会议",
                            "外出培训学习",
                            "处理紧急工作事务",
                            "出差洽谈业务",
                            "参加行业展会",
                            "公司团建活动",
                            "接待重要客户",
                            "参加学术研讨会",
                            "外出调研考察",
                            "参加政府会议",
                        ],
                    }

                    reason = random.choice(reason_templates[type_id])

                    # 创建请假记录
                    absence = Absence(
                        user_id=employee.user_id,
                        start_time=datetime.combine(start_date, time(9, 0)),
                        end_time=datetime.combine(end_date, time(18, 0)),
                        reason=reason,
                        status=status_id,
                        absence_type=type_id,
                    )
                    absence_records.append(absence)

            # 生成额外的10条随机类型记录
            for _ in range(10):
                # 随机选择一个员工
                employee = random.choice(employees)

                # 随机选择请假类型
                type_id, type_name = random.choice(absence_types)

                # 随机选择状态
                status_id, status_name = random.choice(absence_statuses)

                # 随机生成请假日期 (在过去或未来一个月内)
                days_offset = random.randint(-30, 30)
                start_date = today + timedelta(days=days_offset)
                end_date = start_date + timedelta(days=random.randint(1, 10))

                # 根据类型选择原因
                reason_templates = {
                    0: [  # 病假原因
                        "身体不适，需要休息",
                        "去医院体检",
                        "需要复诊治疗",
                        "药物副作用反应",
                    ],
                    1: [  # 私事请假原因
                        "处理个人事务",
                        "家庭安排调整",
                        "私人约会",
                        "其他私人事务",
                    ],
                    2: [  # 公事请假原因
                        "公务外出",
                        "临时工作安排",
                        "参加会议",
                        "紧急工作任务",
                    ],
                }

                reason = random.choice(reason_templates[type_id])

                # 创建请假记录
                absence = Absence(
                    user_id=employee.user_id,
                    start_time=datetime.combine(start_date, time(9, 0)),
                    end_time=datetime.combine(end_date, time(18, 0)),
                    reason=reason,
                    status=status_id,
                    absence_type=type_id,
                )
                absence_records.append(absence)

            # 批量插入请假记录
            if absence_records:
                db.session.add_all(absence_records)
                db.session.commit()
                print(f"成功生成并插入了 {len(absence_records)} 条模拟请假记录。")

                # 统计各类数据
                type_counts = {0: 0, 1: 0, 2: 0}
                status_counts = {0: 0, 1: 0, 2: 0}

                for record in absence_records:
                    type_counts[record.absence_type] += 1
                    status_counts[record.status] += 1

                print(
                    f"请假类型统计: 病假({type_counts[0]}), 私事请假({type_counts[1]}), 公事请假({type_counts[2]})"
                )
                print(
                    f"请假状态统计: 未审批({status_counts[0]}), 已拒绝({status_counts[1]}), 已通过({status_counts[2]})"
                )
            else:
                print("没有生成任何模拟请假记录。")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"插入模拟请假数据时发生错误: {e}")
            return False


def main():
    """主函数，执行数据库初始化流程"""
    print("开始设置数据库...")

    with app.app_context():  # 添加全局应用上下文
        if not create_database():
            return

        if create_tables_with_sqlalchemy():
            if insert_test_data():
                if insert_attendance_data():
                    # 初始化月度考勤统计数据
                    initialize_monthly_attendance_stats()
                    # 生成历史月度考勤统计数据
                    generate_historical_monthly_stats()
                    # 生成模拟请假数据
                    insert_absence_data()
        else:
            print("因为表创建失败，所以无法插入测试数据。")

    print("\n" + "=" * 40)
    print("数据库设置完成！")
    print("\n登录信息:")
    print("  - 管理员账号: admin, 密码: admin123")
    print("  - 员工账号: empid001 - empid100, 密码: 123456")
    print("\n已为所有员工生成从本月第一天到今天的模拟考勤数据。")
    print("\n已为所有员工生成过去6个月的模拟月度考勤统计数据。")
    print("=" * 40)


if __name__ == "__main__":
    main()
