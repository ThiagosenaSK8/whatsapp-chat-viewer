# -*- coding: utf-8 -*-
import logging
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('templates', __name__)

@bp.route('/')
def index():
    """Home page - redirect to login if not authenticated, dashboard if authenticated"""
    logging.info("Home page accessed")
    if current_user.is_authenticated:
        return redirect(url_for('templates.dashboard'))
    return redirect(url_for('templates.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page - main landing page after login"""
    logging.info(f"Dashboard page accessed by user: {current_user.email}")
    return render_template('pages/dashboard.html')

@bp.route('/login')
def login():
    """Login page"""
    logging.info("Login page accessed")
    if current_user.is_authenticated:
        return redirect(url_for('templates.dashboard'))
    return render_template('pages/login.html')

@bp.route('/chat')
@login_required
def chat():
    """Main chat page"""
    logging.info(f"Chat page accessed by user: {current_user.email}")
    return render_template('pages/chat.html')

@bp.route('/analytics')
@login_required
def analytics():
    """Analytics page"""
    logging.info(f"Analytics page accessed by user: {current_user.email}")
    return render_template('pages/analytics.html')

@bp.route('/settings')
@login_required
def settings():
    """Settings page"""
    logging.info(f"Settings page accessed by user: {current_user.email}")
    return render_template('pages/settings.html')