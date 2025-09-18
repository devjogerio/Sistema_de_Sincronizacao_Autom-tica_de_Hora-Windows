# 🕐 Sistema de Sincronização Automática de Hora - Windows

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-blue.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Stable-brightgreen.svg)]()

Sistema robusto e seguro para sincronização automática de data e hora do Windows usando servidores NTP confiáveis. Desenvolvido para ambientes corporativos que necessitam de precisão temporal e auditoria completa.

## 🚀 Características

### 🎯 Funcionalidades Principais
- **Sincronização NTP**: Obtém hora precisa de servidores NTP confiáveis
- **Interface Gráfica**: Dashboard moderno com monitoramento em tempo real
- **Arquitetura MVC**: Código organizado seguindo padrão Model-View-Controller
- **Execução como Serviço**: Funciona como serviço Windows para operação contínua
- **Monitoramento Visual**: Métricas de latência, precisão e status de conectividade

### 🔧 Recursos Técnicos
- **Logging Completo**: Sistema de auditoria com rotação automática de logs
- **Tratamento de Erros**: Recuperação automática de falhas de rede e permissões
- **Configuração Flexível**: Todas as configurações via variáveis de ambiente
- **Validação de Segurança**: Verificações de privilégios e validações de entrada
- **Notificações por Email**: Alertas automáticos para falhas críticas
- **Banco de Dados**: Armazenamento de métricas históricas e configurações

## 📋 Pré-requisitos

- Windows 10/11 ou Windows Server 2016+
- Python 3.8 ou superior
- Privilégios administrativos
- Conexão com a internet para acesso aos servidores NTP

## 🔧 Instalação

### 1. Clone ou baixe o projeto
```bash
git clone <repositorio>
cd projeto-automatic-windows-hora
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
copy .env.example .env

# Edite o arquivo .env com suas configurações
notepad .env
```

### 4. Instale como serviço (Recomendado)
```bash
# Execute como administrador
install_service.bat
```

**OU** instale manualmente:
```bash
# Como administrador
python windows_service.py install
python windows_service.py start
```

## ⚙️ Configuração

### 📝 Arquivo de Configuração (.env)
Edite o arquivo `.env` com suas preferências:

```env
# === Configurações do Servidor NTP ===
NTP_SERVER=pool.ntp.org
NTP_TIMEOUT=10
NTP_PORT=123

# === Configurações de Monitoramento ===
SYNC_INTERVAL_MINUTES=60
TIME_TOLERANCE_SECONDS=5
MAX_RETRY_ATTEMPTS=3

# === Configurações de Logging ===
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/time_sync.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# === Configurações de Email (Opcional) ===
EMAIL_ENABLED=false
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_app
EMAIL_TO=admin@empresa.com

# === Configurações da Interface ===
UI_THEME=modern
UI_UPDATE_INTERVAL=5
UI_SHOW_GRAPHS=true
UI_AUTO_START=false

# === Configurações do Banco de Dados ===
DB_PATH=data/ntp_monitor.db
DB_BACKUP_ENABLED=true
DB_RETENTION_DAYS=30
```

### 🔧 Configurações Avançadas
Para configurações mais específicas, edite diretamente os arquivos de modelo em `app/models/config_models.py`.

## 🎯 Modos de Execução

### 1. Interface Gráfica (Dashboard)
```bash
python main.py
```
**Funcionalidades do Dashboard:**
- 📊 **Monitoramento em Tempo Real**: Visualização de métricas NTP atualizadas
- 🎛️ **Controles Interativos**: Iniciar/parar monitoramento com um clique
- 📈 **Gráficos de Performance**: Latência, precisão e histórico de sincronização
- ⚙️ **Configurações Dinâmicas**: Alterar servidor NTP e intervalos sem reiniciar
- 🔔 **Alertas Visuais**: Notificações para falhas e problemas de conectividade
- 📋 **Logs Integrados**: Visualização de logs diretamente na interface

### 2. Execução Única (Linha de Comando)
```bash
python main.py --once
```

### 3. Verificação de Status
```bash
python main.py --status
```

### 4. Execução Contínua (Sem Interface)
```bash
python main.py --headless
```

### 5. Como Serviço Windows
```bash
# Instalar
python windows_service.py install

# Iniciar
net start WindowsTimeSyncService

# Parar
net stop WindowsTimeSyncService

# Desinstalar
python windows_service.py uninstall
```

## 📊 Monitoramento

### Logs
Os logs são salvos em `logs/time_sync.log` com rotação automática:
- Tentativas de sincronização
- Sucessos e falhas
- Erros de rede e permissões
- Eventos do serviço

### Status do Sistema
```bash
python main.py --status
```

Mostra:
- Hora atual do sistema
- Hora obtida do servidor NTP
- Diferença em segundos
- Status de conectividade
- Necessidade de sincronização

## 🔒 Segurança

- **Privilégios Administrativos**: Necessários para alterar a hora do sistema
- **Validação de Entrada**: Todas as configurações são validadas
- **Tratamento de Erros**: Falhas não comprometem a estabilidade do sistema
- **Logs de Auditoria**: Todas as alterações são registradas

## 🛠️ Solução de Problemas

### ❌ Problemas Comuns

#### Erro de Privilégios
```
ERRO: Privilégios administrativos necessários
```
**Solução**: Execute como administrador

#### Erro de Conectividade NTP
```
ERRO: Timeout ao conectar com servidor NTP
```
**Soluções**:
- Verifique conexão com internet
- Teste servidor NTP alternativo
- Verifique firewall/proxy

#### Serviço não inicia
```
ERRO: Falha ao iniciar serviço
```
**Soluções**:
- Verifique logs em `logs/time_sync.log`
- Confirme instalação das dependências
- Execute diagnóstico: `python main.py --status`

### 🖥️ Problemas da Interface Gráfica

#### Interface não abre
```
ERRO: Too early to create variable: no default root window
```
**Soluções**:
- Verifique se o Tkinter está instalado: `python -m tkinter`
- Execute: `python main.py --headless` para modo sem interface
- Reinstale dependências: `pip install -r requirements.txt`

#### Dashboard travando
```
ERRO: Interface não responde
```
**Soluções**:
- Feche e reabra a aplicação
- Verifique logs para erros de threading
- Execute com modo debug: `python main.py --debug`

### 🗄️ Problemas do Banco de Dados

#### Erro de acesso ao banco
```
ERRO: Database is locked
```
**Soluções**:
- Feche todas as instâncias da aplicação
- Verifique permissões na pasta `data/`
- Execute: `python -c "import sqlite3; sqlite3.connect('data/ntp_monitor.db').close()"`

#### Dados corrompidos
```
ERRO: Database disk image is malformed
```
**Soluções**:
- Faça backup do banco atual
- Delete `data/ntp_monitor.db`
- Reinicie a aplicação (criará novo banco)

### 📧 Problemas de Email

#### Falha no envio de emails
```
ERRO: SMTP Authentication failed
```
**Soluções**:
- Verifique credenciais no arquivo `.env`
- Use senha de aplicativo (Gmail, Outlook)
- Confirme configurações SMTP do provedor

## 📁 Estrutura do Projeto

### 🏗️ Arquitetura MVC
O projeto foi refatorado seguindo o padrão **Model-View-Controller (MVC)** para melhor organização e manutenibilidade:

```
projeto-automatic-windows-hora/
├── app/                      # 📦 Aplicação principal (MVC)
│   ├── controllers/          # 🎮 Controladores (lógica de negócio)
│   │   ├── dashboard_controller.py  # Controlador do dashboard
│   │   └── ntp_controller.py        # Controlador NTP
│   ├── models/              # 📊 Modelos (estruturas de dados)
│   │   ├── config_models.py         # Modelos de configuração
│   │   ├── ntp_metrics.py          # Métricas NTP
│   │   └── server_config.py        # Configuração de servidores
│   ├── services/            # 🔧 Serviços (lógica de aplicação)
│   │   ├── config_service.py       # Gerenciamento de configurações
│   │   ├── database_service.py     # Acesso ao banco de dados
│   │   ├── email_service.py        # Notificações por email
│   │   └── ntp_service.py          # Comunicação NTP
│   ├── utils/               # 🛠️ Utilitários
│   │   ├── formatters.py           # Formatação de dados
│   │   ├── logger.py               # Sistema de logging
│   │   └── validators.py           # Validações
│   └── views/               # 🖥️ Interface (apresentação)
│       ├── components.py           # Componentes reutilizáveis
│       └── dashboard_view.py       # Interface do dashboard
├── data/                    # 💾 Banco de dados
│   └── ntp_monitor.db      # SQLite database
├── exports/                 # 📤 Relatórios exportados
├── main.py                 # 🚀 Ponto de entrada principal
├── requirements.txt        # 📋 Dependências Python
├── .env.example           # ⚙️ Exemplo de configuração
└── logs/                  # 📝 Diretório de logs
    └── time_sync.log     # Arquivo de log principal
```

### 📚 Arquivos Legados (Compatibilidade)
```
├── config.py              # ⚠️ Configurações (legado)
├── ntp_client.py          # ⚠️ Cliente NTP (legado)
├── windows_time_sync.py   # ⚠️ Sincronização Windows (legado)
├── logger_config.py       # ⚠️ Sistema de logging (legado)
├── windows_service.py     # ⚠️ Serviço Windows (legado)
└── install_service.bat    # ⚠️ Instalador automático (legado)
```

## 🔄 Comandos Úteis

### 🖥️ Interface Gráfica
```bash
# Iniciar dashboard completo
python main.py

# Iniciar em modo debug
python main.py --debug

# Iniciar sem interface (headless)
python main.py --headless
```

### 🔧 Linha de Comando
```bash
# Verificar status do serviço
sc query WindowsTimeSyncService

# Ver logs em tempo real (PowerShell)
Get-Content logs\time_sync.log -Wait -Tail 10

# Testar conectividade NTP
python -c "from app.services.ntp_service import NTPService; print(NTPService().test_connectivity())"

# Forçar sincronização única
python main.py --once

# Exportar métricas para CSV
python -c "from app.services.database_service import DatabaseService; DatabaseService().export_metrics()"
```

### 🗄️ Banco de Dados
```bash
# Verificar integridade do banco
python -c "from app.services.database_service import DatabaseService; DatabaseService().check_integrity()"

# Fazer backup do banco
python -c "from app.services.database_service import DatabaseService; DatabaseService().backup_database()"

# Limpar dados antigos
python -c "from app.services.database_service import DatabaseService; DatabaseService().cleanup_old_data()"
```

## 📊 Status do Projeto

- ✅ **Funcional**: Sistema totalmente operacional
- ✅ **Testado**: Validado em Windows 10/11
- ✅ **Documentado**: Documentação completa
- ✅ **Seguro**: Validações e tratamento de erros
- 🔄 **Mantido**: Atualizações regulares

## 🛠️ Tecnologias Utilizadas

### 🐍 Backend & Core
- **Python 3.8+**: Linguagem principal
- **ntplib**: Cliente NTP para sincronização
- **pywin32**: Integração com APIs do Windows
- **schedule**: Agendamento de tarefas
- **python-dotenv**: Gerenciamento de configurações

### 🖥️ Interface Gráfica
- **tkinter**: Interface gráfica nativa do Python
- **matplotlib**: Gráficos e visualizações
- **PIL (Pillow)**: Processamento de imagens

### 🗄️ Banco de Dados & Persistência
- **sqlite3**: Banco de dados local
- **json**: Configurações e cache
- **csv**: Exportação de relatórios

### 📧 Comunicação & Alertas
- **smtplib**: Envio de emails
- **email**: Formatação de mensagens
- **logging**: Sistema de auditoria

### 🏗️ Arquitetura & Padrões
- **MVC Pattern**: Separação de responsabilidades
- **Service Layer**: Lógica de negócio centralizada
- **Repository Pattern**: Acesso a dados abstraído
- **Observer Pattern**: Comunicação entre componentes

## 📈 Roadmap

### ✅ Implementado (v2.0)
- [x] **Arquitetura MVC**: Refatoração completa seguindo padrões de design
- [x] **Interface Gráfica**: Dashboard moderno com Tkinter
- [x] **Banco de Dados**: Persistência de métricas e configurações
- [x] **Sistema de Alertas**: Notificações por email configuráveis
- [x] **Logging Avançado**: Sistema robusto de auditoria
- [x] **Configuração Flexível**: Gerenciamento via arquivo .env

### 🔄 Em Desenvolvimento (v2.1)
- [ ] **Testes Automatizados**: Cobertura completa de testes unitários
- [ ] **Documentação API**: Documentação técnica detalhada
- [ ] **Performance**: Otimizações de memória e CPU

### 🚀 Planejado (v3.0)
- [ ] **Interface Web**: Dashboard web responsivo
- [ ] **API REST**: Endpoints para integração externa
- [ ] **Múltiplos Servidores**: Suporte a pool de servidores NTP
- [ ] **Métricas Avançadas**: Análise estatística e tendências
- [ ] **Alertas Inteligentes**: Machine learning para detecção de anomalias
- [ ] **Relatórios**: Geração automática de relatórios PDF

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. **Fork** o projeto
2. **Crie** uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. **Abra** um Pull Request

### 📋 Diretrizes para Contribuição

- Mantenha o código limpo e bem documentado
- Adicione testes para novas funcionalidades
- Siga as convenções de código existentes
- Atualize a documentação quando necessário

## 👥 Autores

- **Desenvolvedor Principal** - *Trabalho inicial* - [Meu GitHub](https://github.com/devjogerio)

## 🙏 Agradecimentos

- Comunidade Python pela excelente documentação
- Contribuidores do projeto ntplib
- Microsoft pela documentação das APIs do Windows

## 📞 Suporte

Se você encontrar problemas ou tiver dúvidas:

1. Verifique a [documentação](README.md)
2. Procure em [Issues existentes](../../issues)
3. Crie uma [Nova Issue](../../issues/new)

## ⚠️ Avisos Importantes

- **Backup**: Sempre faça backup antes de implementar em produção
- **Testes**: Teste em ambiente controlado antes do uso em produção
- **Monitoramento**: Monitore os logs regularmente
- **Atualizações**: Mantenha as dependências atualizadas