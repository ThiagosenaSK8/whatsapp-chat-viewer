# -*- coding: utf-8 -*-
import os
import logging
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

from db.connection import init_database
from db.models import User, db
from utils.config import config
from utils.logs import log_manager
import templates
from routes import auth, chat, analytics, settings

load_dotenv()

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configuration using centralized config
    app.config['SECRET_KEY'] = config.secret_key
    app.config['DEBUG'] = config.flask_debug
    
    # Logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize log manager (this sets up log capturing)
    # log_manager is already initialized when imported
    
    # Initialize database
    init_database(app)
    
    # Clean up database connections after each request
    @app.teardown_appcontext
    def close_db(error):
        db.session.remove()
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Handle favicon.ico requests to avoid 404 errors in console
    @app.route('/favicon.ico')
    def favicon():
        """Return empty response for favicon to avoid 404 errors"""
        return '', 204
    
    # Register blueprints
    app.register_blueprint(templates.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(analytics.bp)
    app.register_blueprint(settings.bp)
    
    logging.info("Flask application created and configured")
    return app

# Create application instance for Gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.port, debug=app.config['DEBUG'])