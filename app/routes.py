from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import LoginForm, RegistrationForm, PostForm, AvatarForm
from app.models import User, Post
from app import db
import os
from werkzeug.utils import secure_filename
from PIL import Image
import time

main = Blueprint('main', __name__)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误')
            return redirect(url_for('main.login'))
        login_user(user)
        return redirect(url_for('main.index'))
    return render_template('login.html', title='登录', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功！')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='注册', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if request.method == 'POST':
        print("Received POST request")  # 调试信息
        print("Form data:", request.form)  # 调试信息
        
        if form.validate_on_submit():
            try:
                post = Post(
                    title=form.title.data,
                    content=form.content.data,
                    user=current_user
                )
                db.session.add(post)
                db.session.commit()
                flash('文章发布成功！')
                return redirect(url_for('main.post', id=post.id))
            except Exception as e:
                print(f"Error creating post: {e}")  # 调试信息
                db.session.rollback()
                flash('发布失败，请重试。')
        else:
            print("Form validation failed:", form.errors)  # 调试信息
            
    return render_template('create_post.html', title='发布文章', form=form)

@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', title=post.title, post=post)

@main.route('/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    if post.user != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('文章已更新！')
        return redirect(url_for('main.post', id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('edit_post.html', title='编辑文章', form=form, post=post)

@main.route('/post/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.user != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('文章已删除！')
    return redirect(url_for('main.index'))

@main.route('/')
@main.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
    return render_template('index.html', title='首页', posts=posts)

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    avatar_form = AvatarForm()
    if avatar_form.validate_on_submit():
        if avatar_form.avatar.data:
            # 保存原始文件
            filename = secure_filename(f'user_{current_user.id}_{int(time.time())}.jpg')
            
            # 确保 static/avatars 目录存在
            avatar_path = os.path.join(current_app.root_path, 'static', 'avatars')
            os.makedirs(avatar_path, exist_ok=True)
            
            filepath = os.path.join(avatar_path, filename)
            
            # 处理图片
            image = Image.open(avatar_form.avatar.data)
            # 将图片转换为正方形
            min_size = min(image.size)
            left = (image.size[0] - min_size) // 2
            top = (image.size[1] - min_size) // 2
            right = left + min_size
            bottom = top + min_size
            image = image.crop((left, top, right, bottom))
            # 调整大小为 200x200
            image = image.resize((200, 200))
            # 保存
            image.save(filepath, quality=95)
            
            # 更新数据库
            current_user.avatar = filename
            db.session.commit()
            flash('头像已更新！')
            return redirect(url_for('main.profile'))
            
    return render_template('profile.html', title='个人资料', avatar_form=avatar_form) 