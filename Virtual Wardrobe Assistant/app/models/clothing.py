from datetime import datetime
from app import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    
    # Relationships
    clothing_items = db.relationship('ClothingItem', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Color(db.Model):
    __tablename__ = 'colors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    hex_code = db.Column(db.String(7))  # Hex color code (e.g., #FFFFFF)
    
    # Relationships
    clothing_items = db.relationship('ClothingItem', backref='color', lazy='dynamic')
    
    def __repr__(self):
        return f'<Color {self.name}>'

class Season(db.Model):
    __tablename__ = 'seasons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Season {self.name}>'

# Association table for many-to-many relationship between ClothingItem and Season
clothing_season = db.Table('clothing_season',
    db.Column('clothing_id', db.Integer, db.ForeignKey('clothing_items.id'), primary_key=True),
    db.Column('season_id', db.Integer, db.ForeignKey('seasons.id'), primary_key=True)
)

class ClothingItem(db.Model):
    __tablename__ = 'clothing_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(255))
    purchase_date = db.Column(db.Date)
    brand = db.Column(db.String(100))
    occasion = db.Column(db.String(100))  # Formal, casual, work, etc.
    weather_min_temp = db.Column(db.Float)  # Minimum temperature this is suitable for
    weather_max_temp = db.Column(db.Float)  # Maximum temperature this is suitable for
    is_waterproof = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'))
    
    # Relationships
    seasons = db.relationship('Season', secondary=clothing_season, backref=db.backref('clothing_items', lazy='dynamic'))
    outfit_items = db.relationship('OutfitItem', backref='clothing_item', lazy='dynamic')
    wear_logs = db.relationship('WearLog', backref='clothing_item', lazy='dynamic')
    
    def __repr__(self):
        return f'<ClothingItem {self.name}>'
    
    @property
    def wear_count(self):
        """Return number of times this item has been worn"""
        return self.wear_logs.count()
    
    @property
    def last_worn(self):
        """Return the date this item was last worn"""
        last_log = self.wear_logs.order_by(db.desc('date')).first()
        return last_log.date if last_log else None
    
    def suitable_for_weather(self, temperature, is_raining=False):
        """Check if item is suitable for given weather conditions"""
        temp_suitable = True
        if self.weather_min_temp is not None and temperature < self.weather_min_temp:
            temp_suitable = False
        if self.weather_max_temp is not None and temperature > self.weather_max_temp:
            temp_suitable = False
        
        rain_suitable = True if not is_raining else self.is_waterproof
        
        return temp_suitable and rain_suitable 