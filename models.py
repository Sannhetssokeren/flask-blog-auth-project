# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin # Для Flask-Login
from werkzeug.security import generate_password_hash, check_password_hash # Для хеширования паролей

# Создаем экземпляр SQLAlchemy
db = SQLAlchemy()

# Модель для пользователей
class Users(UserMixin, db.Model):
    """
    Модель для хранения информации о пользователях.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Связь с заметками (один ко многим)
    notes = db.relationship('Notes', backref='author', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """Хеширует и сохраняет пароль."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет, соответствует ли введенный пароль хешу."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Модель для записей (обновленная, связана с пользователем)
class Notes(db.Model):
    """
    Модель для хранения записей в дневнике.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300), nullable=True)
    text = db.Column(db.Text, nullable=False)
    # Внешний ключ для связи с пользователем
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Notes {self.title}>'
