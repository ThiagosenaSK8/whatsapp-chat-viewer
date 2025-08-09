# Message Type System Update

## 🎯 **Mudanças Implementadas**

### **Sistema Anterior**
- `user`: Todas as mensagens enviadas
- `ai`: Todas as mensagens recebidas (via webhook)

### **Sistema Novo** ✨
- `lead`: **Mensagens recebidas** de fontes externas (via webhook) - aparecem no lado esquerdo
- `user`: **Mensagens enviadas por humanos** quando IA está desativada - aparecem no lado direito com ícone de usuário
- `ai`: **Mensagens enviadas pela IA** quando IA está ativada - aparecem no lado direito com ícone de robô

## 🔄 **Lógica de Funcionamento**

### **Envio de Mensagens** (`/chat/send-message`)
1. Verifica o status da IA para o número de telefone
2. Se `phone.ai_active = True` → mensagem salva como tipo `ai`
3. Se `phone.ai_active = False` → mensagem salva como tipo `user`

### **Recebimento de Mensagens** (`/chat/receive-message`)
1. Todas as mensagens recebidas via webhook são salvas como tipo `lead`
2. Representam mensagens vindas de contatos externos

## 🎨 **Mudanças Visuais**

### **Interface do Chat**
- **Lead (esquerda)**: Ícone de telefone azul, fundo branco
- **User (direita)**: Ícone de usuário, fundo verde WhatsApp
- **AI (direita)**: Ícone de robô, fundo roxo

### **Cores por Tipo**
```css
/* Lead - Mensagens recebidas */
- Avatar: bg-blue-500 com ri-phone-line
- Bolha: bg-white com borda

/* User - Mensagens de humanos */  
- Avatar: bg-whatsapp-green com ri-user-line
- Bolha: bg-whatsapp-green
- Texto timestamp: text-green-100

/* AI - Mensagens da IA */
- Avatar: bg-purple-500 com ri-robot-line  
- Bolha: bg-purple-500
- Texto timestamp: text-purple-100
```

## 📁 **Arquivos Modificados**

### **Backend**
- `db/models.py`: Atualizado comentários e fallback para tipo `lead`
- `routes/chat.py`: 
  - Lógica para determinar tipo baseado em `phone.ai_active`
  - Endpoint `/receive-message` usa tipo `lead`
  - Webhook data inclui `message_type` e `ai_active`

### **Frontend**
- `static/js/chat.js`: 
  - Nova lógica com três tipos (`lead`, `user`, `ai`)
  - Variáveis `isOutgoing` e `isFromAI`
  - Cores e ícones diferenciados
  - Atualização em todas as funções de preview de anexo

### **Migração**
- `migrate_message_types.py`: Script para migrar dados existentes
  - Converte mensagens `ai` antigas para `lead`
  - Mantém mensagens `user` como estão
  - Inclui função de rollback

## 🚀 **Como Executar a Migração**

### **Migração Normal**
```bash
python migrate_message_types.py
```

### **Rollback (se necessário)**
```bash
python migrate_message_types.py rollback
```

## 📊 **Fluxo de Dados**

```mermaid
graph LR
    A[Contato Externo] -->|Webhook| B[/receive-message]
    B -->|type: 'lead'| C[Database]
    
    D[Interface Web] -->|AI Ativa| E[/send-message]
    D -->|AI Inativa| E
    E -->|type: 'ai'| C
    E -->|type: 'user'| C
    
    C --> F[Chat Interface]
    F --> G[Lead - Lado Esquerdo]
    F --> H[User/AI - Lado Direito]
```

## ✅ **Benefícios**

1. **Clareza Visual**: Três tipos distintos de mensagem
2. **Lógica Correta**: Reflete o fluxo real de conversação
3. **Flexibilidade**: Toggle de IA por número
4. **Webhook Rica**: Dados contextuais para sistemas externos
5. **Migração Segura**: Script com rollback incluído

## 🔧 **Próximos Passos**

1. Executar migração em produção
2. Testar interface com os três tipos
3. Verificar webhooks com os novos dados
4. Monitorar logs para garantir funcionamento correto

---
*Atualização implementada com sucesso! 🎉*
