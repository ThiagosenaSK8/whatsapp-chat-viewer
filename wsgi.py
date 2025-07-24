# -*- coding: utf-8 -*-
"""
WSGI entry point for production deployment
"""
import os
from app import create_app

# Create application instance for production
application = create_app('production')

if __name__ == "__main__":
    application.run()