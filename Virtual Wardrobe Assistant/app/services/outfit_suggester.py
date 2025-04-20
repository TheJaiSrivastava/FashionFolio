from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models.clothing import ClothingItem, Category
from app.models.outfit import Outfit, OutfitItem
from app.models.wear_log import WearLog
import random

def suggest_outfits(user_id, temperature=None, weather_condition=None, occasion='casual', limit=5):
    """
    Suggest outfits based on various criteria
    
    Args:
        user_id (int): User ID
        temperature (float, optional): Current temperature in Celsius
        weather_condition (str, optional): Current weather condition
        occasion (str, optional): Occasion to dress for
        limit (int, optional): Maximum number of suggestions to return
        
    Returns:
        list: Suggested outfits with reasoning
    """
    # Start with existing outfits that the user has created
    outfit_query = Outfit.query.filter_by(user_id=user_id)
    
    # Filter by occasion if specified
    if occasion:
        outfit_query = outfit_query.filter_by(occasion=occasion)
    
    # Filter by temperature if provided
    is_raining = weather_condition and 'rain' in weather_condition.lower()
    if temperature is not None:
        outfit_query = outfit_query.filter(
            (Outfit.weather_min_temp.is_(None) | (Outfit.weather_min_temp <= temperature)),
            (Outfit.weather_max_temp.is_(None) | (Outfit.weather_max_temp >= temperature))
        )
    
    # Get all matching outfits
    existing_outfits = outfit_query.all()
    
    # If we have enough suggestions from existing outfits, prioritize them
    suggested_outfits = []
    
    # Add a reason field to each suggestion
    for outfit in existing_outfits:
        # Skip outfits that are not suitable for rain if it's raining
        if is_raining:
            # Check if outfit has waterproof outerwear
            has_waterproof = False
            for outfit_item in outfit.outfit_items:
                if (outfit_item.clothing_item.category.name in ['Jacket', 'Coat', 'Outerwear'] 
                    and outfit_item.clothing_item.is_waterproof):
                    has_waterproof = True
                    break
            
            if not has_waterproof:
                continue
        
        # Calculate when this outfit was last worn
        last_wear = WearLog.query.filter_by(
            outfit_id=outfit.id
        ).order_by(WearLog.date.desc()).first()
        
        reason = "Matches your style preference"
        
        if last_wear:
            days_since_worn = (datetime.now().date() - last_wear.date).days
            if days_since_worn > 30:
                reason = f"Not worn in {days_since_worn} days"
            else:
                reason = f"Last worn {days_since_worn} days ago"
        else:
            reason = "Never worn before"
        
        suggested_outfits.append({
            'outfit': outfit,
            'reason': reason,
            'is_generated': False
        })
    
    # If we don't have enough existing outfits, generate new ones
    if len(suggested_outfits) < limit:
        # Generate outfits from individual clothing items
        generated_count = limit - len(suggested_outfits)
        generated_outfits = generate_outfits(
            user_id, 
            temperature, 
            weather_condition, 
            occasion, 
            generated_count
        )
        
        suggested_outfits.extend(generated_outfits)
    
    # Sort by favorite status and last worn date
    suggested_outfits.sort(key=lambda x: (
        not x['outfit'].is_favorite if not x.get('is_generated', False) else False,
        x['outfit'].last_worn or datetime.min if not x.get('is_generated', False) else datetime.min
    ))
    
    # Return the top suggestions up to the limit
    return suggested_outfits[:limit]

def generate_outfits(user_id, temperature=None, weather_condition=None, occasion='casual', limit=3):
    """
    Generate new outfit combinations from individual clothing items
    
    Args:
        user_id (int): User ID
        temperature (float, optional): Current temperature in Celsius
        weather_condition (str, optional): Current weather condition
        occasion (str, optional): Occasion to dress for
        limit (int, optional): Maximum number of outfits to generate
        
    Returns:
        list: Generated outfit suggestions
    """
    # Determine if it's raining
    is_raining = weather_condition and 'rain' in weather_condition.lower()
    
    # Build query for suitable clothing items
    query = ClothingItem.query.filter_by(user_id=user_id)
    
    # Filter by temperature if provided
    if temperature is not None:
        query = query.filter(
            (ClothingItem.weather_min_temp.is_(None) | (ClothingItem.weather_min_temp <= temperature)),
            (ClothingItem.weather_max_temp.is_(None) | (ClothingItem.weather_max_temp >= temperature))
        )
    
    # Filter by occasion if provided
    if occasion:
        query = query.filter(
            (ClothingItem.occasion.is_(None)) | 
            (ClothingItem.occasion == '') | 
            (ClothingItem.occasion == occasion)
        )
    
    # Get all suitable items grouped by category
    items_by_category = {}
    for item in query.all():
        if item.category.name not in items_by_category:
            items_by_category[item.category.name] = []
        items_by_category[item.category.name].append(item)
    
    # Define essential categories for different occasions
    essential_categories = {
        'casual': ['T-shirt', 'Shirt', 'Jeans', 'Pants', 'Shorts'],
        'formal': ['Dress Shirt', 'Suit', 'Slacks', 'Dress', 'Blazer'],
        'business': ['Shirt', 'Blouse', 'Slacks', 'Skirt', 'Blazer'],
        'sporty': ['T-shirt', 'Shorts', 'Sweatpants', 'Sports Bra']
    }
    
    # Use casual as default
    required_categories = essential_categories.get(occasion, essential_categories['casual'])
    
    # Add outerwear if cold or raining
    if temperature and temperature < 15 or is_raining:
        required_categories.append('Jacket')
        required_categories.append('Coat')
        required_categories.append('Outerwear')
    
    # Generate outfit combinations
    generated_outfits = []
    attempts = 0
    max_attempts = 20  # Prevent infinite loops
    
    while len(generated_outfits) < limit and attempts < max_attempts:
        attempts += 1
        
        # Create a new outfit
        outfit = Outfit(
            name=f"Suggested {occasion.capitalize()} Outfit",
            description=f"Generated for {temperature}°C, {weather_condition if weather_condition else 'any weather'}",
            occasion=occasion,
            user_id=user_id,
            weather_min_temp=temperature - 5 if temperature else None,
            weather_max_temp=temperature + 5 if temperature else None
        )
        
        # Add items from required categories
        outfit_items = []
        layer_order = 1
        
        # Check if we have the essential categories
        missing_categories = []
        for category in required_categories:
            if category not in items_by_category or not items_by_category[category]:
                missing_categories.append(category)
        
        if missing_categories:
            reason = f"Missing items in categories: {', '.join(missing_categories)}"
            continue
        
        # Add items from each required category
        for category in required_categories:
            # Skip if no items in this category
            if category not in items_by_category or not items_by_category[category]:
                continue
            
            # Select a random item from this category
            # Prioritize items that haven't been worn recently
            category_items = items_by_category[category]
            
            # Get the least recently worn item
            least_worn_item = None
            oldest_wear_date = datetime.now().date()
            
            for item in category_items:
                last_wear = WearLog.query.filter_by(
                    clothing_item_id=item.id
                ).order_by(WearLog.date.desc()).first()
                
                if not last_wear:
                    # Never worn, prioritize this item
                    least_worn_item = item
                    break
                
                if last_wear.date < oldest_wear_date:
                    oldest_wear_date = last_wear.date
                    least_worn_item = item
            
            # If we couldn't find a least worn item, just pick a random one
            selected_item = least_worn_item or random.choice(category_items)
            
            # For rainy weather, make sure outerwear is waterproof
            if is_raining and category in ['Jacket', 'Coat', 'Outerwear'] and not selected_item.is_waterproof:
                # Try to find a waterproof alternative
                waterproof_items = [item for item in category_items if item.is_waterproof]
                if waterproof_items:
                    selected_item = random.choice(waterproof_items)
                else:
                    # If no waterproof items, this outfit won't work for rain
                    break
            
            # Add this item to our outfit
            outfit_items.append({
                'item': selected_item,
                'layer_order': layer_order
            })
            layer_order += 1
        
        # Check if we have a complete outfit
        if len(outfit_items) >= 2:  # At least 2 items for a minimally complete outfit
            # Add outfit items
            for item_data in outfit_items:
                outfit_item = OutfitItem(
                    outfit_id=outfit.id if outfit.id else None,
                    clothing_item_id=item_data['item'].id,
                    layer_order=item_data['layer_order']
                )
                outfit.outfit_items.append(outfit_item)
            
            # Generate reason for suggestion
            reason = f"Generated for {temperature}°C" if temperature else "Generated based on your style"
            if is_raining:
                reason += ", with rain protection"
            
            generated_outfits.append({
                'outfit': outfit,
                'reason': reason,
                'is_generated': True
            })
    
    return generated_outfits 