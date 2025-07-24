# WhatsApp Chat Viewer

Sistema profissional de visualização e gerenciamento de conversas WhatsApp com interface estilo WhatsApp Web.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## ✨ Features

- 🔐 **Autenticação Segura** - Sistema de login com bcrypt
- 💬 **Interface WhatsApp Web** - Design responsivo e moderno
- 🤖 **IA Toggle** - Controle de IA por número
- 📊 **Analytics Dashboard** - Métricas e relatórios
- 📎 **Upload de Arquivos** - Suporte a imagens, PDFs e áudios
- 🔍 **Busca em Tempo Real** - Pesquisar mensagens instantaneamente
- 😊 **Picker de Emojis** - Interface completa de emojis
- 🔗 **Webhooks** - Integração com APIs externas
- ⚙️ **Configurações** - Painel de configurações completo

## 🚀 Deploy Rápido

```bash
# Clone o repositório
git clone https://github.com/SEU_USUARIO/whatsapp-chat-viewer.git
cd whatsapp-chat-viewer

# Setup inicial
./setup.sh

# Configure suas variáveis
cp .env.example .env
nano .env

# Deploy
./deploy.sh production
```

## 📋 Requisitos

- Docker & Docker Compose
- 2GB+ RAM
- 10GB+ armazenamento

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```bash
# Flask
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=production

# Database
POSTGRES_PASSWORD=senha-segura
DATABASE_URL=postgresql://postgres:senha@postgres:5432/whatsapp_chat

# Application
APP_PORT=5000

# Webhooks (configure na interface)
WEBHOOK_SEND_URL=https://sua-api.com/webhook/send
WEBHOOK_RECEIVE_URL=https://sua-api.com/webhook/receive
```

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Frontend      │    │   Backend    │    │  Database   │
│   (HTML/JS)     │◄──►│   (Flask)    │◄──►│ PostgreSQL  │
└─────────────────┘    └──────────────┘    └─────────────┘
         │                       │
         │              ┌────────▼────────┐
         │              │   Webhook API   │
         └──────────────►│   Integration   │
                        └─────────────────┘
```

## 📊 Screenshots

<!-- Adicione screenshots aqui -->

## 🛠️ Desenvolvimento

```bash
# Clone para desenvolvimento
git clone https://github.com/SEU_USUARIO/whatsapp-chat-viewer.git
cd whatsapp-chat-viewer

# Executar em modo desenvolvimento
python run_local.py
```

## 📚 Documentação

- [Guia de Instalação](docs/installation.md)
- [Configuração de Webhooks](docs/webhooks.md)
- [API Reference](docs/api.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/amazing-feature`)
3. Commit suas mudanças (`git commit -m 'Add amazing feature'`)
4. Push para a branch (`git push origin feature/amazing-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

**Seu Nome**
- GitHub: [@seu-usuario](https://github.com/seu-usuario)
- Email: seu-email@exemplo.com

## 🙏 Agradecimentos

- [Flask](https://flask.palletsprojects.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Docker](https://www.docker.com/)

---
⭐ **Star este repositório se ele te ajudou!**