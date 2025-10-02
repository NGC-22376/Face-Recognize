#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库设置脚本
用于创建数据库、执行SQL文件并插入测试数据
"""

import pymysql
import os
from app import app, db
from models import User, Attendance
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import random
import pytz

# 创建中国时区对象（UTC+8）
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')

# 数据库连接配置
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASS', '456729')
DB_NAME = 'face_rec'

bcrypt = Bcrypt()

def create_database():
    """创建数据库"""
    try:
        # 连接MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"数据库 {DB_NAME} 创建成功或已存在")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"创建数据库失败: {e}")
        return False

def execute_sql_file(file_path):
    """执行SQL文件"""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
            
        # 分割SQL语句
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        with connection.cursor() as cursor:
            for statement in sql_statements:
                if statement:
                    cursor.execute(statement)
                    
        connection.commit()
        connection.close()
        print(f"SQL文件 {file_path} 执行成功")
        return True
        
    except Exception as e:
        print(f"执行SQL文件 {file_path} 失败: {e}")
        return False

def create_tables_with_sqlalchemy():
    """使用SQLAlchemy创建表"""
    try:
        with app.app_context():
            # 删除所有表
            db.drop_all()
            
            # 创建所有表
            db.create_all()
            
            print("使用SQLAlchemy创建表成功！")
            return True
    except Exception as e:
        print(f"使用SQLAlchemy创建表失败: {e}")
        return False

def insert_test_data():
    """插入测试数据"""
    try:
        with app.app_context():
            # 检查是否已有数据
            if User.query.first():
                print("数据库中已有数据，跳过插入测试数据")
                return True
                
            # 创建管理员用户
            admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin_user = User(
                account='admin',
                name='管理员',
                password=admin_password,
                role='管理员'
            )
            db.session.add(admin_user)
            
            # 创建普通员工
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
            
            # 创建测试考勤数据
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
            print("测试数据插入成功！")
            return True
            
    except Exception as e:
        print(f"插入测试数据失败: {e}")
        return False

def main():
    """主函数"""
    print("开始设置数据库...")
    
    # 1. 创建数据库
    if not create_database():
        return
    
    # 2. 使用SQLAlchemy创建表（推荐方式）
    if create_tables_with_sqlalchemy():
        print("使用SQLAlchemy创建表成功")
    else:
        print("SQLAlchemy创建表失败，尝试执行SQL文件...")
        # 3. 如果SQLAlchemy失败，尝试执行SQL文件
        sql_files = [
            '../sql/user.sql',
            '../sql/face.sql', 
            '../sql/attendance.sql'
        ]
        
        for sql_file in sql_files:
            if os.path.exists(sql_file):
                execute_sql_file(sql_file)
            else:
                print(f"SQL文件不存在: {sql_file}")
    
    # 4. 插入测试数据
    insert_test_data()
    
    print("数据库设置完成！")
    print("\n登录信息:")
    print("管理员账号: admin, 密码: admin123")
    print("员工账号: emp001-emp005, 密码: 123456")

if __name__ == '__main__':
    main()
