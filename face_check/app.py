from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import face_recognition as fr
import numpy as np
import os
import uuid

app = Flask(__name__)
CORS(app)

# ---------- 数据库 ----------
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "face.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 单表：识别记录（含录入）
class Person(db.Model):
    __tablename__ = 'face'
    rec_id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, nullable=False, comment='用户号（录入时自增）')
    image_path = db.Column(db.String(255), default=None)
    rec_time   = db.Column(db.DateTime, default=datetime.utcnow)
    result     = db.Column(db.String(255), default=None)   # 录入 / 成功 / 未录入 / 异常
    # 128D 特征文件路径（不直接存向量）
    feature_path = db.Column(db.String(255), default=None)

with app.app_context():
    db.create_all()

# ---------- 目录 ----------
os.makedirs("upload", exist_ok=True)
os.makedirs("face_db", exist_ok=True)

# ---------- 工具 ----------
def save_image(file):
    """保存文件并返回路径"""
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join("upload", name)
    os.makedirs("upload", exist_ok=True)
    file.save(path)
    return path

def extract_feature(image_path):
    """提取 128D 向量，失败抛 IndexError"""
    img = fr.load_image_file(image_path)
    return fr.face_encodings(img)[0]

# ---------- 录入 ----------
@app.post("/api/face/register")
def register():
    if "file" not in request.files or "username" not in request.form:
        return jsonify(ok=False, msg="缺少文件或用户名"), 400

    username = request.form["username"].strip()
    if not username:
        return jsonify(ok=False, msg="用户名为空"), 400

    img_path = save_image(request.files["file"])
    try:
        feature = extract_feature(img_path)
    except IndexError:
        os.remove(img_path)
        return jsonify(ok=False, msg="未检测到人脸"), 400

    # 特征文件
    feat_path = os.path.join("face_db", f"{username}.npy")
    np.save(feat_path, feature)

    # 写数据库（user_id 用 username 的 hash 或简单自增，这里直接字符串→整型）
    user_id = abs(hash(username)) % (10 ** 8)          # 8 位数字，可替换为自增
    db.session.add(Person(
        user_id=user_id,
        image_path=img_path,
        result='',
        feature_path=feat_path
    ))
    db.session.commit()
    return jsonify(ok=True, msg="录入成功")

# ---------- 签到 ----------
@app.post("/api/face/checkin")
def checkin():
    if "file" not in request.files:
        return jsonify(ok=False, msg="未上传文件"), 400

    img_path = save_image(request.files["file"])
    try:
        unknown = extract_feature(img_path)
    except IndexError:
        os.remove(img_path)
        return jsonify(ok=False, msg="未检测到人脸"), 400

    # 1:N 比对
    best_uid = None
    best_dist = 0.6
    for p in Person.query.all():
        known = np.load(p.feature_path)
        dist = np.linalg.norm(known - unknown)
        if dist < best_dist:
            best_dist = dist
            best_uid = p.user_id

    os.remove(img_path)
    if best_uid:
        # 按user_id找到最新记录并更新
        rec= (Person.query.filter_by(user_id=best_uid)
              .order_by(Person.rec_time.desc())
              .first())
        if rec:
            rec.result = '成功'
            rec.rec_time = datetime.utcnow()  # 刷新为当前识别时间
            db.session.commit()
        return jsonify(ok=True,
                      username=str(best_uid),   # 前端原来要 username 字段
                      time=datetime.now().strftime("%H:%M:%S"))
    else:
        return jsonify(ok=False, msg="检测到未录入的人脸"), 404

# ---------- 启动 ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)