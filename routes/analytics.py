# -*- coding: utf-8 -*-
import logging
from datetime import date, datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from db.operations import MessageOperations

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/daily-stats', methods=['GET'])
@login_required
def get_daily_stats():
    """Get daily statistics"""
    try:
        target_date_str = request.args.get('date')
        
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        logging.info(f"Getting daily stats for date: {target_date}")
        
        stats = MessageOperations.get_daily_stats(target_date)
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logging.error(f"Error getting daily stats: {e}")
        return jsonify({'success': False, 'message': 'Erro ao carregar estatísticas'}), 500

@bp.route('/weekly-stats', methods=['GET'])
@login_required
def get_weekly_stats():
    """Get weekly statistics"""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        
        logging.info(f"Getting weekly stats from {start_date} to {end_date}")
        
        weekly_stats = []
        current_date = start_date
        
        while current_date <= end_date:
            daily_stats = MessageOperations.get_daily_stats(current_date)
            weekly_stats.append(daily_stats)
            current_date += timedelta(days=1)
        
        # Calculate totals
        total_messages = sum(day['total_messages'] for day in weekly_stats)
        total_ai_messages = sum(day['ai_messages'] for day in weekly_stats)
        total_cost = sum(day['cost'] for day in weekly_stats)
        
        return jsonify({
            'success': True,
            'weekly_stats': weekly_stats,
            'totals': {
                'total_messages': total_messages,
                'total_ai_messages': total_ai_messages,
                'total_cost': total_cost,
                'period': f"{start_date.isoformat()} to {end_date.isoformat()}"
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting weekly stats: {e}")
        return jsonify({'success': False, 'message': 'Erro ao carregar estatísticas semanais'}), 500

@bp.route('/monthly-stats', methods=['GET'])
@login_required
def get_monthly_stats():
    """Get monthly statistics"""
    try:
        today = date.today()
        start_date = today.replace(day=1)
        
        logging.info(f"Getting monthly stats from {start_date} to {today}")
        
        monthly_stats = []
        current_date = start_date
        
        while current_date <= today:
            daily_stats = MessageOperations.get_daily_stats(current_date)
            monthly_stats.append(daily_stats)
            current_date += timedelta(days=1)
        
        # Calculate totals
        total_messages = sum(day['total_messages'] for day in monthly_stats)
        total_ai_messages = sum(day['ai_messages'] for day in monthly_stats)
        total_cost = sum(day['cost'] for day in monthly_stats)
        
        return jsonify({
            'success': True,
            'monthly_stats': monthly_stats,
            'totals': {
                'total_messages': total_messages,
                'total_ai_messages': total_ai_messages,
                'total_cost': total_cost,
                'period': f"{start_date.isoformat()} to {today.isoformat()}"
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting monthly stats: {e}")
        return jsonify({'success': False, 'message': 'Erro ao carregar estatísticas mensais'}), 500