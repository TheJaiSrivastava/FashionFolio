from datetime import datetime
from app import db

class Outfit(db.Model):
    __tablename__ = 'outfits'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    occasion = db.Column(db.String(100))  # Formal, casual, work, etc.
    season = db.Column(db.String(50))  # Summer, winter, spring, fall, or combinations
    weather_min_temp = db.Column(db.Float)  # Minimum temperature this is suitable for
    weather_max_temp = db.Column(db.Float)  # Maximum temperature this is suitable for
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    outfit_items = db.relationship('OutfitItem', backref='outfit', lazy='dynamic', 
                                  cascade='all, delete-orphan')
    wear_logs = db.relationship('WearLog', backref='outfit', lazy='dynamic')
    
    def __repr__(self):
        return f'<Outfit {self.name}>'
    
    @property
    def wear_count(self):
        """Return number of times this outfit has been worn"""
        return self.wear_logs.count()
    
    @property
    def last_worn(self):
        """Return the date this outfit was last worn"""
        last_log = self.wear_logs.order_by(db.desc('date')).first()
        return last_log.date if last_log else None
    
    def suitable_for_weather(self, temperature, is_raining=False):
        """Check if outfit is suitable for given weather conditions"""
        temp_suitable = True
        if self.weather_min_temp is not None and temperature < self.weather_min_temp:
            temp_suitable = False
        if self.weather_max_temp is not None and temperature > self.weather_max_temp:
            temp_suitable = False
            
        # Check if all necessary items are waterproof in case of rain
        rain_suitable = True
        if is_raining:
            outer_items = [item.clothing_item for item in self.outfit_items 
                          if item.clothing_item.category.name in ['Jacket', 'Coat', 'Outerwear']]
            if outer_items:
                rain_suitable = any(item.is_waterproof for item in outer_items)
            else:
                rain_suitable = False
                
        return temp_suitable and rain_suitable

class OutfitItem(db.Model):
    __tablename__ = 'outfit_items'
    
    id = db.Column(db.Integer, primary_key=True)
    layer_order = db.Column(db.Integer)  # Order of layering (1 = innermost)
    
    # Foreign keys
    outfit_id = db.Column(db.Integer, db.ForeignKey('outfits.id'), nullable=False)
    clothing_item_id = db.Column(db.Integer, db.ForeignKey('clothing_items.id'), nullable=False)
    
    def __repr__(self):
        return f'<OutfitItem {self.id}>' 