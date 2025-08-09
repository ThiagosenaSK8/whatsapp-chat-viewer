# -*- coding: utf-8 -*-
import logging
import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from db.connection import check_db_connection
from utils.config import config
from utils.logs import log_manager
import requests
import time

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/webhook-config', methods=['GET'])
@login_required
def get_webhook_config():
    """Get current webhook configuration with detailed status"""
    try:
        logging.info(f"Getting webhook config for user: {current_user.email}")
        
        # Force reload configuration to ensure latest data
        webhook_url = config.reload_config()
        
        # Get detailed configuration status
        config_status = config.get_config_status()
        
        # Test webhook connectivity only if URL exists
        webhook_status = {'status': 'not_configured', 'message': 'URL não configurada', 'response_time': None}
        if webhook_url:
            webhook_status = test_webhook_connection(webhook_url)
        
        config_data = {
            'webhook_url': webhook_url,
            'webhook_status': webhook_status,
            'config_details': config_status,  # Add detailed status
            'last_checked': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'config': config_data})
        
    except Exception as e:
        logging.error(f"Error getting webhook config: {e}")
        return jsonify({'success': False, 'message': 'Erro ao carregar configurações'}), 500

@bp.route('/webhook-config', methods=['POST'])
@login_required
def update_webhook_config():
    """Update webhook configuration"""
    try:
        data = request.get_json()
        new_webhook_url = data.get('webhook_url', '').strip()
        
        logging.info(f"Updating webhook config for user: {current_user.email}")
        logging.info(f"New webhook URL: {new_webhook_url}")
        
        if not new_webhook_url:
            return jsonify({'success': False, 'message': 'URL do webhook é obrigatória'}), 400
        
        # Validate URL format
        if not new_webhook_url.startswith(('http://', 'https://')):
            return jsonify({'success': False, 'message': 'URL deve começar com http:// ou https://'}), 400
        
        # Update global configuration (this will save to file)
        config.webhook_url = new_webhook_url
        
        # Test the new webhook URL after a brief delay to ensure it's saved
        time.sleep(0.1)
        webhook_status = test_webhook_connection(new_webhook_url)
        
        logging.info(f"Webhook URL updated successfully by {current_user.email}")
        
        return jsonify({
            'success': True, 
            'message': 'Configuração do webhook atualizada e salva',
            'webhook_status': webhook_status
        })
        
    except Exception as e:
        logging.error(f"Error updating webhook config: {e}")
        return jsonify({'success': False, 'message': 'Erro ao atualizar configurações'}), 500

@bp.route('/test-webhook', methods=['POST'])
@login_required
def test_webhook():
    """Test webhook connectivity"""
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url') or config.webhook_url
        
        logging.info(f"Testing webhook for user: {current_user.email}")
        
        if not webhook_url:
            return jsonify({'success': False, 'message': 'URL do webhook não configurada'}), 400
        
        # Test the webhook
        status = test_webhook_connection(webhook_url)
        
        return jsonify({
            'success': True,
            'webhook_status': status,
            'message': f"Teste realizado - Status: {status['status']}"
        })
        
    except Exception as e:
        logging.error(f"Error testing webhook: {e}")
        return jsonify({'success': False, 'message': 'Erro ao testar webhook'}), 500

@bp.route('/database-status', methods=['GET'])
@login_required
def get_database_status():
    """Get database connection status"""
    try:
        logging.info(f"Checking database status for user: {current_user.email}")
        
        # Test database connection
        is_connected = check_db_connection()
        
        # Get database info
        database_url = config.database_url
        # Remove credentials from URL for display
        display_url = database_url.split('@')[-1] if '@' in database_url else database_url
        
        status = {
            'connected': is_connected,
            'database_url': display_url,
            'status': 'Conectado' if is_connected else 'Desconectado',
            'last_checked': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'status': status})
        
    except Exception as e:
        logging.error(f"Error checking database status: {e}")
        return jsonify({'success': False, 'message': 'Erro ao verificar status do banco'}), 500

@bp.route('/logs', methods=['GET'])
@login_required
def get_logs():
    """Get application logs"""
    try:
        # Get log level filter
        level = request.args.get('level', 'all').upper()
        lines = int(request.args.get('lines', 100))
        
        logging.info(f"Getting logs for user: {current_user.email} - Level: {level}, Lines: {lines}")
        
        # Get real logs from log manager
        logs = log_manager.get_logs(level, lines)
        
        # Ensure we have some logs to show
        if not logs:
            logs = [{
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': 'Sistema de logs ativo - aguardando atividade',
                'module': 'logs'
            }]
        
        return jsonify({'success': True, 'logs': logs})
        
    except Exception as e:
        logging.error(f"Error getting logs: {e}")
        return jsonify({'success': False, 'message': 'Erro ao carregar logs'}), 500

@bp.route('/clear-logs', methods=['POST'])
@login_required
def clear_logs():
    """Clear application logs"""
    try:
        logging.info(f"Clearing logs requested by user: {current_user.email}")
        
        # Clear real logs
        log_manager.clear_logs()
        
        return jsonify({'success': True, 'message': 'Logs limpos com sucesso'})
        
    except Exception as e:
        logging.error(f"Error clearing logs: {e}")
        return jsonify({'success': False, 'message': 'Erro ao limpar logs'}), 500

def test_webhook_connection(webhook_url):
    """Test webhook connectivity"""
    if not webhook_url:
        return {
            'status': 'not_configured',
            'message': 'URL não configurada',
            'response_time': None
        }
    
    try:
        start_time = datetime.now()
        
        # Send test request
        test_data = {
            'phone_number': '+5511999999999',
            'message': 'Teste de conectividade do webhook',
            'test': True
        }
        
        response = requests.post(
            webhook_url, 
            json=test_data, 
            timeout=10,
            headers={'User-Agent': 'WhatsApp-Chat-Viewer/1.0'}
        )
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            return {
                'status': 'online',
                'message': 'Webhook respondendo normalmente',
                'status_code': response.status_code,
                'response_time': round(response_time, 2)
            }
        else:
            return {
                'status': 'error',
                'message': f'Webhook retornou erro: {response.status_code}',
                'status_code': response.status_code,
                'response_time': round(response_time, 2)
            }
            
    except requests.exceptions.Timeout:
        return {
            'status': 'timeout',
            'message': 'Timeout - Webhook não respondeu em 10 segundos',
            'response_time': None
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': 'offline',
            'message': 'Não foi possível conectar ao webhook',
            'response_time': None
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Erro ao testar webhook: {str(e)}',
            'response_time': None
        }