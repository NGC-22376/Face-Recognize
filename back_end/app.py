from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # 允许跨域请求

db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@localhost/face_rec'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = 'test'  # 可以自定义，建议复杂一点
app.config['JWT_SECRET_KEY'] = 'testtest'  # 可以自定义，建议复杂一点

# 初始化数据库
db = SQLAlchemy(app)

from routes import *

if __name__ == '__main__':
    app.run(debug=True)
