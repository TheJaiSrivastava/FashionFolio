from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from app.models.clothing import ClothingItem, Category
from app.models.outfit import Outfit, OutfitItem
from app.models.wear_log import WearLog
from app.forms.outfit import OutfitForm, WearOutfitForm
from app.services.outfit_suggester import suggest_outfits
from app.services.weather import get_weather_data

outfits_bp = Blueprint('outfits', __name__, url_prefix='/outfits')

@outfits_bp.route('/')
@login_required
def index():
    """Show all outfits"""
    # Get filter parameters
    occasion = request.args.get('occasion')
    season = request.args.get('season')
    is_favorite = request.args.get('favorite', type=bool)
    
    # Base query
    query = Outfit.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if occasion:
        query = query.filter_by(occasion=occasion)
    if season:
        query = query.filter_by(season=season)
    if is_favorite is not None:
        query = query.filter_by(is_favorite=is_favorite)
    
    # Execute query
    outfits = query.order_by(Outfit.created_at.desc()).all()
    
    # Get common occasions and seasons from existing outfits
    occasions = db.session.query(Outfit.occasion).filter(
        Outfit.user_id == current_user.id,
        Outfit.occasion != None
    ).distinct().all()
    occasions = [o[0] for o in occasions if o[0]]
    
    seasons = db.session.query(Outfit.season).filter(
        Outfit.user_id == current_user.id,
        Outfit.season != None
    ).distinct().all()
    seasons = [s[0] for s in seasons if s[0]]
    
    return render_template('outfits/index.html',
                          outfits=outfits,
                          occasions=occasions,
                          seasons=seasons,
                          selected_occasion=occasion,
                          selected_season=season,
                          is_favorite=is_favorite)

@outfits_bp.route('/<int:outfit_id>')
@login_required
def detail(outfit_id):
    """Show details for a specific outfit"""
    outfit = Outfit.query.get_or_404(outfit_id)
    
    # Ensure user owns this outfit
    if outfit.user_id != current_user.id:
        flash('You do not have permission to view this outfit.', 'danger')
        return redirect(url_for('outfits.index'))
    
    # Get outfit items sorted by layer order
    outfit_items = outfit.outfit_items.order_by(OutfitItem.layer_order).all()
    
    # Get wear history
    wear_logs = WearLog.query.filter_by(outfit_id=outfit.id).order_by(WearLog.date.desc()).all()
    
    return render_template('outfits/detail.html', 
                          outfit=outfit, 
                          outfit_items=outfit_items,
                          wear_logs=wear_logs)

@outfits_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new outfit"""
    form = OutfitForm()
    
    if form.validate_on_submit():
        # Create new outfit
        outfit = Outfit(
            name=form.name.data,
            description=form.description.data,
            occasion=form.occasion.data,
            season=form.season.data,
            weather_min_temp=form.weather_min_temp.data,
            weather_max_temp=form.weather_max_temp.data,
            is_favorite=form.is_favorite.data,
            user_id=current_user.id
        )
        db.session.add(outfit)
        db.session.flush()  # Get ID for new outfit
        
        # Add outfit items
        for item_id, layer_order in request.form.getlist('clothing_items'):
            outfit_item = OutfitItem(
                outfit_id=outfit.id,
                clothing_item_id=item_id,
                layer_order=layer_order
            )
            db.session.add(outfit_item)
        
        db.session.commit()
        flash('Outfit created successfully!', 'success')
        return redirect(url_for('outfits.detail', outfit_id=outfit.id))
    
    # Get available clothing items for selection
    clothing_items = ClothingItem.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.all()
    
    return render_template('outfits/form.html', 
                          form=form, 
                          clothing_items=clothing_items,
                          categories=categories,
                          title='Create New Outfit')

@outfits_bp.route('/<int:outfit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(outfit_id):
    """Edit an existing outfit"""
    outfit = Outfit.query.get_or_404(outfit_id)
    
    # Ensure user owns this outfit
    if outfit.user_id != current_user.id:
        flash('You do not have permission to edit this outfit.', 'danger')
        return redirect(url_for('outfits.index'))
    
    form = OutfitForm(obj=outfit)
    
    if form.validate_on_submit():
        # Update outfit details
        outfit.name = form.name.data
        outfit.description = form.description.data
        outfit.occasion = form.occasion.data
        outfit.season = form.season.data
        outfit.weather_min_temp = form.weather_min_temp.data
        outfit.weather_max_temp = form.weather_max_temp.data
        outfit.is_favorite = form.is_favorite.data
        
        # Remove existing outfit items
        OutfitItem.query.filter_by(outfit_id=outfit.id).delete()
        
        # Add updated outfit items
        for item_data in request.form.getlist('clothing_items'):
            item_id, layer_order = item_data.split(',')
            outfit_item = OutfitItem(
                outfit_id=outfit.id,
                clothing_item_id=int(item_id),
                layer_order=int(layer_order)
            )
            db.session.add(outfit_item)
        
        db.session.commit()
        flash('Outfit updated successfully!', 'success')
        return redirect(url_for('outfits.detail', outfit_id=outfit.id))
    
    # Get current outfit items
    current_items = [(item.clothing_item_id, item.layer_order) 
                     for item in outfit.outfit_items.all()]
    
    # Get available clothing items for selection
    clothing_items = ClothingItem.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.all()
    
    return render_template('outfits/form.html', 
                          form=form, 
                          outfit=outfit,
                          current_items=current_items,
                          clothing_items=clothing_items,
                          categories=categories,
                          title='Edit Outfit')

@outfits_bp.route('/<int:outfit_id>/delete', methods=['POST'])
@login_required
def delete(outfit_id):
    """Delete an outfit"""
    outfit = Outfit.query.get_or_404(outfit_id)
    
    # Ensure user owns this outfit
    if outfit.user_id != current_user.id:
        flash('You do not have permission to delete this outfit.', 'danger')
        return redirect(url_for('outfits.index'))
    
    # Delete the outfit (cascade will handle related records)
    db.session.delete(outfit)
    db.session.commit()
    
    flash('Outfit deleted successfully.', 'success')
    return redirect(url_for('outfits.index'))

@outfits_bp.route('/<int:outfit_id>/toggle-favorite', methods=['POST'])
@login_required
def toggle_favorite(outfit_id):
    """Toggle favorite status for an outfit"""
    outfit = Outfit.query.get_or_404(outfit_id)
    
    # Ensure user owns this outfit
    if outfit.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    # Toggle favorite status
    outfit.is_favorite = not outfit.is_favorite
    db.session.commit()
    
    return jsonify({'success': True, 'is_favorite': outfit.is_favorite})

@outfits_bp.route('/<int:outfit_id>/log-wear', methods=['GET', 'POST'])
@login_required
def log_wear(outfit_id):
    """Log when an outfit is worn"""
    outfit = Outfit.query.get_or_404(outfit_id)
    
    # Ensure user owns this outfit
    if outfit.user_id != current_user.id:
        flash('You do not have permission to log wear for this outfit.', 'danger')
        return redirect(url_for('outfits.index'))
    
    form = WearOutfitForm()
    if form.validate_on_submit():
        # Create outfit wear log
        outfit_log = WearLog(
            date=form.date.data,
            notes=form.notes.data,
            weather_condition=form.weather_condition.data,
            temperature=form.temperature.data,
            user_id=current_user.id,
            outfit_id=outfit.id
        )
        db.session.add(outfit_log)
        
        # Also log wear for each individual item in the outfit
        for outfit_item in outfit.outfit_items:
            item_log = WearLog(
                date=form.date.data,
                user_id=current_user.id,
                clothing_item_id=outfit_item.clothing_item_id,
                outfit_id=outfit.id  # Link to the same outfit
            )
            db.session.add(item_log)
        
        db.session.commit()
        flash('Wear logged successfully!', 'success')
        return redirect(url_for('outfits.detail', outfit_id=outfit.id))
    
    # Default to today's date
    if request.method == 'GET':
        form.date.data = datetime.now().date()
        
        # If location is set, try to get current weather
        if current_user.location:
            weather = get_weather_data(current_user.location)
            if weather:
                form.weather_condition.data = weather.get('condition')
                form.temperature.data = weather.get('temperature')
    
    return render_template('outfits/log_wear.html', form=form, outfit=outfit)

@outfits_bp.route('/suggest')
@login_required
def suggest():
    """Suggest outfits based on criteria"""
    # Get filter parameters
    occasion = request.args.get('occasion', 'casual')
    temperature = request.args.get('temperature', type=float)
    weather_condition = request.args.get('weather_condition')
    
    # If no temperature specified but location is set, try to get current weather
    if temperature is None and current_user.location:
        weather = get_weather_data(current_user.location)
        if weather:
            temperature = weather.get('temperature')
            weather_condition = weather.get('condition')
    
    # Get outfit suggestions
    suggested_outfits = suggest_outfits(
        current_user.id,
        temperature=temperature,
        weather_condition=weather_condition,
        occasion=occasion
    )
    
    return render_template('outfits/suggestions.html',
                          outfits=suggested_outfits,
                          temperature=temperature,
                          weather_condition=weather_condition,
                          occasion=occasion) 