# -*- coding: utf-8 -*-
import logging
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('templates', __name__)

@bp.route('/')
def index():
    """Home page - redirect to login if not authenticated, chat if authenticated"""
    logging.info("Home page accessed")
    if current_user.is_authenticated:
        return redirect(url_for('templates.chat'))
    return redirect(url_for('templates.login'))

@bp.route('/login')
def login():
    """Login page"""
    logging.info("Login page accessed")
    if current_user.is_authenticated:
        return redirect(url_for('templates.chat'))
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