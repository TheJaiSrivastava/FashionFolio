import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///wardrobe.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.static_folder, 'uploads'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max upload
        WEATHER_API_KEY=os.environ.get('WEATHER_API_KEY', ''),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Ensure upload folder exists
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
    except OSError:
        pass

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.clothing import clothing_bp
    from app.routes.outfits import outfits_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(clothing_bp, url_prefix='/clothing')
    app.register_blueprint(outfits_bp, url_prefix='/outfits')

    # Context processors
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    return app 