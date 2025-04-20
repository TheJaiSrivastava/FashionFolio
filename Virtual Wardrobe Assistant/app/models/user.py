from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User preferences
    location = db.Column(db.String(100))  # For weather-based recommendations
    style_preference = db.Column(db.String(50))  # casual, formal, sporty, etc.
    
    # Relationships
    clothing_items = db.relationship('ClothingItem', backref='owner', lazy='dynamic')
    outfits = db.relationship('Outfit', backref='owner', lazy='dynamic')
    wear_logs = db.relationship('WearLog', backref='user', lazy='dynamic')
    
    def __init__(self, username, email, password, location=None, style_preference=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.location = location
        self.style_preference = style_preference
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 