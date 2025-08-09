# WhatsApp Chat Viewer

Um aplicativo web moderno para visualização e gerenciamento de conversas do WhatsApp com integração de IA.

## Características

- 🔐 **Autenticação segura** com login/registro
- 💬 **Interface estilo WhatsApp Web** para visualização de mensagens
- 🤖 **Toggle de IA** para ativar/desativar respostas automáticas por número
- 📊 **Painel de Analytics** com métricas detalhadas
- 🔄 **Integração com Webhook** para envio de mensagens
- 📱 **Design responsivo** otimizado para desktop e mobile
- 🎨 **UI/UX moderna** com Tailwind CSS e Remix Icons

## Tecnologias

### Backend
- **Framework**: Flask
- **Banco de Dados**: PostgreSQL com SQLAlchemy
- **Autenticação**: Flask-Login com bcrypt
- **Containerização**: Docker & Docker Compose

### Frontend
- **CSS**: Tailwind CSS (100%)
- **Icons**: Remix Icons
- **JavaScript**: Vanilla JS modular
- **Templates**: Jinja2

## Estrutura do Projeto

```
├── app.py                 # Aplicação principal Flask
├── templates.py           # Rotas de renderização
├── db/                    # Operações de banco
│   ├── models.py         # Modelos SQLAlchemy
│   ├── operations.py     # CRUD operations
│   └── connection.py     # Configuração do banco
├── routes/               # Rotas da API
│   ├── auth.py          # Autenticação
│   ├── chat.py          # Chat e mensagens
│   └── analytics.py     # Analytics e relatórios
├── templates/           # Templates HTML
│   ├── base/           # Templates base
│   ├── pages/          # Páginas individuais
│   └── components/     # Componentes reutilizáveis
├── static/             # Assets estáticos
│   └── js/            # JavaScript modular
├── requirements.txt    # Dependências Python
├── docker-compose.yml  # Configuração Docker
└── Dockerfile         # Imagem Docker
```

## Instalação e Uso

### 1. Usando Docker (Recomendado)

```bash
# Clone o repositório
git clone <repository-url>
cd whatsapp-chat-viewer

# Inicie os serviços
docker-compose up -d

# O aplicativo estará disponível em http://localhost:5000
```

### 2. Instalação Local

```bash
# Clone o repositório
git clone <repository-url>
cd whatsapp-chat-viewer

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure o banco PostgreSQL
# Edite o .env com suas configurações

# Execute a aplicação
python app.py
```

## Configuração

### Variáveis de Ambiente

Edite o arquivo `.env`:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/whatsapp_chat
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
WEBHOOK_URL=https://api.ilumin.app/webhook/7730fe92-3207-4611-acdf-30cc44d766aa
```

### Credenciais Padrão

O aplicativo cria automaticamente um usuário administrador:
- **Email**: admin@admin.com
- **Senha**: admin123

*⚠️ Altere essas credenciais em produção!*

## Funcionalidades

### 1. Gerenciamento de Números
- Adicionar números de WhatsApp
- Filtrar e buscar números
- Ativar/desativar IA por número

### 2. Chat Interface
- Visualização de mensagens estilo WhatsApp
- Bolhas diferenciadas para usuário/IA
- Envio de mensagens com integração webhook
- Timestamps e status de entrega

### 3. Analytics
- Mensagens totais por período
- Mensagens respondidas pela IA
- Cálculo de custos (R$ 0,10 por mensagem IA)
- Gráficos e relatórios detalhados

### 4. Integração Webhook
- Envio automático para API externa
- Tratamento de erros e retry
- Logs detalhados de operações

## Banco de Dados

### Tabelas Principais

**users**
- id, email, password_hash, created_at

**phone_numbers**
- id, number, ai_active, created_at

**messages**
- id, phone_number_id, content, type (user/ai), created_at

## API Endpoints

### Autenticação
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `POST /auth/register` - Registro

### Chat
- `GET /chat/phones` - Listar números
- `GET /chat/messages/<phone>` - Mensagens por número
- `POST /chat/send-message` - Enviar mensagem
- `POST /chat/toggle-ai/<id>` - Toggle IA
- `POST /chat/add-phone` - Adicionar número

### Analytics
- `GET /analytics/daily-stats` - Estatísticas diárias
- `GET /analytics/weekly-stats` - Estatísticas semanais
- `GET /analytics/monthly-stats` - Estatísticas mensais

## Desenvolvimento

### Princípios de Arquitetura
- **Modularidade**: Componentes reutilizáveis
- **Separação de responsabilidades**: Templates vs. Logic
- **Performance**: Lazy loading e otimizações
- **Segurança**: Validação e sanitização
- **Logging**: Rastreamento completo de operações

### Estrutura de Componentes
- Componentes reutilizáveis em `/templates/components/`
- JavaScript modular em `/static/js/`
- Estilos exclusivamente com Tailwind CSS

## Segurança

- ✅ Hashing de senhas com bcrypt
- ✅ Validação de entrada no backend
- ✅ Proteção contra XSS
- ✅ Prevenção de SQL injection
- ✅ Variáveis de ambiente para secrets
- ✅ Rate limiting (recomendado em produção)

## Produção

### Checklist de Deploy
- [ ] Alterar SECRET_KEY
- [ ] Alterar credenciais padrão
- [ ] Configurar SSL/HTTPS
- [ ] Configurar rate limiting
- [ ] Configurar monitoramento
- [ ] Backup automático do banco
- [ ] Configurar logs centralizados

## Suporte

Para dúvidas e suporte:
1. Verifique os logs da aplicação
2. Consulte a documentação da API
3. Abra uma issue no repositório

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.