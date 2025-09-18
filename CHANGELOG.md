# 📝 Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Não Lançado]

### Planejado
- Interface web para monitoramento
- Suporte a múltiplos servidores NTP
- Notificações por email
- Métricas de performance
- Dashboard de monitoramento

## [1.0.0] - 2024-01-XX

### Adicionado
- Sistema completo de sincronização automática de hora
- Cliente NTP para obtenção de hora precisa
- Integração com APIs do Windows para atualização de hora
- Sistema de logging com rotação automática
- Execução como serviço Windows
- Configuração via variáveis de ambiente
- Tratamento robusto de erros e validações
- Script de instalação automatizada
- Documentação completa
- Testes de conectividade
- Múltiplos modos de execução (único, contínuo, status)

### Funcionalidades Principais
- **Sincronização NTP**: Conecta com pool.ntp.org para hora precisa
- **Privilégios Administrativos**: Gerencia elevação automática
- **Logging Auditável**: Registra todas as operações
- **Configuração Flexível**: Todas as configurações via .env
- **Execução Contínua**: Funciona como serviço Windows
- **Validação de Segurança**: Verificações de entrada e privilégios

### Arquivos Principais
- `main.py` - Script principal com tratamento de argumentos
- `config.py` - Gerenciamento de configurações
- `ntp_client.py` - Cliente NTP para sincronização
- `windows_time_sync.py` - Integração com Windows
- `logger_config.py` - Sistema de logging
- `windows_service.py` - Implementação como serviço
- `install_service.bat` - Instalador automatizado
- `test_connectivity.py` - Testes de conectividade

### Dependências
- `ntplib==0.4.0` - Cliente NTP
- `pywin32>=307` - APIs do Windows
- `schedule==1.2.0` - Agendamento de tarefas
- `python-dotenv==1.0.0` - Gerenciamento de configurações

### Configurações Suportadas
- `NTP_SERVER` - Servidor NTP (padrão: pool.ntp.org)
- `SYNC_INTERVAL` - Intervalo de sincronização
- `LOG_LEVEL` - Nível de logging
- `LOG_MAX_SIZE` - Tamanho máximo dos logs
- `LOG_BACKUP_COUNT` - Número de backups de log

## [0.1.0] - 2024-01-XX

### Adicionado
- Estrutura inicial do projeto
- Configuração básica de desenvolvimento
- Documentação inicial

---

## Tipos de Mudanças

- **Adicionado** para novas funcionalidades
- **Alterado** para mudanças em funcionalidades existentes
- **Descontinuado** para funcionalidades que serão removidas
- **Removido** para funcionalidades removidas
- **Corrigido** para correções de bugs
- **Segurança** para vulnerabilidades corrigidas