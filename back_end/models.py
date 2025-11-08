from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.String(255))
    name = db.Column(db.String(255))
    password = db.Column(db.String(255))
    role = db.Column(db.String(255))  # 角色权限，如员工，管理员

    # 添加安全问题和答案字段
    security_question_1 = db.Column(db.String(255), nullable=True)
    security_answer_1 = db.Column(
        db.String(255), nullable=True, comment="哈希后的密保答案1"
    )
    security_question_2 = db.Column(db.String(255), nullable=True)
    security_answer_2 = db.Column(
        db.String(255), nullable=True, comment="哈希后的密保答案2"
    )
    security_question_3 = db.Column(db.String(255), nullable=True)
    security_answer_3 = db.Column(
        db.String(255), nullable=True, comment="哈希后的密保答案3"
    )

    # 关联关系
    faces = db.relationship("Face", backref="user", cascade="all, delete-orphan")
    attendances = db.relationship(
        "Attendance", backref="user", cascade="all, delete-orphan"
    )
    # 请假申请关联
    absences = db.relationship("Absence", backref="user", cascade="all, delete-orphan")
    # 人脸审核表
    face_enrollment = db.relationship(
        "FaceEnrollment", backref="user", cascade="all, delete-orphan"
    )


class Face(db.Model):
    __tablename__ = "face"
    rec_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id", ondelete="CASCADE"))
    image_path = db.Column(db.String(255))
    rec_time = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.Column(db.String(50))


class Attendance(db.Model):
    __tablename__ = "attendance"
    attendance_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id", ondelete="CASCADE"))
    clock_in_time = db.Column(db.DateTime, nullable=True)
    clock_out_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50))


class Absence(db.Model):
    __tablename__ = "absence"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False
    )
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(
        db.Integer, nullable=False, default=0, comment="0:未审批, 1:已拒绝, 2:已通过"
    )
    reason = db.Column(db.Text, nullable=False)
    absence_type = db.Column(
        db.Integer, nullable=False, default=0
    )  # 0病假 1私事请假 2公事请假


# 人脸录入审核表
class FaceEnrollment(db.Model):
    __tablename__ = "face_enrollment"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    image_path = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Integer, default=0)  # 0:待审核, 1:通过, 2:拒绝
    created_time = db.Column(db.DateTime)
    reviewed_time = db.Column(db.DateTime)
    review_comment = db.Column(db.String(255))  # 审核意见
