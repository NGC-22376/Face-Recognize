#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试考勤计算逻辑的正确性
验证应出勤天数是否正确减去了已批准的请假天数
"""

import sys
import os
from datetime import date, timedelta

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'back_end'))

from back_end.routes import calculate_should_attend_days
from back_end.models import db, User, Absence
from back_end import create_app

def test_attendance_calculation():
    """测试考勤计算逻辑"""
    print("=== 考勤计算逻辑测试 ===")
    
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        # 查找一个测试用户
        test_user = User.query.filter_by(role='员工').first()
        if not test_user:
            print("未找到测试用户")
            return
            
        print(f"测试用户: {test_user.name} (ID: {test_user.user_id})")
        
        # 获取当前日期信息
        today = date.today()
        current_year = today.year
        current_month = today.month
        
        print(f"当前日期: {today}")
        print(f"当前年份: {current_year}")
        print(f"当前月份: {current_month}")
        
        # 计算应出勤天数
        should_attend = calculate_should_attend_days(
            test_user.user_id, current_year, current_month, today
        )
        
        print(f"计算得出的应出勤天数: {should_attend}")
        
        # 查看该用户的所有已批准请假记录
        approved_leaves = Absence.query.filter(
            Absence.user_id == test_user.user_id,
            Absence.status == 2
        ).all()
        
        print(f"\n该用户已批准的请假记录数量: {len(approved_leaves)}")
        
        for i, leave in enumerate(approved_leaves, 1):
            print(f"请假记录 {i}:")
            print(f"  开始时间: {leave.start_time}")
            print(f"  结束时间: {leave.end_time}")
            print(f"  请假理由: {leave.reason}")
        
        print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_attendance_calculation()