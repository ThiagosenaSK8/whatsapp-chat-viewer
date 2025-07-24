# -*- coding: utf-8 -*-
import os
import logging
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

from config import config
from db.connection import init_database
from db.models import User
import templates
from routes import auth, chat, analytics, files, settings

load_dotenv()

def create_app(config_name=None):
    """Create and configure Flask application"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Production logging configuration
    if config_name == 'production':
        if not app.debug:
            # File handler for production
            file_handler = logging.FileHandler('app.log')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Application startup')
    else:
        # Console logging for development
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Initialize database
    init_database(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(templates.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(analytics.bp)
    app.register_blueprint(files.bp)
    app.register_blueprint(settings.bp)
    
    app.logger.info(f"Flask application created with {config_name} configuration")
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)