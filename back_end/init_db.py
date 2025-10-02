#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库初始化脚本
用于创建表结构和插入测试数据
"""

from app import app, db
from models import User, Attendance
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import random
import pytz

# 创建中国时区对象（UTC+8）
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')

bcrypt = Bcrypt()

def init_database():
    """初始化数据库"""
    with app.app_context():
        # 删除所有表
        db.drop_all()
        
        # 创建所有表
        db.create_all()
        
        print("数据库表创建成功！")
        
        # 创建测试用户
        create_test_users()
        
        # 创建测试考勤数据
        create_test_attendance()
        
        print("测试数据插入完成！")

def create_test_users():
    """创建测试用户"""
    # 管理员用户
    admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
    admin_user = User(
        account='admin',
        name='管理员',
        password=admin_password,
        role='管理员'
    )
    db.session.add(admin_user)
    
    # 普通员工
    employees = [
        {'account': 'emp001', 'name': '张三', 'role': '员工'},
        {'account': 'emp002', 'name': '李四', 'role': '员工'},
        {'account': 'emp003', 'name': '王五', 'role': '员工'},
        {'account': 'emp004', 'name': '赵六', 'role': '员工'},
        {'account': 'emp005', 'name': '钱七', 'role': '员工'},
    ]
    
    for emp_data in employees:
        password = bcrypt.generate_password_hash('123456').decode('utf-8')
        employee = User(
            account=emp_data['account'],
            name=emp_data['name'],
            password=password,
            role=emp_data['role']
        )
        db.session.add(employee)
    
    db.session.commit()
    print("测试用户创建完成")

def create_test_attendance():
    """创建测试考勤数据"""
    users = User.query.filter_by(role='员工').all()
    
    # 为每个员工创建过去30天的考勤记录
    for user in users:
        for i in range(30):
            date = datetime.now(SHANGHAI_TZ) - timedelta(days=i)
            
            # 80% 的概率出勤
            if random.random() < 0.8:
                # 随机生成上班时间 (8:30 - 9:30)
                clock_in_hour = random.randint(8, 9)
                clock_in_minute = random.randint(0, 59) if clock_in_hour == 8 else random.randint(0, 30)
                
                clock_in_time = date.replace(
                    hour=clock_in_hour,
                    minute=clock_in_minute,
                    second=random.randint(0, 59),
                    microsecond=0
                )
                
                # 判断状态
                status = '正常'
                if clock_in_hour > 9 or (clock_in_hour == 9 and clock_in_minute > 0):
                    status = '迟到'
                
                # 随机生成下班时间 (17:30 - 19:00)
                clock_out_hour = random.randint(17, 18)
                clock_out_minute = random.randint(30, 59) if clock_out_hour == 17 else random.randint(0, 59)
                
                clock_out_time = date.replace(
                    hour=clock_out_hour,
                    minute=clock_out_minute,
                    second=random.randint(0, 59),
                    microsecond=0
                )
                
                # 如果下班时间早于18:00，设为早退
                if clock_out_hour < 18:
                    status = '早退'
                
                attendance = Attendance(
                    user_id=user.user_id,
                    clock_in_time=clock_in_time,
                    clock_out_time=clock_out_time,
                    status=status
                )
                db.session.add(attendance)
    
    db.session.commit()
    print("测试考勤数据创建完成")

if __name__ == '__main__':
    init_database()
