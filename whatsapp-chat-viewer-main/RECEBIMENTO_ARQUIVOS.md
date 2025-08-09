# WhatsApp Chat Viewer - Recebimento de Arquivos

## Nova Funcionalidade: Recebimento de Mensagens com Anexos

### Endpoint para Recebimento

**URL:** `POST /chat/receive-message`

**Descrição:** Endpoint público para receber mensagens com anexos vindas de webhooks externos.

### Formato de Dados Esperado

```json
{
    "phone_number": "+5511999999999",
    "message": "Texto da mensagem (opcional)",
    "attachment_url": "https://external.com/path/to/file.jpg",
    "attachment_name": "foto.jpg",
    "attachment_type": "image"
}
```

### Campos Obrigatórios

- `phone_number`: Número do WhatsApp (obrigatório)
- `message` OU `attachment_url`: Pelo menos um deve estar presente

### Campos Opcionais

- `attachment_name`: Nome do arquivo
- `attachment_type`: Tipo do arquivo (image, video, audio, pdf, document, file)

### Funcionamento

1. **Recebe a requisição** do webhook externo
2. **Valida os dados** (número de telefone e conteúdo)
3. **Baixa o arquivo** da URL externa se fornecida
4. **Salva localmente** em `/static/uploads/`
5. **Cria a mensagem** no banco como tipo 'ai'
6. **Atualiza automaticamente** na interface via polling

### Recursos Implementados

#### ✅ Download Automático
- Baixa arquivos de URLs externas
- Valida tamanho (máx. 50MB)
- Verifica tipos permitidos
- Gera nomes únicos para evitar conflitos

#### ✅ Validação de Segurança
- Tipos de arquivo permitidos
- Limite de tamanho
- Sanitização de nomes
- Timeout de download (30s)

#### ✅ Atualização em Tempo Real
- Polling automático a cada 3 segundos
- Notificações de novas mensagens
- Pausa quando aba não está ativa
- Interface atualizada automaticamente

#### ✅ Tratamento de Erros
- Continua funcionando mesmo se download falhar
- Logs detalhados para debugging
- Resposta JSON padronizada

### Exemplo de Integração

```bash
# Enviar mensagem de texto
curl -X POST http://localhost:5000/chat/receive-message \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+5511999999999",
    "message": "Olá! Esta é uma mensagem recebida."
  }'

# Enviar mensagem com arquivo
curl -X POST http://localhost:5000/chat/receive-message \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+5511999999999",
    "message": "Aqui está a foto que você pediu",
    "attachment_url": "https://example.com/foto.jpg",
    "attachment_name": "foto.jpg",
    "attachment_type": "image"
  }'
```

### Resposta de Sucesso

```json
{
    "success": true,
    "message": {
        "id": 123,
        "phone_number_id": 1,
        "content": "Texto da mensagem",
        "type": "ai",
        "created_at": "2025-07-31T12:34:56.789Z",
        "attachment_url": "/chat/uploads/abc123_20250731_123456.jpg",
        "attachment_full_url": "http://localhost:5000/chat/uploads/abc123_20250731_123456.jpg",
        "attachment_name": "foto.jpg",
        "attachment_type": "image",
        "attachment_size": 1024000
    },
    "attachment_downloaded": true
}
```

### Configuração no Webhook Externo

Para integrar com seu sistema externo, configure o webhook para enviar mensagens recebidas para:

```
POST http://seu-dominio.com/chat/receive-message
```

### Logs e Monitoramento

Todos os recebimentos são logados com:
- Número de telefone
- Dados da mensagem
- Status do download
- Erros (se houver)

### Próximos Passos

1. **Configure seu webhook externo** para usar o endpoint `/chat/receive-message`
2. **Teste com mensagens simples** primeiro
3. **Teste com anexos** depois
4. **Monitore os logs** para verificar o funcionamento

### Limitações

- **Tamanho máximo:** 50MB por arquivo
- **Tipos permitidos:** Imagens, vídeos, áudios, PDFs, documentos, arquivos
- **Timeout:** 30 segundos para download
- **Polling:** 3 segundos de intervalo para atualizações

---

**Status:** ✅ **IMPLEMENTADO E FUNCIONANDO**

A funcionalidade de recebimento de arquivos está completamente implementada e pronta para uso!