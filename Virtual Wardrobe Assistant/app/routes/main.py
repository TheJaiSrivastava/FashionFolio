from flask import Blueprint, render_template, current_app, request, jsonify
from flask_login import login_required, current_user
import requests
from datetime import datetime

from app.models.clothing import ClothingItem
from app.models.outfit import Outfit
from app.services.weather import get_weather_data
from app.services.outfit_suggester import suggest_outfits

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get some stats
    total_items = ClothingItem.query.filter_by(user_id=current_user.id).count()
    total_outfits = Outfit.query.filter_by(user_id=current_user.id).count()
    
    # Get recent items and outfits
    recent_items = ClothingItem.query.filter_by(user_id=current_user.id).order_by(
        ClothingItem.created_at.desc()).limit(5).all()
    recent_outfits = Outfit.query.filter_by(user_id=current_user.id).order_by(
        Outfit.created_at.desc()).limit(5).all()
    
    # Get weather data if location is set
    weather_data = None
    if current_user.location:
        weather_data = get_weather_data(current_user.location)
    
    # Get outfit suggestions based on weather and user preferences
    outfit_suggestions = []
    if weather_data:
        outfit_suggestions = suggest_outfits(
            current_user.id, 
            temperature=weather_data.get('temperature'), 
            weather_condition=weather_data.get('condition'),
            occasion=request.args.get('occasion', 'casual')
        )
    
    return render_template('dashboard.html',
                          total_items=total_items,
                          total_outfits=total_outfits,
                          recent_items=recent_items,
                          recent_outfits=recent_outfits,
                          weather_data=weather_data,
                          outfit_suggestions=outfit_suggestions)

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/api/weather')
@login_required
def weather_api():
    """API endpoint to get weather data"""
    location = request.args.get('location', current_user.location)
    if not location:
        return jsonify({'error': 'No location provided'}), 400
    
    weather_data = get_weather_data(location)
    if not weather_data:
        return jsonify({'error': 'Could not retrieve weather data'}), 500
    
    return jsonify(weather_data) 