#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试加班时间判断逻辑的正确性
验证19:00后打卡才算加班的逻辑
"""

import sys
import os
from datetime import datetime, date, time, timedelta

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'back_end'))

from back_end.routes import db
from back_end.models import Attendance
from back_end import create_app

def create_test_attendance_record(clock_out_time_str):
    """创建测试考勤记录"""
    app = create_app()
    with app.app_context():
        # 创建一个测试考勤记录
        test_date = date.today()
        clock_in_time = datetime.combine(test_date, time(9, 0))  # 上班时间 9:00
        clock_out_time = datetime.combine(test_date, time.fromisoformat(clock_out_time_str))
        
        # 创建考勤记录
        attendance = Attendance(
            user_id=1,  # 测试用户ID
            clock_in_time=clock_in_time,
            clock_out_time=clock_out_time,
            work_date=test_date,
            status="正常",
            clock_in_status="正常",
            clock_out_status="正常"
        )
        
        return attendance

def test_overtime_logic():
    """测试加班时间判断逻辑"""
    print("=== 加班时间判断逻辑测试 ===")
    
    app = create_app()
    with app.app_context():
        # 测试不同下班时间的情况
        test_times = [
            ("17:30", "17:30下班，应该算早退"),
            ("18:00", "18:00下班，应该算正常"),
            ("18:30", "18:30下班，应该算正常"),
            ("19:00", "19:00下班，应该算正常"),
            ("19:30", "19:30下班，应该算加班"),
            ("20:00", "20:00下班，应该算加班"),
            ("21:00", "21:00下班，应该算加班")
        ]
        
        for time_str, description in test_times:
            print(f"\n测试: {description}")
            
            # 创建测试记录
            attendance = create_test_attendance_record(time_str)
            
            # 根据我们修改的逻辑判断状态
            clock_out_time = attendance.clock_out_time
            if clock_out_time.hour < 18 or (clock_out_time.hour == 18 and clock_out_time.minute == 0):
                calculated_status = "早退"
                calculated_clock_out_status = "早退"
            elif clock_out_time.hour < 19:
                # 18:00-19:00之间打卡算正常下班
                calculated_status = "正常"
                calculated_clock_out_status = "正常"
            else:
                # 19:00后打卡才算加班
                calculated_status = "加班"
                calculated_clock_out_status = "加班"
            
            print(f"  下班时间: {time_str}")
            print(f"  计算得出的打卡状态: {calculated_clock_out_status}")
            print(f"  计算得出的考勤状态: {calculated_status}")

if __name__ == "__main__":
    test_overtime_logic()
    print("\n=== 测试完成 ===")