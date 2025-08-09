// -*- coding: utf-8 -*-
// Chat functionality for WhatsApp Chat Viewer
console.log('🚀 Chat.js loading...');

// Global variables
let currentPhoneNumber = null;
let currentPhoneId = null;
let currentAIStatus = false;
let selectedFile = null;
let messagePollingInterval = null;
let lastMessageCount = 0;

// Debug function for logging with visual feedback
function debugLog(message, data = null) {
    console.log(`[CHAT DEBUG] ${message}`, data || '');
    
    // Also show in page if debug element exists
    const debugElement = document.getElementById('debug-output');
    if (debugElement) {
        const timestamp = new Date().toLocaleTimeString();
        const debugMessage = `${timestamp}: ${message}${data !== null ? ' ' + JSON.stringify(data) : ''}`;
        debugElement.innerHTML += `<div>${debugMessage}</div>`;
        debugElement.scrollTop = debugElement.scrollHeight;
    }
}

// Create debug output element if it doesn't exist
function createDebugOutput() {
    if (!document.getElementById('debug-output')) {
        const debugDiv = document.createElement('div');
        debugDiv.id = 'debug-output';
        debugDiv.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            width: 300px;
            height: 200px;
            background: rgba(0,0,0,0.8);
            color: #00ff00;
            font-family: monospace;
            font-size: 10px;
            padding: 10px;
            border-radius: 5px;
            overflow-y: auto;
            z-index: 9999;
            display: none;
        `;
        document.body.appendChild(debugDiv);
        
        // Add toggle for debug window
        const toggleButton = document.createElement('button');
        toggleButton.textContent = 'Debug';
        toggleButton.style.cssText = `
            position: fixed;
            top: 220px;
            right: 10px;
            background: #333;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            z-index: 10000;
        `;
        toggleButton.onclick = () => {
            debugDiv.style.display = debugDiv.style.display === 'none' ? 'block' : 'none';
        };
        document.body.appendChild(toggleButton);
    }
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Safe toast function with visual feedback and fallback
function safeShowToast(message, type = 'info', duration = 4000) {
    debugLog(`🍞 Attempting to show toast: "${message}" (${type})`);
    
    // Try to use the main toast function first
    if (typeof window.showToast === 'function') {
        try {
            window.showToast(message, type, duration);
            debugLog(`✅ Toast shown via window.showToast`);
            return;
        } catch (error) {
            debugLog(`❌ window.showToast failed:`, error);
        }
    } else {
        debugLog(`❌ window.showToast is not available`);
    }
    
    // Fallback 1: Create a simple visual toast
    try {
        const container = document.getElementById('toast-container');
        if (container) {
            debugLog(`📦 Creating fallback toast in container`);
            
            const toast = document.createElement('div');
            const toastId = `fallback-toast-${Date.now()}`;
            toast.id = toastId;
            
            // Color scheme based on type
            const colors = {
                success: 'bg-green-50 border-green-200 text-green-800',
                error: 'bg-red-50 border-red-200 text-red-800',
                warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
                info: 'bg-blue-50 border-blue-200 text-blue-800'
            };
            
            const icons = {
                success: 'ri-check-circle-line',
                error: 'ri-error-warning-line',
                warning: 'ri-alert-line',
                info: 'ri-information-line'
            };
            
            toast.className = `
                ${colors[type] || colors.info}
                border rounded-lg p-4 mb-3 shadow-md
                flex items-start space-x-3
                transform transition-all duration-300 ease-in-out
                opacity-0 translate-x-full
            `;
            
            toast.innerHTML = `
                <i class="${icons[type] || icons.info} text-lg flex-shrink-0 mt-0.5"></i>
                <div class="flex-1">
                    <div class="font-medium">${escapeHtml(message)}</div>
                </div>
                <button onclick="document.getElementById('${toastId}').remove()" 
                        class="text-gray-400 hover:text-gray-600 flex-shrink-0">
                    <i class="ri-close-line"></i>
                </button>
            `;
            
            container.appendChild(toast);
            
            // Animate in
            requestAnimationFrame(() => {
                toast.style.opacity = '1';
                toast.style.transform = 'translateX(0)';
            });
            
            // Auto remove
            setTimeout(() => {
                if (document.getElementById(toastId)) {
                    toast.style.opacity = '0';
                    toast.style.transform = 'translateX(100%)';
                    setTimeout(() => {
                        if (toast.parentNode) {
                            toast.remove();
                        }
                    }, 300);
                }
            }, duration);
            
            debugLog(`✅ Fallback toast created and animated`);
            return;
        } else {
            debugLog(`❌ Toast container not found`);
        }
    } catch (error) {
        debugLog(`❌ Fallback toast creation failed:`, error);
    }
    
    // Fallback 2: Console log only (don't use alert to avoid annoyance)
    debugLog(`⚠️ Using console fallback for: "${message}"`);
    console.log(`[TOAST ${type.toUpperCase()}] ${message}`);
    
    // Create a temporary status message in the chat
    try {
        const messagesContainer = document.getElementById('messages-container');
        if (messagesContainer && (type === 'success' || type === 'error')) {
            const statusDiv = document.createElement('div');
            statusDiv.className = `
                text-center p-3 m-2 rounded-lg text-sm
                ${type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}
            `;
            statusDiv.textContent = message;
            messagesContainer.appendChild(statusDiv);
            
            // Remove after a few seconds
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.remove();
                }
            }, duration);
            
            debugLog(`✅ Status message added to chat container`);
        }
    } catch (error) {
        debugLog(`❌ Chat status message failed:`, error);
    }
}

// Global functions for sidemenu integration
window.loadMessages = loadMessages;
window.updateAIToggleState = updateAIToggleState;
window.clearChat = clearChat;

function clearChat() {
    debugLog('Clearing chat...');
    currentPhoneNumber = null;
    currentPhoneId = null;
    currentAIStatus = false;
    
    // Reset chat header
    document.getElementById('selected-phone-name').textContent = 'Selecione um número';
    document.getElementById('selected-phone-status').textContent = 'Nenhum número selecionado';
    
    // Reset avatar
    const avatar = document.getElementById('selected-phone-avatar');
    avatar.innerHTML = '<i class="ri-user-line text-gray-600"></i>';
    avatar.className = 'w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center';
    
    // Disable input
    document.getElementById('message-input').disabled = true;
    document.getElementById('send-button').disabled = true;
    document.getElementById('attachment-button').disabled = true;
    document.getElementById('ai-toggle').disabled = true;
    
    // Clear AI toggle state
    const toggle = document.getElementById('ai-toggle');
    const thumb = document.getElementById('ai-toggle-thumb');
    const statusText = document.getElementById('ai-status-text');
    
    toggle.className = toggle.className.replace('bg-whatsapp-green', 'bg-gray-200');
    thumb.className = thumb.className.replace('translate-x-6', 'translate-x-1');
    statusText.textContent = 'Inativa';
    statusText.className = 'text-sm text-gray-500';
    
    // Show welcome message
    const container = document.getElementById('messages-container');
    container.innerHTML = `
        <div class="flex flex-col items-center justify-center h-full text-gray-500">
            <div class="w-64 h-64 opacity-10 mb-4">
                <i class="ri-chat-3-line text-9xl"></i>
            </div>
            <h3 class="text-xl font-medium mb-2">WhatsApp Chat Viewer</h3>
            <p class="text-center text-gray-400 max-w-md">
                Selecione um número na barra lateral para visualizar as conversas e gerenciar as mensagens.
            </p>
        </div>
    `;
    
    // Stop polling
    stopMessagePolling();
}

async function loadMessages(phoneNumber) {
    debugLog(`Loading messages for phone: ${phoneNumber}`);
    currentPhoneNumber = phoneNumber;
    
    // Update header
    updateChatHeader(phoneNumber);
    
    // Enable input
    document.getElementById('message-input').disabled = false;
    document.getElementById('send-button').disabled = false;
    document.getElementById('attachment-button').disabled = false;
    
    try {
        const response = await fetch(`/chat/messages/${encodeURIComponent(phoneNumber)}`);
        const data = await response.json();
        
        if (data.success) {
            displayMessages(data.messages);
            lastMessageCount = data.messages.length;
            
            // Start polling for new messages
            startMessagePolling();
        } else {
            safeShowToast('Erro ao carregar mensagens', 'error');
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        safeShowToast('Erro ao carregar mensagens', 'error');
    }
}

function updateChatHeader(phoneNumber) {
    debugLog(`Updating chat header for: ${phoneNumber}`);
    document.getElementById('selected-phone-name').textContent = phoneNumber;
    document.getElementById('selected-phone-status').textContent = 'Online';
    
    // Update avatar with initials
    const avatar = document.getElementById('selected-phone-avatar');
    const initials = phoneNumber.slice(-4); // Last 4 digits
    avatar.innerHTML = `<span class="text-xs font-medium text-white">${initials}</span>`;
    avatar.className = 'w-10 h-10 bg-whatsapp-green rounded-full flex items-center justify-center';
}

function updateAIToggleState(phoneId, aiActive) {
    debugLog(`Updating AI toggle state - Phone ID: ${phoneId}, AI Active: ${aiActive}`);
    currentPhoneId = phoneId;
    currentAIStatus = aiActive;
    
    const toggle = document.getElementById('ai-toggle');
    const thumb = document.getElementById('ai-toggle-thumb');
    const statusText = document.getElementById('ai-status-text');
    
    if (!toggle || !thumb || !statusText) {
        console.error('AI toggle elements not found');
        return;
    }
    
    toggle.disabled = false;
    
    if (aiActive) {
        toggle.className = toggle.className.replace('bg-gray-200', 'bg-whatsapp-green');
        thumb.className = thumb.className.replace('translate-x-1', 'translate-x-6');
        statusText.textContent = 'Ativa';
        statusText.className = 'text-sm text-whatsapp-green';
    } else {
        toggle.className = toggle.className.replace('bg-whatsapp-green', 'bg-gray-200');
        thumb.className = thumb.className.replace('translate-x-6', 'translate-x-1');
        statusText.textContent = 'Inativa';
        statusText.className = 'text-sm text-gray-500';
    }
}

async function toggleMainAI() {
    debugLog('Toggling AI status...');
    if (!currentPhoneId) {
        console.error('No phone ID available for AI toggle');
        safeShowToast('Nenhum número selecionado', 'error');
        return;
    }
    
    try {
        debugLog(`Making toggle request for phone ID: ${currentPhoneId}`);
        
        const response = await fetch(`/chat/toggle-ai/${currentPhoneId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        debugLog(`Toggle response status: ${response.status}`);
        const data = await response.json();
        debugLog('Toggle AI response:', data);
        
        if (data.success) {
            // Update local state
            currentAIStatus = data.new_status;
            updateAIToggleState(currentPhoneId, currentAIStatus);
            
            // Reload sidebar to sync
            if (window.loadPhoneNumbers) {
                window.loadPhoneNumbers();
            }
            
            safeShowToast('Status da IA alterado', 'success');
        } else {
            safeShowToast(data.message || 'Erro ao alterar status da IA', 'error');
        }
    } catch (error) {
        console.error('Error toggling AI:', error);
        safeShowToast('Erro ao alterar status da IA', 'error');
    }
}

function displayMessages(messages) {
    debugLog(`Displaying ${messages.length} messages`);
    const container = document.getElementById('messages-container');
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center h-full text-gray-500">
                <i class="ri-chat-off-line text-6xl mb-4 opacity-50"></i>
                <h3 class="text-lg font-medium mb-2">Nenhuma mensagem</h3>
                <p class="text-center text-gray-400">
                    Seja o primeiro a enviar uma mensagem para ${currentPhoneNumber}
                </p>
            </div>
        `;
        return;
    }
    
    const messagesHtml = messages.map(message => {
        // Message type logic:
        // - 'lead': Message received from external (left side, shows phone icon)
        // - 'user': Message sent by human (right side, shows user icon)
        // - 'ai': Message sent by AI (right side, shows robot icon)
        const isOutgoing = message.type === 'user' || message.type === 'ai';
        const isFromAI = message.type === 'ai';
        const messageTime = new Date(message.created_at).toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // Generate attachment preview
        let attachmentHtml = '';
        if (message.attachment_url) {
            attachmentHtml = generateAttachmentPreview(message);
        }
        
        return `
            <div class="flex ${isOutgoing ? 'justify-end' : 'justify-start'} mb-3">
                <div class="flex items-end space-x-2 max-w-xs lg:max-w-md">
                    ${!isOutgoing ? `
                        <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                            <i class="ri-phone-line text-white text-sm"></i>
                        </div>
                    ` : ''}
                    <div class="message-enter">
                        <div class="rounded-lg ${
                            isOutgoing 
                                ? (isFromAI ? 'bg-purple-500 text-white rounded-br-sm' : 'bg-whatsapp-green text-white rounded-br-sm')
                                : 'bg-white text-gray-900 border border-gray-200 rounded-bl-sm'
                        }">
                            ${attachmentHtml}
                            ${message.content ? `<div class="px-4 py-2">
                                <p class="text-sm whitespace-pre-wrap break-words">${escapeHtml(message.content)}</p>
                            </div>` : ''}
                            <div class="flex items-center justify-end px-4 py-2 space-x-1">
                                <span class="text-xs ${isOutgoing ? (isFromAI ? 'text-purple-100' : 'text-green-100') : 'text-gray-500'}">${messageTime}</span>
                                ${isOutgoing ? '<i class="ri-check-double-line text-xs ' + (isFromAI ? 'text-purple-100' : 'text-green-100') + '"></i>' : ''}
                            </div>
                        </div>
                    </div>
                    ${isOutgoing ? `
                        <div class="w-8 h-8 ${isFromAI ? 'bg-purple-500' : 'bg-whatsapp-green'} rounded-full flex items-center justify-center flex-shrink-0">
                            <i class="${isFromAI ? 'ri-robot-line' : 'ri-user-line'} text-white text-sm"></i>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `<div class="flex flex-col">${messagesHtml}</div>`;
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

async function sendMessage(event) {
    event.preventDefault();
    debugLog("=== SEND MESSAGE FUNCTION CALLED ===");
    
    if (!currentPhoneNumber) {
        console.error("No phone number selected");
        safeShowToast('Selecione um número primeiro', 'error');
        return;
    }
    
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const attachmentButton = document.getElementById('attachment-button');
    const content = messageInput.value.trim();
    
    debugLog(`Message content: "${content}"`);
    debugLog(`Selected file: ${selectedFile ? selectedFile.name : 'none'}`);
    
    if (!content && !selectedFile) {
        console.error("No content or file provided");
        safeShowToast('Digite uma mensagem ou selecione um arquivo', 'error');
        return;
    }
    
    // Disable inputs while sending
    messageInput.disabled = true;
    sendButton.disabled = true;
    attachmentButton.disabled = true;
    
    let loadingToastId = null;
    
    try {
        let attachmentUrl = null;
        let attachmentFullUrl = null;
        let attachmentName = null;
        let attachmentType = null;
        let attachmentSize = null;
        
        // Upload file first if there's one selected
        if (selectedFile) {
            debugLog("Starting file upload...");
            
            // Use safe loading toast or fallback
            if (typeof window.showLoadingToast === 'function') {
                loadingToastId = window.showLoadingToast('Enviando arquivo...');
            } else {
                console.log('Enviando arquivo...');
            }
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('phone_number', currentPhoneNumber);
            
            debugLog("Sending file upload request...");
            
            try {
                const uploadResponse = await fetch('/chat/upload-attachment', {
                    method: 'POST',
                    body: formData
                });
                
                debugLog(`Upload response status: ${uploadResponse.status}`);
                
                const uploadData = await uploadResponse.json();
                debugLog("Upload response data:", uploadData);
                
                if (uploadData.success) {
                    attachmentUrl = uploadData.url;
                    attachmentFullUrl = uploadData.full_url;
                    attachmentName = uploadData.filename;
                    attachmentType = uploadData.type;
                    attachmentSize = uploadData.size;
                    
                    if (loadingToastId && typeof window.updateLoadingToast === 'function') {
                        window.updateLoadingToast(loadingToastId, 'Enviando mensagem...');
                    }
                } else {
                    if (loadingToastId && typeof window.finishLoadingToast === 'function') {
                        window.finishLoadingToast(loadingToastId, uploadData.message || 'Erro ao enviar arquivo', 'error');
                    } else {
                        safeShowToast(uploadData.message || 'Erro ao enviar arquivo', 'error');
                    }
                    return;
                }
            } catch (uploadError) {
                console.error("Upload error:", uploadError);
                if (loadingToastId && typeof window.finishLoadingToast === 'function') {
                    window.finishLoadingToast(loadingToastId, 'Erro na conexão durante upload', 'error');
                } else {
                    safeShowToast('Erro na conexão durante upload', 'error');
                }
                return;
            }
        }
        
        // Prepare message data
        const messageData = {
            phone_number: currentPhoneNumber,
            content: content || '',
            attachment_url: attachmentUrl,
            attachment_full_url: attachmentFullUrl,
            attachment_name: attachmentName,
            attachment_type: attachmentType,
            attachment_size: attachmentSize
        };
        
        debugLog("Sending message with data:", messageData);
        
        // Send message with detailed error handling and timeout
        let response;
        try {
            // Create AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000); // 8 second timeout
            
            response = await fetch('/chat/send-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(messageData),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId); // Clear timeout if request completes
            debugLog(`Message response status: ${response.status}`);
            
        } catch (fetchError) {
            console.error("Fetch error details:", fetchError);
            
            let errorMessage = 'Erro de conexão com o servidor';
            if (fetchError.name === 'AbortError') {
                errorMessage = 'Timeout: Servidor demorou para responder (8s)';
            }
            
            if (loadingToastId && typeof window.finishLoadingToast === 'function') {
                window.finishLoadingToast(loadingToastId, errorMessage, 'error');
            } else {
                safeShowToast(errorMessage, 'error');
            }
            return;
        }
        
        // Parse response
        let data;
        try {
            const responseText = await response.text();
            debugLog("Raw response text:", responseText);
            
            if (!responseText) {
                throw new Error("Empty response from server");
            }
            
            data = JSON.parse(responseText);
            debugLog("Parsed response data:", data);
            
        } catch (parseError) {
            console.error("Response parsing error:", parseError);
            
            if (loadingToastId && typeof window.finishLoadingToast === 'function') {
                window.finishLoadingToast(loadingToastId, 'Resposta inválida do servidor', 'error');
            } else {
                safeShowToast('Resposta inválida do servidor', 'error');
            }
            return;
        }
        
        // Handle response
        if (data.success) {
            debugLog("Message sent successfully");
            
            // Clear input and file
            messageInput.value = '';
            clearSelectedFile();
            
            // Reload messages to show the new one
            loadMessages(currentPhoneNumber);
            
            if (loadingToastId && typeof window.finishLoadingToast === 'function') {
                window.finishLoadingToast(loadingToastId, 'Mensagem enviada', 'success');
            } else {
                safeShowToast('Mensagem enviada', 'success');
            }
        } else {
            console.error("Server reported error:", data.message);
            
            if (loadingToastId && typeof window.finishLoadingToast === 'function') {
                window.finishLoadingToast(loadingToastId, data.message || 'Erro ao enviar mensagem', 'error');
            } else {
                safeShowToast(data.message || 'Erro ao enviar mensagem', 'error');
            }
        }
        
    } catch (error) {
        console.error("=== UNEXPECTED ERROR IN SEND MESSAGE ===");
        console.error("Error:", error);
        
        if (loadingToastId && typeof window.finishLoadingToast === 'function') {
            window.finishLoadingToast(loadingToastId, 'Erro inesperado', 'error');
        } else {
            safeShowToast('Erro inesperado', 'error');
        }
        
    } finally {
        // Re-enable inputs
        messageInput.disabled = false;
        sendButton.disabled = false;
        attachmentButton.disabled = false;
        messageInput.focus();
        
        debugLog("=== SEND MESSAGE FUNCTION COMPLETED ===");
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    console.log(`File selected: ${file.name}, size: ${file.size}`);
    
    // Check file size (max 50MB)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('Arquivo muito grande. Tamanho máximo: 50MB', 'error');
        event.target.value = '';
        return;
    }
    
    selectedFile = file;
    
    // Update UI to show file selected
    const fileIndicator = document.getElementById('file-indicator');
    const fileNameDisplay = document.getElementById('file-name-display');
    const fileName = file.name.length > 30 ? file.name.substring(0, 30) + '...' : file.name;
    
    fileNameDisplay.textContent = fileName;
    fileIndicator.classList.remove('hidden');
    
    showToast(`Arquivo "${fileName}" selecionado`, 'success');
}

function clearSelectedFile() {
    console.log('Clearing selected file');
    selectedFile = null;
    const fileIndicator = document.getElementById('file-indicator');
    fileIndicator.classList.add('hidden');
    document.getElementById('attachment-input').value = '';
}

function getFileType(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension)) {
        return 'image';
    } else if (['mp4', 'avi', 'mov', 'wmv', 'webm'].includes(extension)) {
        return 'video';
    } else if (['mp3', 'wav', 'ogg', 'm4a', 'aac'].includes(extension)) {
        return 'audio';
    } else if (['pdf'].includes(extension)) {
        return 'document';
    } else {
        return 'file';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function generateAttachmentPreview(message) {
    const isOutgoing = message.type === 'user' || message.type === 'ai';
    const isFromAI = message.type === 'ai';
    const fileName = escapeHtml(message.attachment_name || 'Arquivo');
    const fileSize = message.attachment_size ? formatFileSize(message.attachment_size) : '';
    const attachmentType = message.attachment_type;
    
    switch (attachmentType) {
        case 'image':
            return `
                <div class="attachment-preview">
                    <img src="${message.attachment_url}" 
                         alt="${fileName}" 
                         class="max-w-full h-auto rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                         onclick="openImageModal('${message.attachment_url}', '${fileName}')"
                         loading="lazy">
                    <div class="px-2 py-1 text-xs ${isOutgoing ? (isFromAI ? 'text-purple-100' : 'text-green-100') : 'text-gray-500'}">
                        <i class="ri-image-line mr-1"></i>${fileName} ${fileSize ? `• ${fileSize}` : ''}
                    </div>
                </div>
            `;
            
        case 'video':
            return `
                <div class="attachment-preview">
                    <video controls class="max-w-full h-auto rounded-lg">
                        <source src="${message.attachment_url}" type="video/mp4">
                        Seu navegador não suporta o elemento de vídeo.
                    </video>
                    <div class="px-2 py-1 text-xs ${isOutgoing ? (isFromAI ? 'text-purple-100' : 'text-green-100') : 'text-gray-500'}">
                        <i class="ri-video-line mr-1"></i>${fileName} ${fileSize ? `• ${fileSize}` : ''}
                    </div>
                </div>
            `;
            
        case 'audio':
            return `
                <div class="attachment-preview p-4">
                    <div class="flex items-center space-x-3 mb-2">
                        <div class="w-10 h-10 ${isOutgoing ? (isFromAI ? 'bg-purple-600' : 'bg-green-600') : 'bg-blue-500'} rounded-full flex items-center justify-center">
                            <i class="ri-music-2-line text-white"></i>
                        </div>
                        <div class="flex-1">
                            <div class="text-sm font-medium ${isOutgoing ? 'text-white' : 'text-gray-900'}">${fileName}</div>
                            <div class="text-xs ${isOutgoing ? (isFromAI ? 'text-purple-100' : 'text-green-100') : 'text-gray-500'}">${fileSize}</div>
                        </div>
                    </div>
                    <audio controls class="w-full">
                        <source src="${message.attachment_url}" type="audio/mpeg">
                        Seu navegador não suporta o elemento de áudio.
                    </audio>
                </div>
            `;
            
        case 'pdf':
            return `
                <div class="attachment-preview p-4">
                    <a href="${message.attachment_url}" target="_blank" 
                       class="flex items-center space-x-3 hover:opacity-80 transition-opacity">
                        <div class="w-10 h-10 bg-red-500 rounded-lg flex items-center justify-center">
                            <i class="ri-file-pdf-line text-white text-lg"></i>
                        </div>
                        <div class="flex-1">
                            <div class="text-sm font-medium ${isOutgoing ? 'text-white' : 'text-gray-900'}">${fileName}</div>
                            <div class="text-xs ${isOutgoing ? (isFromAI ? 'text-purple-100' : 'text-green-100') : 'text-gray-500'}">PDF ${fileSize ? `• ${fileSize}` : ''}</div>
                        </div>
                        <i class="ri-external-link-line ${isOutgoing ? (isFromAI ? 'text-purple-100' : 'text-green-100') : 'text-gray-400'}"></i>
                    </a>
                </div>
            `;
            
        case 'document':
            return `
                <div class="attachment-preview p-4">
                    <a href="${message.attachment_url}" target="_blank" 
                       class="flex items-center space-x-3 hover:opacity-80 transition-opacity">
                        <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                            <i class="ri-file-text-line text-white text-lg"></i>
                        </div>
                        <div class="flex-1">
                            <div class="text-sm font-medium ${isOutgoing ? 'text-white' : 'text-gray-900'}">${fileName}</div>
                            <div class="text-xs ${isOutgoing ? (isFromAI ? 'text-purple-100' : 'text-green-100') : 'text-gray-500'}">Documento ${fileSize ? `• ${fileSize}` : ''}</div>
                        </div>
                        <i class="ri-external-link-line ${isOutgoing ? (isFromAI ? 'text-purple-100' : 'text-green-100') : 'text-gray-400'}"></i>
                    </a>
                </div>
            `;
            
        default:
            return `
                <div class="attachment-preview p-4">
                    <a href="${message.attachment_url}" target="_blank" 
                       class="flex items-center space-x-3 hover:opacity-80 transition-opacity">
                        <div class="w-10 h-10 bg-gray-500 rounded-lg flex items-center justify-center">
                            <i class="ri-file-line text-white text-lg"></i>
                        </div>
                        <div class="flex-1">
                            <div class="text-sm font-medium ${isOutgoing ? 'text-white' : 'text-gray-900'}">${fileName}</div>
                            <div class="text-xs ${isOutgoing ? (isFromAI ? 'text-purple-100' : 'text-green-100') : 'text-gray-500'}">Arquivo ${fileSize ? `• ${fileSize}` : ''}</div>
                        </div>
                        <i class="ri-external-link-line ${isOutgoing ? (isFromAI ? 'text-purple-100' : 'text-green-100') : 'text-gray-400'}"></i>
                    </a>
                </div>
            `;
    }
}

function openImageModal(imageUrl, fileName) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4';
    modal.onclick = (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    };
    
    // Create modal content
    modal.innerHTML = `
        <div class="relative max-w-4xl max-h-full">
            <img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(fileName)}" class="max-w-full max-h-full object-contain">
            <button onclick="document.body.removeChild(this.closest('.fixed'))" 
                    class="absolute top-4 right-4 text-white hover:text-gray-300 bg-black bg-opacity-50 rounded-full p-2">
                <i class="ri-close-line text-xl"></i>
            </button>
            <div class="absolute bottom-4 left-4 right-4 text-center">
                <div class="bg-black bg-opacity-50 text-white px-4 py-2 rounded-lg inline-block">
                    ${escapeHtml(fileName)}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Auto-resize message input
function setupMessageInput() {
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('input', function(e) {
            // Auto-focus behavior
            if (e.target.value.length > 0) {
                e.target.style.paddingRight = '3rem';
            } else {
                e.target.style.paddingRight = '3rem';
            }
        });
    }
}

// Auto-refresh messages for real-time updates
function startMessagePolling() {
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
    }
    
    console.log('Starting message polling...');
    // Poll for new messages every 3 seconds when a phone is selected
    messagePollingInterval = setInterval(() => {
        if (currentPhoneNumber) {
            checkForNewMessages();
        }
    }, 3000);
}

function stopMessagePolling() {
    if (messagePollingInterval) {
        console.log('Stopping message polling...');
        clearInterval(messagePollingInterval);
        messagePollingInterval = null;
    }
}

async function checkForNewMessages() {
    if (!currentPhoneNumber) return;
    
    try {
        const response = await fetch(`/chat/messages/${encodeURIComponent(currentPhoneNumber)}`);
        const data = await response.json();
        
        if (data.success && data.messages.length > lastMessageCount) {
            // New messages detected - reload the display
            displayMessages(data.messages);
            lastMessageCount = data.messages.length;
            
            // Show notification for new messages
            const newMessagesCount = data.messages.length - lastMessageCount;
            if (newMessagesCount > 0) {
                showToast(`${newMessagesCount} nova(s) mensagem(ns) recebida(s)`, 'info', 3000);
            }
        }
        
        lastMessageCount = data.messages.length;
    } catch (error) {
        console.error('Error checking for new messages:', error);
        // Don't show error toast for polling failures to avoid spam
    }
}

// Focus message input when a phone is selected
function setupPhoneSelectionListener() {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.target.id === 'selected-phone-name') {
                const phoneText = mutation.target.textContent;
                if (phoneText !== 'Selecione um número') {
                    setTimeout(() => {
                        const messageInput = document.getElementById('message-input');
                        if (messageInput) {
                            messageInput.focus();
                        }
                    }, 100);
                }
            }
        });
    });
    
    const phoneNameElement = document.getElementById('selected-phone-name');
    if (phoneNameElement) {
        observer.observe(phoneNameElement, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }
}

// Initialize chat functionality
document.addEventListener('DOMContentLoaded', function() {
    debugLog('🚀 Chat.js DOMContentLoaded event fired');
    
    // Create debug output window
    createDebugOutput();
    
    // Check for required dependencies
    debugLog("Checking dependencies...");
    
    const checks = [
        { name: 'showToast', func: window.showToast },
        { name: 'showLoadingToast', func: window.showLoadingToast },
        { name: 'updateLoadingToast', func: window.updateLoadingToast },
        { name: 'finishLoadingToast', func: window.finishLoadingToast },
    ];
    
    checks.forEach(check => {
        if (typeof check.func === 'function') {
            debugLog(`✅ ${check.name} is available`);
        } else {
            debugLog(`❌ ${check.name} is NOT available`);
        }
    });
    
    // Setup message input functionality
    setupMessageInput();
    
    // Setup phone selection listener
    setupPhoneSelectionListener();
    
    // Setup message form submission
    const messageForm = document.getElementById('message-form');
    if (messageForm) {
        messageForm.addEventListener('submit', sendMessage);
        debugLog('✅ Message form event listener added');
    } else {
        debugLog('❌ Message form not found');
    }
    
    // Setup file selection
    const attachmentInput = document.getElementById('attachment-input');
    if (attachmentInput) {
        attachmentInput.addEventListener('change', handleFileSelect);
        debugLog('✅ Attachment input event listener added');
    } else {
        debugLog('❌ Attachment input not found');
    }
    
    // Setup attachment button
    const attachmentButton = document.getElementById('attachment-button');
    if (attachmentButton) {
        attachmentButton.addEventListener('click', function() {
            document.getElementById('attachment-input').click();
        });
        debugLog('✅ Attachment button event listener added');
    } else {
        debugLog('❌ Attachment button not found');
    }
    
    // Setup clear file button
    const clearFileBtn = document.getElementById('clear-file-btn');
    if (clearFileBtn) {
        clearFileBtn.addEventListener('click', clearSelectedFile);
        debugLog('✅ Clear file button event listener added');
    } else {
        debugLog('❌ Clear file button not found');
    }
    
    // Setup AI toggle
    const aiToggle = document.getElementById('ai-toggle');
    if (aiToggle) {
        aiToggle.addEventListener('click', toggleMainAI);
        debugLog('✅ AI toggle event listener added');
    } else {
        debugLog('❌ AI toggle not found');
    }
    
    // Stop polling when page is hidden or user leaves
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopMessagePolling();
        } else if (currentPhoneNumber) {
            startMessagePolling();
        }
    });
    
    // Stop polling when window is unloaded
    window.addEventListener('beforeunload', function() {
        stopMessagePolling();
    });
    
    debugLog('📱 Chat.js: Initialization completed');
});

// Phone deletion functionality
function handleDeletePhone(event, button) {
    event.stopPropagation();
    
    const phoneId = parseInt(button.dataset.phoneId);
    const phoneNumber = button.dataset.phoneNumber;
    
    debugLog('Delete phone request:', { phoneId, phoneNumber });
    
    // Validação
    if (!phoneId || phoneId <= 0) {
        debugLog('❌ Invalid phone ID for deletion');
        safeShowToast('Erro: ID do telefone inválido', 'error');
        return;
    }
    
    if (!phoneNumber || phoneNumber.trim() === '') {
        debugLog('❌ Invalid phone number for deletion');
        safeShowToast('Erro: Número do telefone inválido', 'error');
        return;
    }
    
    // Chama a função de confirmação
    confirmDeletePhone(event, phoneId, phoneNumber);
}

function confirmDeletePhone(event, phoneId, phoneNumber) {
    debugLog(`Request to delete phone: ${phoneNumber} (ID: ${phoneId})`);
    
    if (!phoneId || phoneId <= 0) {
        debugLog('❌ Invalid phone ID for deletion');
        safeShowToast('Erro: ID do telefone inválido', 'error');
        return;
    }
    
    // Use modal manager to show confirmation
    if (typeof window.confirmDialog === 'function') {
        window.confirmDialog({
            title: 'Excluir Número',
            message: `Tem certeza que deseja excluir o número ${phoneNumber}?`,
            confirmText: 'Excluir',
            cancelText: 'Cancelar',
            type: 'danger',
            onConfirm: () => {
                debugLog(`Confirmed deletion of phone: ${phoneId}`);
                deletePhone(phoneId, phoneNumber);
            },
            onCancel: () => {
                debugLog(`Cancelled deletion of phone: ${phoneId}`);
            }
        });
    } else {
        // Fallback to native confirm
        if (confirm(`Tem certeza que deseja excluir o número ${phoneNumber}?\n\nEsta ação é irreversível e todas as mensagens serão perdidas.`)) {
            deletePhone(phoneId, phoneNumber);
        }
    }
}

// Actual delete phone function
async function deletePhone(phoneId, phoneNumber) {
    debugLog(`Deleting phone: ${phoneNumber} (ID: ${phoneId})`);
    
    let loadingToastId = null;
    
    try {
        // Show loading toast
        if (typeof window.showLoadingToast === 'function') {
            loadingToastId = window.showLoadingToast('Excluindo número...');
        } else {
            safeShowToast('Excluindo número...', 'info');
        }
        
        const response = await fetch('/chat/delete-phone', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                phone_id: phoneId,
                phone_number: phoneNumber
            })
        });
        
        debugLog(`Delete response status: ${response.status}`);
        
        const data = await response.json();
        debugLog('Delete response data:', data);
        
        if (data.success) {
            if (loadingToastId && typeof window.finishLoadingToast === 'function') {
                window.finishLoadingToast(loadingToastId, 'Número excluído com sucesso', 'success');
            } else {
                safeShowToast('Número excluído com sucesso', 'success');
            }
            
            // If the deleted phone was currently selected, clear selection
            if (currentPhoneId === phoneId) {
                currentPhoneNumber = null;
                currentPhoneId = null;
                currentAIStatus = false;
                
                // Clear messages
                const messagesContainer = document.getElementById('messages-container');
                if (messagesContainer) {
                    messagesContainer.innerHTML = '<div class="text-center text-gray-500 py-8">Selecione um número para ver as mensagens</div>';
                }
                
                // Update header
                const selectedPhoneName = document.getElementById('selected-phone-name');
                if (selectedPhoneName) {
                    selectedPhoneName.textContent = 'Selecione um número';
                }
            }
            
            // Reload phone list
            if (typeof window.loadPhones === 'function') {
                window.loadPhones();
            } else {
                // Fallback: reload page
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
            
        } else {
            if (loadingToastId && typeof window.finishLoadingToast === 'function') {
                window.finishLoadingToast(loadingToastId, data.message || 'Erro ao excluir número', 'error');
            } else {
                safeShowToast(data.message || 'Erro ao excluir número', 'error');
            }
        }
        
    } catch (error) {
        console.error('Delete phone error:', error);
        
        if (loadingToastId && typeof window.finishLoadingToast === 'function') {
            window.finishLoadingToast(loadingToastId, 'Erro de conexão', 'error');
        } else {
            safeShowToast('Erro de conexão', 'error');
        }
    }
}

// Make functions globally available for HTML onclick handlers
window.sendMessage = sendMessage;
window.toggleMainAI = toggleMainAI;
window.handleFileSelect = handleFileSelect;
window.clearSelectedFile = clearSelectedFile;
window.openImageModal = openImageModal;
window.handleDeletePhone = handleDeletePhone;
window.confirmDeletePhone = confirmDeletePhone;
window.deletePhone = deletePhone;
