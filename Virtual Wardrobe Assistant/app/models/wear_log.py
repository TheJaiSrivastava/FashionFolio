from datetime import datetime
from app import db

class WearLog(db.Model):
    __tablename__ = 'wear_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    notes = db.Column(db.Text)
    weather_condition = db.Column(db.String(50))  # Sunny, Rainy, etc.
    temperature = db.Column(db.Float)  # Temperature in Celsius
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    clothing_item_id = db.Column(db.Integer, db.ForeignKey('clothing_items.id'))
    outfit_id = db.Column(db.Integer, db.ForeignKey('outfits.id'))
    
    def __repr__(self):
        return f'<WearLog {self.id} on {self.date}>' 