import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image

from app import db
from app.models.clothing import ClothingItem, Category, Color, Season
from app.models.wear_log import WearLog
from app.forms.clothing import ClothingItemForm, CategoryForm, WearLogForm

wardrobe_bp = Blueprint('wardrobe', __name__, url_prefix='/wardrobe')

# Helper functions
def allowed_file(filename):
    """Check if filename has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    """Save uploaded image with a unique filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Generate unique filename to prevent overwrites
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Resize image to standard size to save space
        img = Image.open(file)
        img = img.resize((800, 800), Image.LANCZOS)  # Maintain aspect ratio
        img.save(file_path)
        
        return unique_filename
    return None

# Routes
@wardrobe_bp.route('/')
@login_required
def index():
    """Show all clothing items in the wardrobe"""
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    color_id = request.args.get('color', type=int)
    season_name = request.args.get('season')
    occasion = request.args.get('occasion')
    
    # Base query
    query = ClothingItem.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if category_id:
        query = query.filter_by(category_id=category_id)
    if color_id:
        query = query.filter_by(color_id=color_id)
    if season_name:
        season = Season.query.filter_by(name=season_name).first()
        if season:
            query = query.filter(ClothingItem.seasons.contains(season))
    if occasion:
        query = query.filter_by(occasion=occasion)
    
    # Execute query
    items = query.order_by(ClothingItem.created_at.desc()).all()
    
    # Get all categories and colors for filter dropdowns
    categories = Category.query.all()
    colors = Color.query.all()
    seasons = Season.query.all()
    
    # Get common occasions from existing items
    occasions = db.session.query(ClothingItem.occasion).filter(
        ClothingItem.user_id == current_user.id,
        ClothingItem.occasion != None
    ).distinct().all()
    occasions = [o[0] for o in occasions if o[0]]
    
    return render_template('wardrobe/index.html', 
                          items=items,
                          categories=categories,
                          colors=colors,
                          seasons=seasons,
                          occasions=occasions,
                          selected_category=category_id,
                          selected_color=color_id,
                          selected_season=season_name,
                          selected_occasion=occasion)

@wardrobe_bp.route('/item/<int:item_id>')
@login_required
def item_detail(item_id):
    """Show details for a specific clothing item"""
    item = ClothingItem.query.get_or_404(item_id)
    
    # Ensure user owns this item
    if item.user_id != current_user.id:
        flash('You do not have permission to view this item.', 'danger')
        return redirect(url_for('wardrobe.index'))
    
    # Get wear history
    wear_logs = WearLog.query.filter_by(clothing_item_id=item.id).order_by(WearLog.date.desc()).all()
    
    return render_template('wardrobe/item_detail.html', item=item, wear_logs=wear_logs)

@wardrobe_bp.route('/item/add', methods=['GET', 'POST'])
@login_required
def add_item():
    """Add a new clothing item"""
    form = ClothingItemForm()
    
    # Populate select fields with database values
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]
    form.color_id.choices = [(c.id, c.name) for c in Color.query.order_by('name')]
    form.seasons.choices = [(s.id, s.name) for s in Season.query.order_by('name')]
    
    if form.validate_on_submit():
        # Handle image upload
        image_filename = None
        if form.image.data:
            image_filename = save_image(form.image.data)
        
        # Create new item
        item = ClothingItem(
            name=form.name.data,
            description=form.description.data,
            image_filename=image_filename,
            purchase_date=form.purchase_date.data,
            brand=form.brand.data,
            occasion=form.occasion.data,
            weather_min_temp=form.weather_min_temp.data,
            weather_max_temp=form.weather_max_temp.data,
            is_waterproof=form.is_waterproof.data,
            user_id=current_user.id,
            category_id=form.category_id.data,
            color_id=form.color_id.data
        )
        
        # Add selected seasons
        selected_seasons = Season.query.filter(Season.id.in_(form.seasons.data)).all()
        item.seasons = selected_seasons
        
        db.session.add(item)
        db.session.commit()
        
        flash('Item added successfully!', 'success')
        return redirect(url_for('wardrobe.item_detail', item_id=item.id))
    
    return render_template('wardrobe/item_form.html', form=form, title='Add New Item')

@wardrobe_bp.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    """Edit an existing clothing item"""
    item = ClothingItem.query.get_or_404(item_id)
    
    # Ensure user owns this item
    if item.user_id != current_user.id:
        flash('You do not have permission to edit this item.', 'danger')
        return redirect(url_for('wardrobe.index'))
    
    form = ClothingItemForm(obj=item)
    
    # Populate select fields with database values
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]
    form.color_id.choices = [(c.id, c.name) for c in Color.query.order_by('name')]
    form.seasons.choices = [(s.id, s.name) for s in Season.query.order_by('name')]
    
    # Pre-select current seasons
    if request.method == 'GET':
        form.seasons.data = [s.id for s in item.seasons]
    
    if form.validate_on_submit():
        # Handle image upload if new image provided
        if form.image.data:
            # Delete old image if it exists
            if item.image_filename:
                try:
                    old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.image_filename)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                except Exception as e:
                    current_app.logger.error(f"Error removing old image: {e}")
            
            # Save new image
            item.image_filename = save_image(form.image.data)
        
        # Update other fields
        item.name = form.name.data
        item.description = form.description.data
        item.purchase_date = form.purchase_date.data
        item.brand = form.brand.data
        item.occasion = form.occasion.data
        item.weather_min_temp = form.weather_min_temp.data
        item.weather_max_temp = form.weather_max_temp.data
        item.is_waterproof = form.is_waterproof.data
        item.category_id = form.category_id.data
        item.color_id = form.color_id.data
        
        # Update selected seasons
        selected_seasons = Season.query.filter(Season.id.in_(form.seasons.data)).all()
        item.seasons = selected_seasons
        
        db.session.commit()
        
        flash('Item updated successfully!', 'success')
        return redirect(url_for('wardrobe.item_detail', item_id=item.id))
    
    return render_template('wardrobe/item_form.html', form=form, item=item, title='Edit Item')

@wardrobe_bp.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    """Delete a clothing item"""
    item = ClothingItem.query.get_or_404(item_id)
    
    # Ensure user owns this item
    if item.user_id != current_user.id:
        flash('You do not have permission to delete this item.', 'danger')
        return redirect(url_for('wardrobe.index'))
    
    # Delete associated image if it exists
    if item.image_filename:
        try:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            current_app.logger.error(f"Error removing image: {e}")
    
    # Delete the item (cascade will handle related records)
    db.session.delete(item)
    db.session.commit()
    
    flash('Item deleted successfully.', 'success')
    return redirect(url_for('wardrobe.index'))

@wardrobe_bp.route('/item/<int:item_id>/log-wear', methods=['GET', 'POST'])
@login_required
def log_wear(item_id):
    """Log when an item is worn"""
    item = ClothingItem.query.get_or_404(item_id)
    
    # Ensure user owns this item
    if item.user_id != current_user.id:
        flash('You do not have permission to log wear for this item.', 'danger')
        return redirect(url_for('wardrobe.index'))
    
    form = WearLogForm()
    if form.validate_on_submit():
        log = WearLog(
            date=form.date.data,
            notes=form.notes.data,
            weather_condition=form.weather_condition.data,
            temperature=form.temperature.data,
            user_id=current_user.id,
            clothing_item_id=item.id
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Wear logged successfully!', 'success')
        return redirect(url_for('wardrobe.item_detail', item_id=item.id))
    
    # Default to today's date
    if request.method == 'GET':
        form.date.data = datetime.now().date()
    
    return render_template('wardrobe/log_wear.html', form=form, item=item)

@wardrobe_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    """Manage clothing categories"""
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data, description=form.description.data)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('wardrobe.manage_categories'))
    
    categories = Category.query.order_by(Category.name).all()
    return render_template('wardrobe/categories.html', form=form, categories=categories) 