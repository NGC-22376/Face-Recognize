from flask import request, jsonify
from app import app, db
from models import User, Attendance, Face
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, date
from sqlalchemy import func, and_, extract

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# JWT错误处理
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'message': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'message': 'Invalid token'}), 422

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({'message': 'Authorization header is expected'}), 401

# 用户注册
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(name=data['name'], account=data['account'], password=hashed_password, role=data['role'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

# 用户登录
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(account=data['account']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        # 创建token时使用字符串作为identity
        access_token = create_access_token(identity=str(user.user_id))
        return jsonify({
            'access_token': access_token,
            'user': {
                'user_id': user.user_id,
                'name': user.name,
                'account': user.account,
                'role': user.role
            }
        }), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

# 用户打卡
@app.route('/attendance', methods=['POST'])
@jwt_required()
def attendance():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # 判断打卡类型（上班/下班）
    attendance_type = data.get('type', 'clock_in')  # clock_in 或 clock_out
    current_time = datetime.now()
    
    if attendance_type == 'clock_in':
        # 上班打卡
        status = '正常'
        # 判断是否迟到（假设9:00为上班时间）
        if current_time.hour > 9 or (current_time.hour == 9 and current_time.minute > 0):
            status = '迟到'
            
        new_attendance = Attendance(
            user_id=current_user_id, 
            clock_in_time=current_time, 
            status=status
        )
    else:
        # 下班打卡 - 更新现有记录
        today_attendance = Attendance.query.filter(
            and_(
                Attendance.user_id == current_user_id,
                func.date(Attendance.clock_in_time) == date.today()
            )
        ).first()
        
        if not today_attendance:
            return jsonify({'message': 'No clock-in record found for today'}), 404
            
        today_attendance.clock_out_time = current_time
        # 判断是否早退（假设18:00为下班时间）
        if current_time.hour < 18:
            today_attendance.status = '早退'
        
        db.session.commit()
        return jsonify({'message': 'Clock-out recorded successfully'}), 200
    
    db.session.add(new_attendance)
    db.session.commit()
    
    return jsonify({'message': 'Clock-in recorded successfully'}), 201

# 获取用户信息
@app.route('/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'user_id': user.user_id,
        'name': user.name,
        'account': user.account,
        'role': user.role
    }), 200

# 获取个人考勤记录
@app.route('/attendance/personal', methods=['GET'])
@jwt_required()
def get_personal_attendance():
    current_user_id = int(get_jwt_identity())
    
    # 获取本月考勤统计 - 使用分别查询的方式
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # 总出勤天数
    total_days = db.session.query(func.count(Attendance.attendance_id)).filter(
        and_(
            Attendance.user_id == current_user_id,
            extract('month', Attendance.clock_in_time) == current_month,
            extract('year', Attendance.clock_in_time) == current_year
        )
    ).scalar() or 0
    
    # 迟到次数
    late_count = db.session.query(func.count(Attendance.attendance_id)).filter(
        and_(
            Attendance.user_id == current_user_id,
            extract('month', Attendance.clock_in_time) == current_month,
            extract('year', Attendance.clock_in_time) == current_year,
            Attendance.status == '迟到'
        )
    ).scalar() or 0
    
    # 早退次数
    early_leave_count = db.session.query(func.count(Attendance.attendance_id)).filter(
        and_(
            Attendance.user_id == current_user_id,
            extract('month', Attendance.clock_in_time) == current_month,
            extract('year', Attendance.clock_in_time) == current_year,
            Attendance.status == '早退'
        )
    ).scalar() or 0
    
    # 正常次数
    normal_count = db.session.query(func.count(Attendance.attendance_id)).filter(
        and_(
            Attendance.user_id == current_user_id,
            extract('month', Attendance.clock_in_time) == current_month,
            extract('year', Attendance.clock_in_time) == current_year,
            Attendance.status == '正常'
        )
    ).scalar() or 0
    
    # 获取最近的考勤记录
    recent_records = Attendance.query.filter_by(user_id=current_user_id)\
        .order_by(Attendance.clock_in_time.desc())\
        .limit(10).all()
    
    records_list = []
    for record in recent_records:
        records_list.append({
            'attendance_id': record.attendance_id,
            'clock_in_time': record.clock_in_time.strftime('%Y-%m-%d %H:%M:%S') if record.clock_in_time else None,
            'clock_out_time': record.clock_out_time.strftime('%Y-%m-%d %H:%M:%S') if record.clock_out_time else None,
            'status': record.status
        })
    
    return jsonify({
        'monthly_stats': {
            'total_days': total_days,
            'late_count': late_count,
            'early_leave_count': early_leave_count,
            'normal_count': normal_count,
            'should_attend': 22  # 假设每月应出勤22天
        },
        'recent_records': records_list
    }), 200

# 管理员查看当天考勤总体情况
@app.route('/admin/attendance/daily', methods=['GET'])
@jwt_required()
def get_daily_attendance_overview():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    # 检查是否为管理员
    if not user or user.role != '管理员':
        return jsonify({'message': 'Access denied. Admin role required.'}), 403
    
    today = date.today()
    
    # 当天考勤统计 - 使用分别查询的方式
    actual_attendance = db.session.query(func.count(func.distinct(Attendance.user_id))).filter(
        func.date(Attendance.clock_in_time) == today
    ).scalar() or 0
    
    late_count = db.session.query(func.count(Attendance.attendance_id)).filter(
        and_(
            func.date(Attendance.clock_in_time) == today,
            Attendance.status == '迟到'
        )
    ).scalar() or 0
    
    early_leave_count = db.session.query(func.count(Attendance.attendance_id)).filter(
        and_(
            func.date(Attendance.clock_in_time) == today,
            Attendance.status == '早退'
        )
    ).scalar() or 0
    
    normal_count = db.session.query(func.count(Attendance.attendance_id)).filter(
        and_(
            func.date(Attendance.clock_in_time) == today,
            Attendance.status == '正常'
        )
    ).scalar() or 0
    
    # 总员工数
    total_employees = User.query.filter_by(role='员工').count()
    
    return jsonify({
        'date': today.strftime('%Y-%m-%d'),
        'should_attend': total_employees,
        'actual_attendance': actual_attendance,
        'late_count': late_count,
        'early_leave_count': early_leave_count,
        'normal_count': normal_count
    }), 200

# 管理员查看所有员工考勤情况
@app.route('/admin/attendance/employees', methods=['GET'])
@jwt_required()
def get_employees_attendance():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    # 检查是否为管理员
    if not user or user.role != '管理员':
        return jsonify({'message': 'Access denied. Admin role required.'}), 403
    
    # 获取排序参数
    sort_by = request.args.get('sort_by', 'name')  # name, late_count, early_leave_count, normal_count
    sort_order = request.args.get('sort_order', 'asc')  # asc, desc
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    today = date.today()
    
    # 获取所有员工
    employees = User.query.filter_by(role='员工').all()
    employees_list = []
    
    for user in employees:
        # 今日出勤
        today_attendance = db.session.query(func.count(Attendance.attendance_id)).filter(
            and_(
                Attendance.user_id == user.user_id,
                func.date(Attendance.clock_in_time) == today
            )
        ).scalar() or 0
        
        # 本月总出勤
        monthly_total = db.session.query(func.count(Attendance.attendance_id)).filter(
            and_(
                Attendance.user_id == user.user_id,
                extract('month', Attendance.clock_in_time) == current_month,
                extract('year', Attendance.clock_in_time) == current_year
            )
        ).scalar() or 0
        
        # 本月迟到次数
        monthly_late = db.session.query(func.count(Attendance.attendance_id)).filter(
            and_(
                Attendance.user_id == user.user_id,
                extract('month', Attendance.clock_in_time) == current_month,
                extract('year', Attendance.clock_in_time) == current_year,
                Attendance.status == '迟到'
            )
        ).scalar() or 0
        
        # 本月早退次数
        monthly_early_leave = db.session.query(func.count(Attendance.attendance_id)).filter(
            and_(
                Attendance.user_id == user.user_id,
                extract('month', Attendance.clock_in_time) == current_month,
                extract('year', Attendance.clock_in_time) == current_year,
                Attendance.status == '早退'
            )
        ).scalar() or 0
        
        # 本月正常次数
        monthly_normal = db.session.query(func.count(Attendance.attendance_id)).filter(
            and_(
                Attendance.user_id == user.user_id,
                extract('month', Attendance.clock_in_time) == current_month,
                extract('year', Attendance.clock_in_time) == current_year,
                Attendance.status == '正常'
            )
        ).scalar() or 0
        
        employees_list.append({
            'user_id': user.user_id,
            'name': user.name,
            'account': user.account,
            'today_attendance': today_attendance,
            'monthly_stats': {
                'total_days': monthly_total,
                'late_count': monthly_late,
                'early_leave_count': monthly_early_leave,
                'normal_count': monthly_normal,
                'should_attend': 22
            }
        })
    
    # 应用Python排序
    if sort_by == 'late_count':
        employees_list.sort(key=lambda x: x['monthly_stats']['late_count'], reverse=(sort_order == 'desc'))
    elif sort_by == 'early_leave_count':
        employees_list.sort(key=lambda x: x['monthly_stats']['early_leave_count'], reverse=(sort_order == 'desc'))
    elif sort_by == 'normal_count':
        employees_list.sort(key=lambda x: x['monthly_stats']['normal_count'], reverse=(sort_order == 'desc'))
    else:  # 默认按姓名排序
        employees_list.sort(key=lambda x: x['name'], reverse=(sort_order == 'desc'))
    
    return jsonify({
        'employees': employees_list,
        'sort_by': sort_by,
        'sort_order': sort_order
    }), 200
