# -*- coding: utf-8 -*-
import logging
import requests
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from db.operations import PhoneOperations, MessageOperations
from utils.config import config
from urllib.parse import urlparse
import mimetypes

bp = Blueprint('chat', __name__, url_prefix='/chat')

# Upload configurations
UPLOAD_FOLDER = 'static/uploads'
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp',  # Images
    'mp4', 'avi', 'mov', 'wmv', 'webm',   # Videos
    'mp3', 'wav', 'ogg', 'm4a', 'aac',    # Audio
    'pdf', 'doc', 'docx', 'txt',          # Documents
    'zip', 'rar'                          # Archives
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if extension in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
        return 'image'
    elif extension in {'mp4', 'avi', 'mov', 'wmv', 'webm'}:
        return 'video'
    elif extension in {'mp3', 'wav', 'ogg', 'm4a', 'aac'}:
        return 'audio'
    elif extension in {'pdf'}:
        return 'pdf'
    elif extension in {'doc', 'docx'}:
        return 'document'
    else:
        return 'file'

@bp.route('/phones', methods=['GET'])
@login_required
def get_phone_numbers():
    """Get all phone numbers"""
    try:
        logging.info(f"Getting phone numbers for user: {current_user.email}")
        phones = PhoneOperations.get_all_phone_numbers()
        
        phone_list = []
        for phone in phones:
            phone_list.append({
                'id': phone.id,
                'number': phone.number,
                'ai_active': phone.ai_active,
                'created_at': phone.created_at.isoformat() if phone.created_at else None
            })
        
        return jsonify({'success': True, 'phones': phone_list})
    except Exception as e:
        logging.error(f"Error getting phone numbers: {e}")
        return jsonify({'success': False, 'message': 'Erro ao carregar números'}), 500

@bp.route('/messages/<phone_number>', methods=['GET'])
@login_required
def get_messages(phone_number):
    """Get messages for a specific phone number"""
    try:
        logging.info(f"Getting messages for phone: {phone_number}")
        messages = MessageOperations.get_messages_by_phone(phone_number)
        
        message_list = []
        for message in messages:
            message_list.append(message.to_dict())
        
        return jsonify({'success': True, 'messages': message_list})
    except Exception as e:
        logging.error(f"Error getting messages for phone {phone_number}: {e}")
        return jsonify({'success': False, 'message': 'Erro ao carregar mensagens'}), 500

@bp.route('/send-message', methods=['POST'])
@login_required
def send_message():
    """Send a message"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        content = data.get('content', '')
        attachment_url = data.get('attachment_url')
        attachment_full_url = data.get('attachment_full_url')
        attachment_name = data.get('attachment_name')
        attachment_type = data.get('attachment_type')
        attachment_size = data.get('attachment_size')
        
        logging.info(f"Sending message to phone: {phone_number}")
        
        if not phone_number:
            return jsonify({'success': False, 'message': 'Número é obrigatório'}), 400
        
        if not content and not attachment_url:
            return jsonify({'success': False, 'message': 'Conteúdo ou anexo são obrigatórios'}), 400
        
        # Save message to database as 'user' type (sent by admin)
        message = MessageOperations.create_message(
            phone_number, content, 'user',
            attachment_url, attachment_full_url, attachment_name, attachment_type, attachment_size
        )
        if not message:
            return jsonify({'success': False, 'message': 'Erro ao salvar mensagem'}), 500
        
        # Send to webhook using global configuration
        webhook_url = config.webhook_url
        webhook_data = {
            'phone_number': phone_number,
            'message': content,
            'attachment_url': attachment_url,
            'attachment_full_url': attachment_full_url,
            'attachment_name': attachment_name,
            'attachment_type': attachment_type
        }
        
        webhook_sent = False
        if webhook_url:
            try:
                response = requests.post(webhook_url, json=webhook_data, timeout=10)
                logging.info(f"Webhook response status: {response.status_code}")
                webhook_sent = True
            except requests.RequestException as e:
                logging.error(f"Error calling webhook: {e}")
                # Continue even if webhook fails - message is saved
        else:
            logging.warning("No webhook URL configured - message not sent to external service")
        
        return jsonify({
            'success': True, 
            'message': message.to_dict(),
            'webhook_sent': webhook_sent
        })
        
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@bp.route('/toggle-ai/<int:phone_id>', methods=['POST'])
@login_required
def toggle_ai(phone_id):
    """Toggle AI status for a phone number"""
    try:
        logging.info(f"Toggling AI status for phone ID: {phone_id}")
        
        success = PhoneOperations.toggle_ai_status(phone_id)
        if success:
            return jsonify({'success': True, 'message': 'Status da IA alterado com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Número não encontrado'}), 404
            
    except Exception as e:
        logging.error(f"Error toggling AI status for phone {phone_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@bp.route('/add-phone', methods=['POST'])
@login_required
def add_phone():
    """Add a new phone number"""
    try:
        data = request.get_json()
        phone_number = data.get('number')
        
        logging.info(f"Adding new phone number: {phone_number}")
        
        if not phone_number:
            return jsonify({'success': False, 'message': 'Número é obrigatório'}), 400
        
        phone = PhoneOperations.create_phone_number(phone_number)
        if phone:
            return jsonify({
                'success': True, 
                'phone': {
                    'id': phone.id,
                    'number': phone.number,
                    'ai_active': phone.ai_active,
                    'created_at': phone.created_at.isoformat() if phone.created_at else None
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Erro ao criar número'}), 500
            
    except Exception as e:
        logging.error(f"Error adding phone number: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@bp.route('/upload-attachment', methods=['POST'])
@login_required
def upload_attachment():
    """Upload an attachment file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        phone_number = request.form.get('phone_number')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
        if not phone_number:
            return jsonify({'success': False, 'message': 'Número de telefone é obrigatório'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_UPLOAD_SIZE:
            return jsonify({'success': False, 'message': 'Arquivo muito grande. Máximo: 50MB'}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(os.getcwd(), UPLOAD_FOLDER)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Generate public URLs
        file_url = f"/chat/uploads/{unique_filename}"
        file_full_url = f"{request.scheme}://{request.host}{file_url}"
        
        logging.info(f"File uploaded successfully: {unique_filename} for phone: {phone_number}")
        
        return jsonify({
            'success': True,
            'url': file_url,
            'full_url': file_full_url,
            'filename': filename,
            'size': file_size,
            'type': get_file_type(filename)
        })
        
    except Exception as e:
        logging.error(f"Error uploading attachment: {e}")
        return jsonify({'success': False, 'message': 'Erro ao fazer upload do arquivo'}), 500

@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    try:
        upload_dir = os.path.join(os.getcwd(), UPLOAD_FOLDER)
        return send_from_directory(upload_dir, filename)
    except Exception as e:
        logging.error(f"Error serving file {filename}: {e}")
        return "Arquivo não encontrado", 404

@bp.route('/receive-message', methods=['POST'])
def receive_message():
    """Receive incoming messages with attachments from webhook"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        content = data.get('message', '')
        attachment_url = data.get('attachment_url')
        attachment_name = data.get('attachment_name')
        attachment_type = data.get('attachment_type')
        
        logging.info(f"Receiving message from phone: {phone_number}")
        logging.info(f"Message data: {data}")
        
        if not phone_number:
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        if not content and not attachment_url:
            return jsonify({'success': False, 'message': 'Content or attachment is required'}), 400
        
        # Initialize variables for local attachment handling
        local_attachment_url = None
        local_attachment_full_url = None
        local_attachment_name = attachment_name
        local_attachment_type = attachment_type
        local_attachment_size = None
        
        # Download and save attachment locally if provided
        if attachment_url:
            try:
                download_result = download_attachment(attachment_url, attachment_name)
                if download_result['success']:
                    local_attachment_url = download_result['url']
                    local_attachment_full_url = download_result['full_url']
                    local_attachment_name = download_result['filename']
                    local_attachment_type = download_result['type']
                    local_attachment_size = download_result['size']
                    logging.info(f"Attachment downloaded successfully: {local_attachment_name}")
                else:
                    logging.warning(f"Failed to download attachment: {download_result['message']}")
                    # Continue without attachment
            except Exception as e:
                logging.error(f"Error downloading attachment: {e}")
                # Continue without attachment
        
        # Save message to database as 'ai' type (received from external)
        message = MessageOperations.create_message(
            phone_number, content, 'ai',
            local_attachment_url, local_attachment_full_url, 
            local_attachment_name, local_attachment_type, local_attachment_size
        )
        
        if not message:
            return jsonify({'success': False, 'message': 'Error saving message'}), 500
        
        logging.info(f"Message received and saved successfully for phone: {phone_number}")
        
        return jsonify({
            'success': True, 
            'message': message.to_dict(),
            'attachment_downloaded': local_attachment_url is not None
        })
        
    except Exception as e:
        logging.error(f"Error receiving message: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

def download_attachment(url, original_filename=None):
    """Download attachment from external URL and save locally"""
    try:
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(os.getcwd(), UPLOAD_FOLDER)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Download file with timeout
        headers = {
            'User-Agent': 'WhatsApp-Chat-Viewer/1.0'
        }
        
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Get file size
        file_size = int(response.headers.get('content-length', 0))
        
        # Check file size limit
        if file_size > MAX_UPLOAD_SIZE:
            return {
                'success': False,
                'message': f'File too large: {file_size} bytes (max: {MAX_UPLOAD_SIZE})'
            }
        
        # Determine filename and extension
        if original_filename:
            filename = secure_filename(original_filename)
        else:
            # Extract filename from URL or Content-Disposition header
            filename = extract_filename_from_response(response, url)
        
        # Validate file extension
        if not allowed_file(filename):
            return {
                'success': False,
                'message': f'File type not allowed: {filename}'
            }
        
        # Generate unique filename to avoid conflicts
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Get actual file size
        actual_size = os.path.getsize(file_path)
        
        # Generate public URLs
        file_url = f"/chat/uploads/{unique_filename}"
        file_full_url = f"http://localhost:5000{file_url}"  # You might want to use request.host here
        
        return {
            'success': True,
            'url': file_url,
            'full_url': file_full_url,
            'filename': filename,
            'unique_filename': unique_filename,
            'size': actual_size,
            'type': get_file_type(filename)
        }
        
    except requests.RequestException as e:
        return {
            'success': False,
            'message': f'Network error downloading file: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error downloading file: {str(e)}'
        }

def extract_filename_from_response(response, url):
    """Extract filename from HTTP response or URL"""
    # Try to get filename from Content-Disposition header
    content_disposition = response.headers.get('content-disposition')
    if content_disposition:
        import re
        filename_match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
        if filename_match:
            filename = filename_match.group(1).strip('"\'')
            if filename:
                return secure_filename(filename)
    
    # Try to get filename from URL
    parsed_url = urlparse(url)
    url_filename = os.path.basename(parsed_url.path)
    if url_filename and '.' in url_filename:
        return secure_filename(url_filename)
    
    # Try to determine extension from Content-Type
    content_type = response.headers.get('content-type', '')
    extension = mimetypes.guess_extension(content_type.split(';')[0])
    if extension:
        return f"attachment{extension}"
    
    # Default fallback
    return "attachment.bin"