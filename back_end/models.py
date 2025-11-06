from app import db
from datetime import datetime




class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='员工')

    security_question_1 = db.Column(db.String(255), nullable=True)
    security_answer_1 = db.Column(db.String(255), nullable=True, comment='哈希后的密保答案1')
    security_question_2 = db.Column(db.String(255), nullable=True)
    security_answer_2 = db.Column(db.String(255), nullable=True, comment='哈希后的密保答案2')
    security_question_3 = db.Column(db.String(255), nullable=True)
    security_answer_3 = db.Column(db.String(255), nullable=True, comment='哈希后的密保答案3')


    faces = db.relationship('Face', backref='user', cascade="all, delete-orphan")
    attendances = db.relationship('Attendance', backref='user', cascade="all, delete-orphan")
    absences = db.relationship('Absence', backref='user', cascade="all, delete-orphan")



class Face(db.Model):
    __tablename__ = 'face'
    rec_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'))
    image_path = db.Column(db.String(255))
    rec_time = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.Column(db.String(50))

class Attendance(db.Model):
    __tablename__ = 'attendance'
    attendance_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'))
    clock_in_time = db.Column(db.DateTime, nullable=True)
    clock_out_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50))

class Absence(db.Model):
    __tablename__ = 'absence'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0, comment='0:未审批, 1:已拒绝, 2:已通过')
    reason = db.Column(db.Text, nullable=False)
