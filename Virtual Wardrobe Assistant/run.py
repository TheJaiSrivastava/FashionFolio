from app import create_app, db
from app.models.user import User
from app.models.clothing import ClothingItem, Category, Color
from app.models.outfit import Outfit, OutfitItem
from app.models.wear_log import WearLog

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'ClothingItem': ClothingItem, 
        'Category': Category, 
        'Color': Color,
        'Outfit': Outfit,
        'OutfitItem': OutfitItem,
        'WearLog': WearLog
    }

if __name__ == '__main__':
    app.run(debug=True) 