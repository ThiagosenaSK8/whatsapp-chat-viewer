# Guia de Integração - Endpoint `/receive-message`

## 🎯 **Visão Geral**

O endpoint `/chat/receive-message` foi aprimorado para lidar de forma robusta com mensagens externas, especialmente attachments, garantindo consistência dos dados mesmo quando informações estão incompletas.

## 📡 **Como Enviar Mensagens Externas**

### **1. Mensagem Simples (Apenas Texto)**
```json
POST /chat/receive-message
{
  "phone_number": "+5511999999999",
  "message": "Olá! Como você está?"
}
```

### **2. Attachment Completo (Recomendado)**
```json
{
  "phone_number": "+5511999999999",
  "message": "Segue a foto solicitada",
  "attachment_url": "https://example.com/photos/image.jpg",
  "attachment_name": "foto_perfil.jpg",
  "attachment_type": "image",
  "attachment_size": 245760
}
```

### **3. Attachment Mínimo (Sistema Auto-Detecta)**
```json
{
  "phone_number": "+5511999999999", 
  "attachment_url": "https://example.com/files/document.pdf"
}
```

### **4. Attachment Local (Já no Servidor)**
```json
{
  "phone_number": "+5511999999999",
  "attachment_url": "/chat/uploads/existing_file.jpg",
  "attachment_name": "arquivo_existente.jpg"
}
```

## 🔄 **Processamento Inteligente**

### **Sistema de Fallback em Camadas:**

1. **Download Bem-Sucedido** ✅
   - Arquivo baixado e salvo localmente
   - Metadados detectados automaticamente
   - URL convertida para URL local

2. **Download Falhou, Mas Temos Metadados** ⚠️
   - Mantém URL original
   - Usa metadados fornecidos
   - Sistema continua funcional

3. **Falha Total, Dados Mínimos** 🔧
   - Armazena o que foi fornecido
   - Gera valores padrão seguros
   - Mensagem não é perdida

## 🎨 **Detecção Automática de Tipos**

### **Por Extensão:**
```javascript
.jpg, .png, .gif → "image"
.mp4, .avi → "video"  
.mp3, .wav → "audio"
.pdf → "pdf"
.doc, .txt → "document"
outros → "file"
```

### **Por Content-Type (Se Disponível):**
```javascript
image/* → "image"
video/* → "video"
audio/* → "audio"  
application/pdf → "pdf"
```

## 📊 **Respostas do Sistema**

### **Sucesso com Download:**
```json
{
  "success": true,
  "message": {
    "id": 123,
    "content": "Mensagem com anexo",
    "type": "lead",
    "attachment_url": "/chat/uploads/abc123_20250809_143022.jpg",
    "attachment_name": "foto.jpg",
    "attachment_type": "image",
    "attachment_size": 245760
  },
  "attachment_downloaded": true,
  "attachment_was_local": false
}
```

### **Sucesso com Fallback:**
```json
{
  "success": true,
  "message": {
    "id": 124,
    "content": "Documento importante",
    "type": "lead",
    "attachment_url": "https://external.com/doc.pdf",
    "attachment_name": "documento.pdf", 
    "attachment_type": "pdf",
    "attachment_size": null
  },
  "attachment_downloaded": false,
  "attachment_was_local": false
}
```

## ⚡ **Casos de Uso Práticos**

### **WhatsApp Business API:**
```javascript
// Recebeu mensagem do WhatsApp
const whatsappData = {
  phone_number: message.from,
  message: message.text?.body || '',
  attachment_url: message.image?.link || message.document?.link,
  attachment_name: message.document?.filename,
  attachment_type: message.type // 'image', 'document', etc
};

fetch('/chat/receive-message', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(whatsappData)
});
```

### **Telegram Bot:**
```python
# Recebeu arquivo do Telegram
telegram_data = {
    "phone_number": f"+{message.from_user.id}",
    "message": message.caption or "",
    "attachment_url": bot.get_file_url(message.photo[-1].file_id),
    "attachment_type": "image"
}

requests.post('/chat/receive-message', json=telegram_data)
```

### **Sistema Próprio:**
```php
// Upload local já processado
$localData = [
    'phone_number' => $customer_phone,
    'message' => $message_text,
    'attachment_url' => '/chat/uploads/' . $uploaded_filename,
    'attachment_name' => $original_filename,
    'attachment_type' => $detected_type,
    'attachment_size' => $file_size
];

$this->httpClient->post('/chat/receive-message', ['json' => $localData]);
```

## 🛡️ **Garantias de Consistência**

### **Dados Sempre Salvos:**
- ✅ Mensagem nunca é perdida
- ✅ Phone number criado automaticamente se não existir  
- ✅ Tipo sempre definido como `lead`
- ✅ Timestamps automáticos

### **Metadados Seguros:**
- ✅ Nome do arquivo sempre presente (fallback: "attachment")
- ✅ Tipo sempre definido (fallback: "file")
- ✅ URLs sempre válidas (local ou externa)
- ✅ Tamanho opcional (pode ser null)

### **Logs Detalhados:**
```
📱 Receiving message from phone: +5511999999999
📄 Message has content: true
📎 Message has attachment: true  
🌐 External attachment detected - attempting download
✅ Attachment downloaded successfully: foto.jpg
📎 Final attachment details:
   URL: /chat/uploads/abc123_20250809_143022.jpg
   Name: foto.jpg
   Type: image
   Size: 245760
```

## 🔧 **Configurações e Limites**

```python
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp',  # Images
    'mp4', 'avi', 'mov', 'wmv', 'webm',   # Videos
    'mp3', 'wav', 'ogg', 'm4a', 'aac',    # Audio
    'pdf', 'doc', 'docx', 'txt',          # Documents
    'zip', 'rar'                          # Archives
}
WEBHOOK_TIMEOUT = 30  # segundos para download
```

## 🎉 **Benefícios da Nova Implementação**

1. **Robustez**: Sistema nunca falha por dados incompletos
2. **Flexibilidade**: Aceita múltiplos formatos de entrada
3. **Consistência**: Dados sempre padronizados
4. **Rastreabilidade**: Logs detalhados para debugging
5. **Performance**: Download assíncrono não bloqueia resposta
6. **Segurança**: Validação rigorosa de arquivos

**Conclusão**: Mesmo que você envie apenas uma URL sem metadados, o sistema irá tentar detectar automaticamente e, em último caso, criar valores padrão seguros. Suas mensagens nunca serão perdidas! 🚀
