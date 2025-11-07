# app.py

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Users, Notes
import secrets # Для генерации токенов

# Создаем экземпляр Flask-приложения
app = Flask(__name__)

# --- Настройка приложения ---
# Обязательно для Flask и Flask-WTF (если будете использовать формы)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-it-for-production' # Замените на случайный ключ!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализируем db, migrate и login_manager
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Маршрут для перенаправления при попытке доступа к защищенным страницам
login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ к этой странице.'

@login_manager.user_loader
def load_user(user_id):
    """Загружает пользователя по ID из сессии."""
    return Users.query.get(int(user_id))

# --- Маршруты ---
# Главная страница ('/')
@app.route('/')
@login_required # Только для авторизованных пользователей
def blog():
    """
    Отображает страницу блога.
    """
    return render_template('blog.html')

# Страница приветствия ('/home')
@app.route('/home')
def home():
    """
    Отображает страницу с кнопками регистрации и логина.
    """
    if current_user.is_authenticated:
        return redirect(url_for('blog')) # Если уже вошли, перенаправляем на блог
    return render_template('home.html')

# Страница регистрации ('/register')
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Отображает форму регистрации и обрабатывает её отправку.
    """
    if current_user.is_authenticated:
        return redirect(url_for('blog')) # Если уже вошли, перенаправляем на блог

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Проверка на уникальность логина и email
        if Users.query.filter_by(username=username).first():
            flash('Логин занят.')
            return redirect(url_for('register'))

        if Users.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован.')
            return redirect(url_for('register'))

        # Создаем нового пользователя
        new_user = Users(username=username, email=email)
        new_user.set_password(password) # Хешируем пароль

        # Добавляем в БД
        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация успешна! Пожалуйста, войдите.')
        return redirect(url_for('login'))

    return render_template('register.html')

# Страница логина ('/login')
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Отображает форму логина и обрабатывает её отправку.
    """
    if current_user.is_authenticated:
        return redirect(url_for('blog')) # Если уже вошли, перенаправляем на блог

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me')) # Проверяем галочку "Запомнить меня"

        user = Users.query.filter_by(username=username).first()

        # Проверяем, существует ли пользователь и правильный ли пароль
        if user and user.check_password(password):
            login_user(user, remember=remember_me) # Авторизуем пользователя
            # Генерация токена (опционально, можно хранить в сессии или использовать Flask-Login сессии)
            session['user_token'] = secrets.token_urlsafe(32) # Пример токена
            next_page = request.args.get('next') # Редирект на защищенную страницу, если была
            return redirect(next_page) if next_page else redirect(url_for('blog'))
        else:
            flash('Неправильный логин или пароль.')

    return render_template('login.html')

# Страница выхода ('/logout')
@app.route('/logout')
@login_required
def logout():
    """
    Выходит из системы.
    """
    logout_user()
    session.pop('user_token', None) # Удаляем токен из сессии (если хранили там)
    flash('Вы вышли из системы.')
    return redirect(url_for('home'))

# --- Страница "Дневник программиста" (обновлена для привязки к пользователю) ---
@app.route('/notes', methods=['GET', 'POST'])
@login_required # Только для авторизованных пользователей
def notes():
    """
    Отображает страницу дневника и обрабатывает добавление новых записей.
    """
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        content = request.form.get('content')

        if title and content:
            # Создаем новую заметку, привязанную к текущему пользователю
            new_note = Notes(title=title, subtitle=subtitle, text=content, author=current_user)
            db.session.add(new_note)
            db.session.commit()
            return redirect(url_for('notes'))

    # Запрашиваем только заметки текущего пользователя
    user_notes = Notes.query.filter_by(user_id=current_user.id).all()
    return render_template('notes.html', notes=user_notes)

# Проверяем, что скрипт запущен напрямую (а не импортирован)
if __name__ == '__main__':
    # Запускаем веб-сервер Flask в режиме отладки (debug=True)
    app.run(debug=True)