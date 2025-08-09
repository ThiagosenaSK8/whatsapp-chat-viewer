# -*- coding: utf-8 -*-
import logging
import requests
import os
import uuid
import threading
import time
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
    """Get file type and MIME type for better webhook compatibility"""
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if extension in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
        return 'image'
    elif extension in {'mp4', 'avi', 'mov', 'wmv', 'webm'}:
        return 'video'
    elif extension in {'mp3', 'wav', 'ogg', 'm4a', 'aac'}:
        return 'audio'
    elif extension in {'pdf'}:
        return 'pdf'
    elif extension in {'doc', 'docx', 'txt'}:
        return 'document'
    else:
        return 'file'

def get_mime_type(filename):
    """Get MIME type for file"""
    try:
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    except Exception as e:
        logging.warning(f"Error detecting MIME type for {filename}: {e}")
        return 'application/octet-stream'

# Global variables for webhook reliability
webhook_failures = 0
last_failure_time = None
MAX_FAILURES_BEFORE_CIRCUIT_BREAK = 5
CIRCUIT_BREAK_DURATION = 60  # seconds

def is_circuit_broken():
    """Check if circuit breaker is active"""
    global webhook_failures, last_failure_time
    if webhook_failures >= MAX_FAILURES_BEFORE_CIRCUIT_BREAK:
        if last_failure_time and (time.time() - last_failure_time) < CIRCUIT_BREAK_DURATION:
            return True
        else:
            # Reset circuit breaker after duration
            webhook_failures = 0
            last_failure_time = None
    return False

def record_webhook_result(success):
    """Record webhook success/failure for circuit breaker"""
    global webhook_failures, last_failure_time
    if success:
        webhook_failures = max(0, webhook_failures - 1)  # Reduce failure count on success
    else:
        webhook_failures += 1
        last_failure_time = time.time()

def validate_webhook_data(data):
    """Validate webhook data before sending"""
    try:
        # Check if data can be serialized to JSON
        import json
        json.dumps(data, ensure_ascii=False, default=str)
        
        # Check required fields
        required_fields = ['event_type', 'phone_number', 'timestamp']
        for field in required_fields:
            if field not in data or data[field] is None:
                logging.warning(f"Missing required field: {field}")
                return False
        
        # Validate phone number format (basic check)
        phone = data.get('phone_number', '')
        if not phone or len(phone) < 8:  # Minimum reasonable phone length
            logging.warning(f"Invalid phone number: {phone}")
            return False
        
        return True
    except Exception as e:
        logging.error(f"Webhook data validation failed: {e}")
        return False

def send_webhook_with_retry(webhook_type, phone_number, data, max_retries=2):
    """Send webhook with retry in background thread"""
    def _retry_webhook():
        try:
            success = False
            for attempt in range(max_retries + 1):
                if attempt > 0:
                    delay = min(2 ** attempt, 5)  # Exponential backoff, max 5s
                    logging.info(f"Webhook retry {attempt}/{max_retries} in {delay}s...")
                    time.sleep(delay)
                
                success = send_webhook(webhook_type, phone_number, data)
                if success:
                    logging.info(f"✅ Webhook retry {attempt} successful")
                    record_webhook_result(True)
                    break
                else:
                    logging.warning(f"⚠️ Webhook attempt {attempt + 1} failed")
            
            if not success:
                logging.error(f"❌ All {max_retries + 1} webhook attempts failed")
                record_webhook_result(False)
        
        except Exception as e:
            logging.error(f"❌ Error in webhook retry thread: {e}")
            record_webhook_result(False)
    
    # Start retry in background thread
    thread = threading.Thread(target=_retry_webhook, daemon=True)
    thread.start()

def send_webhook(webhook_type, phone_number, data):
    """
    Send webhook notification with improved reliability
    
    Args:
        webhook_type (str): Type of webhook event ('message', 'ai_toggle', 'phone_added')
        phone_number (str): Phone number involved in the event
        data (dict): Additional data to send with the webhook
    
    Returns:
        bool: True if webhook was sent successfully, False otherwise
    """
    try:
        webhook_url = config.webhook_url
        if not webhook_url:
            logging.debug(f"No webhook URL configured for {webhook_type} event - skipping")
            return False
        
        # Check circuit breaker
        if is_circuit_broken():
            logging.warning(f"⚡ Circuit breaker active - skipping webhook {webhook_type}")
            return False
        
        # Prepare webhook payload with better serialization
        webhook_data = {
            'event_type': webhook_type,
            'phone_number': phone_number,
            'timestamp': datetime.now().isoformat(),
            **data  # Merge additional data
        }
        
        # Validate data before sending
        if not validate_webhook_data(webhook_data):
            logging.error(f"❌ Webhook data validation failed for {webhook_type}")
            return False
        
        # Concise logging (reduced verbosity for performance)
        logging.info(f"🚀 Sending {webhook_type} webhook for {phone_number}")
        
        # Log attachment info only if present (concise)
        if 'attachment_type' in data and data['attachment_type']:
            attachment_info = f"{data.get('attachment_type')} ({data.get('attachment_size', 0)} bytes)"
            logging.info(f"📎 Attachment: {attachment_info}")
        
        # Prepare headers with better compatibility
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'WhatsApp-Chat-Viewer-Webhook/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'close'  # Prevent connection reuse issues
        }
        
        # Get timeout from config
        timeout = config.webhook_timeout
        
        # Send webhook with configured timeout
        response = requests.post(
            webhook_url, 
            json=webhook_data,
            headers=headers,
            timeout=timeout,
            allow_redirects=False
        )
        
        # Check response
        response.raise_for_status()
        
        # Log success with response info
        logging.info(f"✅ Webhook {webhook_type} sent successfully ({response.status_code}) in {timeout}s timeout")
        
        # Record success
        record_webhook_result(True)
        return True
        
    except requests.Timeout:
        logging.warning(f"⏰ Webhook {webhook_type} timed out ({config.webhook_timeout}s)")
        record_webhook_result(False)
        return False
    except requests.ConnectionError as e:
        logging.warning(f"🔌 Webhook {webhook_type} connection failed: {str(e)[:100]}")
        record_webhook_result(False)
        return False
    except requests.HTTPError as e:
        status = e.response.status_code if e.response else 'Unknown'
        logging.error(f"📡 Webhook {webhook_type} HTTP error: {status}")
        if e.response and hasattr(e.response, 'text'):
            logging.error(f"Response: {e.response.text[:200]}...")
        record_webhook_result(False)
        return False
    except requests.RequestException as e:
        logging.warning(f"🌐 Webhook {webhook_type} request failed: {str(e)[:100]}")
        record_webhook_result(False)
        return False
    except Exception as e:
        logging.error(f"💥 Unexpected webhook {webhook_type} error: {str(e)[:100]}")
        record_webhook_result(False)
        return False
        logging.error(f"Traceback: {traceback.format_exc()}")
        return False

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
    logging.info("=== SEND MESSAGE ENDPOINT CALLED ===")
    
    try:
        # Log request details
        logging.info(f"Request method: {request.method}")
        logging.info(f"Request headers: {dict(request.headers)}")
        logging.info(f"Content-Type: {request.content_type}")
        
        # Parse JSON data safely
        try:
            data = request.get_json()
            logging.info(f"Parsed JSON data: {data}")
        except Exception as json_error:
            logging.error(f"Failed to parse JSON: {json_error}")
            return jsonify({'success': False, 'message': 'Dados JSON inválidos'}), 400
        
        if not data:
            logging.error("No JSON data received")
            return jsonify({'success': False, 'message': 'Nenhum dado recebido'}), 400
        
        # Extract and validate data
        phone_number = data.get('phone_number')
        content = data.get('content', '')
        attachment_url = data.get('attachment_url')
        attachment_full_url = data.get('attachment_full_url')
        attachment_name = data.get('attachment_name')
        attachment_type = data.get('attachment_type')
        attachment_size = data.get('attachment_size')
        
        logging.info(f"Processing message for phone: {phone_number}")
        logging.info(f"Message content length: {len(content) if content else 0}")
        logging.info(f"Has attachment: {bool(attachment_url)}")
        
        # Validation
        if not phone_number:
            logging.error("Phone number is missing")
            return jsonify({'success': False, 'message': 'Número é obrigatório'}), 400
        
        if not content and not attachment_url:
            logging.error("Both content and attachment are missing")
            return jsonify({'success': False, 'message': 'Conteúdo ou anexo são obrigatórios'}), 400
        
        # Determine message type based on AI status for the phone
        phone = PhoneOperations.get_phone_by_number(phone_number)
        if not phone:
            logging.error(f"Phone number not found: {phone_number}")
            return jsonify({'success': False, 'message': 'Número não encontrado'}), 404
        
        # Message type logic:
        # - 'ai' if AI is active for this phone (automated response)
        # - 'user' if AI is inactive (human response)
        message_type = 'ai' if phone.ai_active else 'user'
        logging.info(f"Message type determined: {message_type} (AI active: {phone.ai_active})")
        
        # Database operation with detailed logging
        logging.info("Starting database operation...")
        try:
            message = MessageOperations.create_message(
                phone_number, content, message_type,
                attachment_url, attachment_full_url, attachment_name, attachment_type, attachment_size
            )
            logging.info(f"Database operation result: {message is not None}")
        except Exception as db_error:
            logging.error(f"Database operation failed: {db_error}")
            logging.error(f"Database error type: {type(db_error).__name__}")
            return jsonify({'success': False, 'message': 'Erro ao salvar mensagem no banco'}), 500
        
        if not message:
            logging.error("Message creation returned None")
            return jsonify({'success': False, 'message': 'Erro ao salvar mensagem'}), 500
        
        logging.info(f"Message saved successfully with ID: {message.id}")
        
        # Webhook operation with improved reliability (hybrid approach)
        webhook_sent = False
        webhook_sent_immediately = False
        try:
            logging.info("=== STARTING WEBHOOK OPERATION ===")
            
            # Prepare webhook data with message type info
            webhook_data = {
                'message': content,
                'message_type': message_type,  # Include the message type for webhook
                'ai_active': phone.ai_active,  # Include AI status for context
                'attachment_url': attachment_url,
                'attachment_full_url': attachment_full_url,
                'attachment_name': attachment_name,
                'attachment_type': attachment_type,
                'attachment_size': attachment_size,
                'message_id': message.id,
                'sent_by': current_user.email
            }
            
            # Log specific information for different file types (concise)
            if attachment_type:
                type_emoji = {
                    'image': '📸', 'pdf': '📄', 'document': '📝', 
                    'audio': '🎵', 'video': '🎬'
                }.get(attachment_type, '📎')
                logging.info(f"{type_emoji} Processing webhook for {attachment_type} attachment")
            
            # Try immediate send (primary attempt)
            webhook_sent_immediately = send_webhook('message', phone_number, webhook_data)
            
            if webhook_sent_immediately:
                logging.info("✅ Webhook sent immediately")
                webhook_sent = True
            else:
                logging.info("⚠️ Immediate webhook failed - scheduling retry in background")
                # Schedule background retry (secondary attempt)
                send_webhook_with_retry('message', phone_number, webhook_data, max_retries=2)
                webhook_sent = True  # Consider as "sent" since we're retrying
            
            # Log result concisely
            status_emoji = "✅" if webhook_sent_immediately else "🔄"
            logging.info(f"{status_emoji} Webhook operation completed: immediate={webhook_sent_immediately}")
            
        except Exception as webhook_error:
            logging.error(f"❌ Webhook operation failed: {webhook_error}")
            # Schedule retry even on exception
            try:
                send_webhook_with_retry('message', phone_number, webhook_data, max_retries=1)
                webhook_sent = True  # Consider as "sent" since we're retrying
            except Exception:
                pass  # Continue even if retry scheduling fails
            # Continue even if webhook fails - message is already saved
        
        # Prepare response
        logging.info("Preparing response...")
        
        # Safely serialize message to dict with error handling
        try:
            message_dict = message.to_dict()
            logging.info(f"Message serialized successfully: {type(message_dict)}")
        except Exception as serialize_error:
            logging.error(f"Error serializing message: {serialize_error}")
            # Create a safe minimal response if serialization fails
            message_dict = {
                'id': message.id,
                'content': message.content or '',
                'type': message.type,
                'created_at': message.created_at.isoformat() if message.created_at else None,
                'phone_number_id': message.phone_number_id
            }
            logging.info("Using minimal message dict due to serialization error")
        
        try:
            response_data = {
                'success': True, 
                'message': message_dict,
                'webhook_sent': webhook_sent
            }
            logging.info(f"Response data prepared successfully")
            
            # Test JSON serialization before sending
            import json
            json.dumps(response_data, default=str)
            logging.info("Response data JSON serialization test passed")
            
        except Exception as response_error:
            logging.error(f"Error preparing response data: {response_error}")
            # Ultra-safe fallback response
            response_data = {
                'success': True,
                'message': {'id': message.id if message else 0},
                'webhook_sent': webhook_sent
            }
            logging.info("Using ultra-safe fallback response")
        
        logging.info("=== SEND MESSAGE ENDPOINT COMPLETED SUCCESSFULLY ===")
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"=== FATAL ERROR IN SEND MESSAGE ENDPOINT ===")
        logging.error(f"Error: {e}")
        logging.error(f"Error type: {type(e).__name__}")
        logging.error(f"Error args: {e.args}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        
        try:
            return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
        except Exception as response_error:
            logging.error(f"Failed to send error response: {response_error}")
            # Force a basic response if JSON fails
            return "Internal Server Error", 500

@bp.route('/toggle-ai/<int:phone_id>', methods=['POST'])
@login_required
def toggle_ai(phone_id):
    """Toggle AI status for a phone number"""
    try:
        logging.info(f"Toggling AI status for phone ID: {phone_id}")
        
        # Get phone info before toggle to know the current state
        phone = PhoneOperations.get_phone_by_id(phone_id)
        if not phone:
            return jsonify({'success': False, 'message': 'Número não encontrado'}), 404
            
        # Store previous state
        previous_ai_status = phone.ai_active
        
        # Toggle AI status
        success = PhoneOperations.toggle_ai_status(phone_id)
        if not success:
            return jsonify({'success': False, 'message': 'Erro ao alterar status da IA'}), 500
        
        # Get new state after toggle
        new_ai_status = not previous_ai_status
        
        logging.info(f"AI status changed for phone {phone.number}: {previous_ai_status} -> {new_ai_status}")
        
        # Send webhook notification for AI status change
        webhook_data = {
            'previous_status': previous_ai_status,
            'new_status': new_ai_status,
            'changed_by': current_user.email,
            'phone_id': phone_id
        }
        
        webhook_sent = send_webhook('ai_toggle', phone.number, webhook_data)
        
        return jsonify({
            'success': True, 
            'message': 'Status da IA alterado com sucesso',
            'webhook_sent': webhook_sent,
            'new_status': new_ai_status
        })
            
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
            # Send webhook notification for new phone added
            webhook_data = {
                'phone_id': phone.id,
                'ai_active': phone.ai_active,
                'added_by': current_user.email
            }
            
            webhook_sent = send_webhook('phone_added', phone_number, webhook_data)
            
            return jsonify({
                'success': True, 
                'phone': {
                    'id': phone.id,
                    'number': phone.number,
                    'ai_active': phone.ai_active,
                    'created_at': phone.created_at.isoformat() if phone.created_at else None
                },
                'webhook_sent': webhook_sent
            })
        else:
            return jsonify({'success': False, 'message': 'Erro ao criar número'}), 500
            
    except Exception as e:
        logging.error(f"Error adding phone number: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@bp.route('/webhook-status', methods=['GET'])
@login_required
def webhook_status():
    """Get webhook status including circuit breaker info"""
    try:
        global webhook_failures, last_failure_time
        
        circuit_broken = is_circuit_broken()
        time_since_last_failure = None
        if last_failure_time:
            time_since_last_failure = int(time.time() - last_failure_time)
        
        status_data = {
            'success': True,
            'webhook_url': config.webhook_url or '',
            'webhook_timeout': config.webhook_timeout,
            'circuit_broken': circuit_broken,
            'failure_count': webhook_failures,
            'time_since_last_failure': time_since_last_failure,
            'max_failures': MAX_FAILURES_BEFORE_CIRCUIT_BREAK,
            'circuit_break_duration': CIRCUIT_BREAK_DURATION
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        logging.error(f"Error getting webhook status: {e}")
        return jsonify({'success': False, 'message': 'Erro ao obter status do webhook'}), 500

@bp.route('/reset-webhook-circuit', methods=['POST'])
@login_required
def reset_webhook_circuit():
    """Reset webhook circuit breaker"""
    try:
        global webhook_failures, last_failure_time
        webhook_failures = 0
        last_failure_time = None
        
        logging.info("Webhook circuit breaker reset by user")
        return jsonify({
            'success': True,
            'message': 'Circuit breaker resetado com sucesso'
        })
        
    except Exception as e:
        logging.error(f"Error resetting webhook circuit: {e}")
        return jsonify({'success': False, 'message': 'Erro ao resetar circuit breaker'}), 500

@bp.route('/test-webhook', methods=['POST'])
@login_required
def test_webhook():
    """Test webhook functionality"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number', 'test-number')
        attachment_type = data.get('attachment_type', 'test')
        
        # Prepare test webhook data
        test_data = {
            'message': 'Test webhook message',
            'attachment_url': '/test/file.jpg',
            'attachment_full_url': 'http://localhost:5000/test/file.jpg',
            'attachment_name': 'test_file.jpg',
            'attachment_type': attachment_type,
            'attachment_size': 12345,
            'message_id': 999999,
            'sent_by': current_user.email,
            'test_mode': True
        }
        
        logging.info(f"Testing webhook for attachment type: {attachment_type}")
        webhook_sent = send_webhook('message', phone_number, test_data)
        
        return jsonify({
            'success': True,
            'webhook_sent': webhook_sent,
            'message': f'Test webhook for {attachment_type} completed'
        })
        
    except Exception as e:
        logging.error(f"Error testing webhook: {e}")
        return jsonify({'success': False, 'message': 'Erro ao testar webhook'}), 500

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
        file_type = get_file_type(filename)
        mime_type = get_mime_type(filename)
        
        logging.info(f"=== FILE UPLOAD SUCCESS ===")
        logging.info(f"Original filename: {filename}")
        logging.info(f"Unique filename: {unique_filename}")
        logging.info(f"File size: {file_size} bytes")
        logging.info(f"File type: {file_type}")
        logging.info(f"MIME type: {mime_type}")
        logging.info(f"Phone number: {phone_number}")
        logging.info(f"File URL: {file_url}")
        logging.info(f"Full URL: {file_full_url}")
        
        return jsonify({
            'success': True,
            'url': file_url,
            'full_url': file_full_url,
            'filename': filename,
            'size': file_size,
            'type': file_type,
            'mime_type': mime_type
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
    """
    Receive incoming messages with attachments from webhook
    
    Supports multiple attachment formats:
    1. Complete attachment data (preferred):
       {
         "attachment_url": "https://external.com/file.jpg",
         "attachment_name": "photo.jpg",
         "attachment_type": "image",
         "attachment_size": 123456
       }
    
    2. Minimal attachment data (will be auto-detected):
       {
         "attachment_url": "https://external.com/file.jpg"
       }
    
    3. Direct local file reference:
       {
         "attachment_url": "/chat/uploads/file.jpg",
         "attachment_name": "file.jpg",
         "attachment_type": "image"
       }
    """
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        content = data.get('message', '')
        
        # Attachment fields with flexible handling
        attachment_url = data.get('attachment_url')
        attachment_name = data.get('attachment_name')
        attachment_type = data.get('attachment_type')
        attachment_size = data.get('attachment_size')
        
        logging.info(f"📱 Receiving message from phone: {phone_number}")
        logging.info(f"📄 Message has content: {bool(content)}")
        logging.info(f"📎 Message has attachment: {bool(attachment_url)}")
        
        # Validation
        if not phone_number:
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        if not content and not attachment_url:
            return jsonify({'success': False, 'message': 'Content or attachment is required'}), 400
        
        # Ensure phone exists (create if needed)
        phone = PhoneOperations.get_phone_by_number(phone_number)
        if not phone:
            logging.info(f"📞 Creating new phone number: {phone_number}")
            phone = PhoneOperations.create_phone_number(phone_number)
            if not phone:
                return jsonify({'success': False, 'message': 'Error creating phone number'}), 500
        
        # Initialize attachment variables with safe defaults
        final_attachment_url = None
        final_attachment_full_url = None
        final_attachment_name = None
        final_attachment_type = None
        final_attachment_size = None
        
        # Process attachment if provided
        if attachment_url:
            logging.info(f"📎 Processing attachment: {attachment_url}")
            
            # Check if it's already a local file (starts with /chat/uploads/)
            if attachment_url.startswith('/chat/uploads/'):
                logging.info("📁 Local attachment detected")
                final_attachment_url = attachment_url
                final_attachment_full_url = f"{request.scheme}://{request.host}{attachment_url}"
                final_attachment_name = attachment_name or os.path.basename(attachment_url)
                final_attachment_type = attachment_type or get_file_type(final_attachment_name)
                
                # Try to get file size if file exists locally
                try:
                    upload_dir = os.path.join(os.getcwd(), UPLOAD_FOLDER)
                    file_path = os.path.join(upload_dir, os.path.basename(attachment_url))
                    if os.path.exists(file_path):
                        final_attachment_size = os.path.getsize(file_path)
                except Exception as e:
                    logging.warning(f"Could not get local file size: {e}")
                    final_attachment_size = attachment_size  # Use provided size if available
                    
            else:
                # External URL - attempt to download and process
                logging.info("🌐 External attachment detected - attempting download")
                try:
                    download_result = download_attachment_enhanced(
                        attachment_url, 
                        attachment_name, 
                        attachment_type, 
                        attachment_size
                    )
                    
                    if download_result['success']:
                        final_attachment_url = download_result['url']
                        final_attachment_full_url = download_result['full_url']
                        final_attachment_name = download_result['filename']
                        final_attachment_type = download_result['type']
                        final_attachment_size = download_result['size']
                        logging.info(f"✅ Attachment downloaded successfully: {final_attachment_name}")
                    else:
                        logging.warning(f"❌ Download failed: {download_result['message']}")
                        # Fallback: store original URL with available metadata
                        final_attachment_url = attachment_url  # Keep original URL
                        final_attachment_full_url = attachment_url
                        final_attachment_name = attachment_name or extract_filename_from_url(attachment_url)
                        final_attachment_type = attachment_type or 'file'
                        final_attachment_size = attachment_size
                        logging.info("📋 Using original attachment metadata as fallback")
                        
                except Exception as e:
                    logging.error(f"💥 Attachment processing error: {e}")
                    # Fallback: store what we have
                    final_attachment_url = attachment_url
                    final_attachment_full_url = attachment_url
                    final_attachment_name = attachment_name or 'attachment'
                    final_attachment_type = attachment_type or 'file'
                    final_attachment_size = attachment_size
                    logging.info("📋 Using minimal attachment metadata due to error")
            
            # Log final attachment details
            logging.info(f"📎 Final attachment details:")
            logging.info(f"   URL: {final_attachment_url}")
            logging.info(f"   Name: {final_attachment_name}")
            logging.info(f"   Type: {final_attachment_type}")
            logging.info(f"   Size: {final_attachment_size}")
        
        # Save message to database as 'lead' type (received from external)
        message = MessageOperations.create_message(
            phone_number, content, 'lead',
            final_attachment_url, final_attachment_full_url, 
            final_attachment_name, final_attachment_type, final_attachment_size
        )
        
        if not message:
            return jsonify({'success': False, 'message': 'Error saving message'}), 500
        
        logging.info(f"Message received and saved successfully for phone: {phone_number}")
        
        return jsonify({
            'success': True, 
            'message': message.to_dict(),
            'attachment_downloaded': final_attachment_url is not None,
            'attachment_was_local': final_attachment_url and final_attachment_url.startswith('/chat/uploads/') if final_attachment_url else False
        })
        
    except Exception as e:
        logging.error(f"Error receiving message: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

def extract_filename_from_url(url):
    """Extract filename from URL for fallback purposes"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if filename and '.' in filename:
            return secure_filename(filename)
        return 'attachment'
    except Exception:
        return 'attachment'

def download_attachment_enhanced(url, original_filename=None, original_type=None, original_size=None):
    """
    Enhanced version of download_attachment with better metadata handling
    """
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
        
        # Get file size from headers or use provided size
        file_size = int(response.headers.get('content-length', original_size or 0))
        
        # Check file size limit
        if file_size > MAX_UPLOAD_SIZE:
            return {
                'success': False,
                'message': f'File too large: {file_size} bytes (max: {MAX_UPLOAD_SIZE})'
            }
        
        # Determine filename with preference for provided name
        if original_filename:
            filename = secure_filename(original_filename)
        else:
            filename = extract_filename_from_response(response, url)
        
        # Validate file extension (if we have one)
        if '.' in filename and not allowed_file(filename):
            # If provided type suggests it should be allowed, trust it
            if not original_type or original_type == 'file':
                return {
                    'success': False,
                    'message': f'File type not allowed: {filename}'
                }
            # Otherwise, use the original type to generate a safe extension
            filename = f"attachment.{get_extension_from_type(original_type)}"
        
        # Generate unique filename to avoid conflicts
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'bin'
        unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Get actual file size
        actual_size = os.path.getsize(file_path)
        
        # Determine file type with preference for provided type
        determined_type = original_type or get_file_type(filename)
        
        # Generate public URLs
        file_url = f"/chat/uploads/{unique_filename}"
        file_full_url = f"{request.scheme if 'request' in globals() else 'http'}://localhost:5000{file_url}"
        
        return {
            'success': True,
            'url': file_url,
            'full_url': file_full_url,
            'filename': original_filename or filename,
            'unique_filename': unique_filename,
            'size': actual_size,
            'type': determined_type
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

def get_extension_from_type(file_type):
    """Get file extension from file type"""
    type_extensions = {
        'image': 'jpg',
        'video': 'mp4',
        'audio': 'mp3',
        'pdf': 'pdf',
        'document': 'doc',
        'file': 'bin'
    }
    return type_extensions.get(file_type, 'bin')
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

@bp.route('/delete-phone/<int:phone_id>', methods=['DELETE'])
@login_required
def delete_phone(phone_id):
    """Delete a phone number and all its messages"""
    try:
        logging.info(f"Deleting phone ID: {phone_id} by user: {current_user.email}")
        
        # Get phone info before deletion for webhook
        phone = PhoneOperations.get_phone_by_id(phone_id)
        if not phone:
            return jsonify({'success': False, 'message': 'Número não encontrado'}), 404
        
        phone_number = phone.number
        
        # Delete phone (cascade will delete messages)
        success = PhoneOperations.delete_phone(phone_id)
        if not success:
            return jsonify({'success': False, 'message': 'Erro ao excluir número'}), 500
        
        logging.info(f"Phone {phone_number} deleted successfully")
        
        # Send webhook notification for phone deletion
        webhook_data = {
            'phone_id': phone_id,
            'deleted_by': current_user.email,
            'messages_deleted': True  # Cascade deletion includes messages
        }
        
        webhook_sent = send_webhook('phone_deleted', phone_number, webhook_data)
        
        return jsonify({
            'success': True, 
            'message': 'Número excluído com sucesso',
            'webhook_sent': webhook_sent
        })
            
    except Exception as e:
        logging.error(f"Error deleting phone {phone_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500


@bp.route('/delete-phone', methods=['POST'])
@login_required
def delete_phone_post():
    """Delete a phone number via POST request"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
        
        phone_id = data.get('phone_id')
        if not phone_id:
            return jsonify({'success': False, 'message': 'ID do telefone não fornecido'}), 400
        
        # Call the main delete function
        return delete_phone(phone_id)
        
    except Exception as e:
        logging.error(f"Error in delete_phone_post: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500