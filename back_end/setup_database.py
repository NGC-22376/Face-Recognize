import pymysql
import os
import random
from datetime import datetime, timedelta, date, time  # 新增 time 和 date 模块
import pytz
from app import app, db
from flask_bcrypt import Bcrypt
from sqlalchemy import text
from models import User, Attendance, Absence, Face, FaceEnrollment, MonthlyAttendanceStats

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
                    # 模拟大约5%的缺勤率 (当天无记录)
                    if random.random() < 0.05:
                        continue

                    status_parts = []

                    # --- 生成上班打卡时间 ---
                    base_in_time = datetime.combine(
                        current_date, WORK_START_TIME, tzinfo=SHANGHAI_TZ
                    )
                    # 模拟15%的迟到率
                    if random.random() < 0.15:
                        # 迟到 1 到 59 分钟
                        delay = timedelta(minutes=random.randint(1, 59))
                        clock_in = base_in_time + delay
                        status_parts.append("迟到")
                    else:
                        # 正常/早到: 提前 0 到 30 分钟
                        early_arrival = timedelta(minutes=random.randint(0, 30))
                        clock_in = base_in_time - early_arrival

                    # --- 生成下班打卡时间 ---
                    base_out_time = datetime.combine(
                        current_date, WORK_END_TIME, tzinfo=SHANGHAI_TZ
                    )
                    # 模拟15%的早退率
                    if random.random() < 0.15:
                        # 早退 1 到 59 分钟
                        early_departure = timedelta(minutes=random.randint(1, 59))
                        clock_out = base_out_time - early_departure
                        status_parts.append("早退")
                    else:
                        # 正常/加班: 延迟 0 到 90 分钟
                        overtime = timedelta(minutes=random.randint(0, 90))
                        clock_out = base_out_time + overtime

                    # --- 确定最终状态 ---
                    if not status_parts:
                        status = "正常"
                    else:
                        status = "、".join(status_parts)  # 例如 "迟到、早退"

                    # 创建考勤对象
                    record = Attendance(
                        user_id=user_id,
                        clock_in_time=clock_in,
                        clock_out_time=clock_out,
                        status=status,
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
                    MonthlyAttendanceStats.month == current_month
                ).first()
                
                # 如果不存在，则创建新的统计记录
                if not existing_stats:
                    # 获取该员工本月的所有考勤记录
                    attendance_records = Attendance.query.filter(
                        Attendance.user_id == employee.user_id,
                        db.extract('year', Attendance.clock_in_time) == current_year,
                        db.extract('month', Attendance.clock_in_time) == current_month
                    ).all()
                    
                    # 计算最早和最晚打卡时间
                    earliest_clock_in = None
                    latest_clock_in = None
                    earliest_clock_out = None
                    latest_clock_out = None
                    
                    for record in attendance_records:
                        if record.clock_in_time:
                            clock_in_time = record.clock_in_time.time()
                            if not earliest_clock_in or clock_in_time < earliest_clock_in:
                                earliest_clock_in = clock_in_time
                            if not latest_clock_in or clock_in_time > latest_clock_in:
                                latest_clock_in = clock_in_time
                        
                        if record.clock_out_time:
                            clock_out_time = record.clock_out_time.time()
                            if not earliest_clock_out or clock_out_time < earliest_clock_out:
                                earliest_clock_out = clock_out_time
                            if not latest_clock_out or clock_out_time > latest_clock_out:
                                latest_clock_out = clock_out_time
                    
                    # 创建月度统计记录
                    monthly_stats = MonthlyAttendanceStats(
                        user_id=employee.user_id,
                        year=current_year,
                        month=current_month,
                        earliest_clock_in=earliest_clock_in,
                        latest_clock_in=latest_clock_in,
                        earliest_clock_out=earliest_clock_out,
                        latest_clock_out=latest_clock_out
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


def insert_absence_data():
    """为部分员工生成模拟请假数据"""
    with app.app_context():
        try:
            print("\n正在生成模拟请假数据...")
            
            # 获取当前日期
            now = datetime.now(SHANGHAI_TZ)
            today = now.date()
            
            # 获取所有员工
            employees = User.query.filter(User.role == "员工").all()
            
            # 为约10%的员工生成请假记录
            absence_records = []
            for employee in employees:
                # 10%概率生成请假记录
                if random.random() < 0.1:
                    # 随机选择请假类型 (0:病假, 1:私事请假, 2:公事请假)
                    absence_type = random.randint(0, 2)
                    
                    # 随机生成请假日期 (在未来一周内)
                    start_date = today + timedelta(days=random.randint(1, 7))
                    end_date = start_date + timedelta(days=random.randint(1, 5))
                    
                    # 生成请假原因
                    reasons = [
                        "身体不适，需要休息",
                        "家中有事，需要处理",
                        "参加重要会议",
                        "外出培训学习",
                        "处理紧急工作事务"
                    ]
                    reason = random.choice(reasons)
                    
                    # 创建请假记录 (状态设为未审批: 0)
                    absence = Absence(
                        user_id=employee.user_id,
                        start_time=datetime.combine(start_date, time(9, 0)),
                        end_time=datetime.combine(end_date, time(18, 0)),
                        reason=reason,
                        status=0,  # 未审批
                        absence_type=absence_type
                    )
                    absence_records.append(absence)
            
            # 批量插入请假记录
            if absence_records:
                db.session.add_all(absence_records)
                db.session.commit()
                print(f"成功生成并插入了 {len(absence_records)} 条模拟请假记录。")
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
    print("=" * 40)


if __name__ == "__main__":
    main()
