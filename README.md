# 🕐 Sistema de Sincronização Automática de Hora - Windows

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-blue.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Stable-brightgreen.svg)]()

Sistema robusto e seguro para sincronização automática de data e hora do Windows usando servidores NTP confiáveis. Desenvolvido para ambientes corporativos que necessitam de precisão temporal e auditoria completa.

## 🚀 Características

- **Sincronização NTP**: Obtém hora precisa de servidores NTP confiáveis
- **Execução como Serviço**: Funciona como serviço Windows para operação contínua
- **Logging Completo**: Sistema de auditoria com rotação automática de logs
- **Tratamento de Erros**: Recuperação automática de falhas de rede e permissões
- **Configuração Flexível**: Todas as configurações via variáveis de ambiente
- **Validação de Segurança**: Verificações de privilégios e validações de entrada

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

Edite o arquivo `.env` com suas preferências:

```env
# Servidor NTP (padrão: pool.ntp.org)
NTP_SERVER=pool.ntp.org
NTP_TIMEOUT=10

# Configurações de logging
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/time_sync.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Intervalo de sincronização (em minutos)
SYNC_INTERVAL_MINUTES=60

# Tolerância de diferença (em segundos)
TIME_TOLERANCE_SECONDS=5
```

## 🎯 Modos de Execução

### 1. Execução Única
```bash
python main.py --once
```

### 2. Verificação de Status
```bash
python main.py --status
```

### 3. Execução Contínua
```bash
python main.py
```

### 4. Como Serviço Windows
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

### Erro de Privilégios
```
ERRO: Privilégios administrativos necessários
```
**Solução**: Execute como administrador

### Erro de Conectividade NTP
```
ERRO: Timeout ao conectar com servidor NTP
```
**Soluções**:
- Verifique conexão com internet
- Teste servidor NTP alternativo
- Verifique firewall/proxy

### Serviço não inicia
```
ERRO: Falha ao iniciar serviço
```
**Soluções**:
- Verifique logs em `logs/time_sync.log`
- Confirme instalação das dependências
- Execute diagnóstico: `python main.py --status`

## 📁 Estrutura do Projeto

```
projeto-automatic-windows-hora/
├── main.py                 # Script principal
├── config.py              # Configurações
├── ntp_client.py          # Cliente NTP
├── windows_time_sync.py   # Sincronização Windows
├── logger_config.py       # Sistema de logging
├── windows_service.py     # Serviço Windows
├── install_service.bat    # Instalador automático
├── requirements.txt       # Dependências Python
├── .env.example          # Exemplo de configuração
└── logs/                 # Diretório de logs
    └── time_sync.log     # Arquivo de log principal
```

## 🔄 Comandos Úteis

```bash
# Verificar status do serviço
sc query WindowsTimeSyncService

# Ver logs em tempo real (PowerShell)
Get-Content logs\time_sync.log -Wait -Tail 10

# Testar conectividade NTP
python -c "from ntp_client import NTPClient; print(NTPClient().test_connectivity())"

# Forçar sincronização única
python main.py --once
```

## 📊 Status do Projeto

- ✅ **Funcional**: Sistema totalmente operacional
- ✅ **Testado**: Validado em Windows 10/11
- ✅ **Documentado**: Documentação completa
- ✅ **Seguro**: Validações e tratamento de erros
- 🔄 **Mantido**: Atualizações regulares

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**: Linguagem principal
- **ntplib**: Cliente NTP para sincronização
- **pywin32**: Integração com APIs do Windows
- **schedule**: Agendamento de tarefas
- **python-dotenv**: Gerenciamento de configurações

## 📈 Roadmap

- [ ] Interface web para monitoramento
- [ ] Suporte a múltiplos servidores NTP
- [ ] Notificações por email
- [ ] Métricas de performance
- [ ] Dashboard de monitoramento

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

- **Desenvolvedor Principal** - *Trabalho inicial* - [Seu GitHub](https://github.com/seuusuario)

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