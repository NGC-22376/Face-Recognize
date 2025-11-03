from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import pytz
from sqlalchemy import create_engine  # 用于数据库连接测
from routes import *

app = Flask(__name__)
CORS(app)  # 允许跨域请求

db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST", "localhost")


# 配置数据库
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/face_rec"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SECRET_KEY"] = "test"  # 可以自定义，建议复杂一点
app.config["JWT_SECRET_KEY"] = "testtest"  # 可以自定义，建议复杂一点
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # 设置token不过期（开发环境）

# 创建中国时区对象（UTC+8）
SHANGHAI_TZ = pytz.timezone("Asia/Shanghai")


# 初始化数据库
db = SQLAlchemy(app)


if __name__ == "__main__":
    # 测试数据库连接
    try:
        engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
        connection = engine.connect()
        print("数据库连接成功")
        connection.close()
    except Exception as e:
        print(f"数据库连接失败: {e}")

    app.run(debug=True, host="0.0.0.0", port=5000)
