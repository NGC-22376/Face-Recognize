from app import db
from datetime import datetime
from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(255))
    name = db.Column(db.String(255))
    password = db.Column(db.String(255))
    role = db.Column(db.String(255))  # 角色权限，如员工，管理员

    # 关联关系
    faces = db.relationship('Face', backref='user', cascade="all, delete-orphan")
    attendances = db.relationship('Attendance', backref='user', cascade="all, delete-orphan")

class Face(db.Model):
    __tablename__ = 'face'
    rec_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE', onupdate='CASCADE'))
    image_path = db.Column(db.String(255))
    rec_time = db.Column(db.DateTime)
    result = db.Column(db.String(255))  # 识别结果，如成功，失败，异常

class Attendance(db.Model):
    __tablename__ = 'attendance'
    attendance_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE', onupdate='CASCADE'))
    clock_in_time = db.Column(db.DateTime)   # 上班时间
    clock_out_time = db.Column(db.DateTime)  # 下班时间
    status = db.Column(db.String(255))       # 状态，如迟到，早退，正常