from app import create_app, db
from app.models import User, Post

app = create_app()

with app.app_context():
    db.drop_all()  # 删除所有表
    db.create_all()  # 重新创建表 