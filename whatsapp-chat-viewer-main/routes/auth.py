# -*- coding: utf-8 -*-
import logging
from flask import Blueprint, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from db.operations import UserOperations

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['POST'])
def login():
    """Process login form"""
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        
        logging.info(f"Login attempt for email: {email}")
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email e senha são obrigatórios'}), 400
        
        user = UserOperations.get_user_by_email(email)
        if user and user.check_password(password):
            login_user(user, remember=True)
            logging.info(f"User logged in successfully: {email}")
            return jsonify({'success': True, 'redirect': url_for('templates.dashboard')})
        else:
            logging.warning(f"Failed login attempt for email: {email}")
            return jsonify({'success': False, 'message': 'Email ou senha incorretos'}), 401
            
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@bp.route('/logout', methods=['POST'])
def logout():
    """Process logout"""
    try:
        if current_user.is_authenticated:
            logging.info(f"User logged out: {current_user.email}")
            logout_user()
        return jsonify({'success': True, 'redirect': url_for('templates.login')})
    except Exception as e:
        logging.error(f"Error during logout: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@bp.route('/register', methods=['POST'])
def register():
    """Process registration form"""
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        
        logging.info(f"Registration attempt for email: {email}")
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email e senha são obrigatórios'}), 400
        
        existing_user = UserOperations.get_user_by_email(email)
        if existing_user:
            return jsonify({'success': False, 'message': 'Email já está em uso'}), 409
        
        user = UserOperations.create_user(email, password)
        if user:
            login_user(user, remember=True)
            logging.info(f"User registered and logged in: {email}")
            return jsonify({'success': True, 'redirect': url_for('templates.dashboard')})
        else:
            return jsonify({'success': False, 'message': 'Erro ao criar usuário'}), 500
            
    except Exception as e:
        logging.error(f"Error during registration: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500