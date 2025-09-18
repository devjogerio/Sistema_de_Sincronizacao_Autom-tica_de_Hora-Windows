"""
Serviço para gerenciamento de configurações.
Centraliza o carregamento e validação de todas as configurações do sistema.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

from ..models.server_config import ServerConfig
from ..models.config_models import EmailConfig, AlertConfig, MonitoringConfig, UIConfig

logger = logging.getLogger(__name__)


class ConfigService:
    """
    Serviço para gerenciamento de configurações do sistema.
    
    Responsável por carregar, validar e fornecer acesso
    a todas as configurações da aplicação.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Inicializa o serviço de configuração.
        
        Args:
            config_file: Caminho para o arquivo de configuração
        """
        self.config_file = Path(config_file)
        self._config_data = {}
        self._servers = []
        self._email_config = None
        self._alert_config = None
        self._monitoring_config = None
        self._ui_config = None
        
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Carrega as configurações do arquivo JSON.
        
        Returns:
            bool: True se carregou com sucesso, False caso contrário
        """
        try:
            if not self.config_file.exists():
                logger.error(f"Arquivo de configuração não encontrado: {self.config_file}")
                self._create_default_config()
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
            
            # Carrega configurações específicas
            self._load_server_configs()
            self._load_email_config()
            self._load_alert_config()
            self._load_monitoring_config()
            self._load_ui_config()
            
            logger.info(f"Configurações carregadas com sucesso de {self.config_file}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON do arquivo de configuração: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            return False
    
    def _load_server_configs(self):
        """Carrega configurações dos servidores NTP."""
        servers_data = self._config_data.get('ntp_servers', [])
        self._servers = []
        
        for server_data in servers_data:
            try:
                server_config = ServerConfig.from_dict(server_data)
                if server_config.validate():
                    self._servers.append(server_config)
                else:
                    logger.warning(f"Configuração inválida para servidor: {server_data}")
            except Exception as e:
                logger.error(f"Erro ao carregar servidor {server_data}: {e}")
    
    def _load_email_config(self):
        """Carrega configuração de email."""
        email_data = self._config_data.get('email', {})
        # Remove campos antigos que não existem mais
        email_data.pop('from_address', None)
        email_data.pop('to_addresses', None)
        try:
            self._email_config = EmailConfig.from_dict(email_data)
        except Exception as e:
            logger.error(f"Erro ao carregar configuração de email: {e}")
            self._email_config = EmailConfig()
    
    def _load_alert_config(self):
        """Carrega configuração de alertas."""
        alert_data = self._config_data.get('alerts', {})
        # Mapeia campos antigos para novos
        if 'offset_threshold' in alert_data:
            alert_data['high_offset_threshold'] = alert_data.pop('offset_threshold')
        if 'response_time_threshold' in alert_data:
            alert_data['slow_response_threshold'] = alert_data.pop('response_time_threshold')
        # Remove campos antigos que não existem mais
        alert_data.pop('email_enabled', None)
        alert_data.pop('console_enabled', None)
        try:
            self._alert_config = AlertConfig.from_dict(alert_data)
        except Exception as e:
            logger.error(f"Erro ao carregar configuração de alertas: {e}")
            self._alert_config = AlertConfig()
    
    def _load_monitoring_config(self):
        """Carrega configuração de monitoramento."""
        monitoring_data = self._config_data.get('monitoring', {})
        # Mapeia campos antigos para novos
        if 'check_interval' in monitoring_data:
            monitoring_data['update_interval'] = monitoring_data.pop('check_interval')
        # Remove campos antigos que não existem mais
        monitoring_data.pop('max_workers', None)
        monitoring_data.pop('retry_attempts', None)
        monitoring_data.pop('retry_delay', None)
        monitoring_data.pop('database_file', None)
        try:
            self._monitoring_config = MonitoringConfig.from_dict(monitoring_data)
        except Exception as e:
            logger.error(f"Erro ao carregar configuração de monitoramento: {e}")
            self._monitoring_config = MonitoringConfig()
    
    def _load_ui_config(self):
        """Carrega configuração da interface."""
        ui_data = self._config_data.get('ui', {})
        # Remove campos antigos que não existem mais
        ui_data.pop('chart_history_hours', None)
        ui_data.pop('show_grid', None)
        ui_data.pop('auto_scale', None)
        try:
            self._ui_config = UIConfig.from_dict(ui_data)
        except Exception as e:
            logger.error(f"Erro ao carregar configuração da UI: {e}")
            self._ui_config = UIConfig()
    
    def _create_default_config(self):
        """Cria um arquivo de configuração padrão."""
        default_config = {
            "ntp_servers": [
                {
                    "name": "pool.ntp.org",
                    "address": "pool.ntp.org",
                    "priority": 1,
                    "timeout": 5,
                    "enabled": True
                },
                {
                    "name": "time.google.com",
                    "address": "time.google.com",
                    "priority": 2,
                    "timeout": 5,
                    "enabled": True
                }
            ],
            "monitoring": {
                "check_interval": 60,
                "max_workers": 10,
                "retry_attempts": 3,
                "retry_delay": 5,
                "database_file": "ntp_monitor.db"
            },
            "alerts": {
                "offset_threshold": 1.0,
                "response_time_threshold": 5.0,
                "availability_threshold": 80.0,
                "email_enabled": False,
                "console_enabled": True
            },
            "email": {
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_address": "",
                "to_addresses": [],
                "use_tls": True,
                "enabled": False
            },
            "ui": {
                "theme": "light",
                "refresh_interval": 30,
                "chart_history_hours": 24,
                "show_grid": True,
                "auto_scale": True
            }
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"Arquivo de configuração padrão criado: {self.config_file}")
        except Exception as e:
            logger.error(f"Erro ao criar arquivo de configuração padrão: {e}")
    
    def get_servers(self) -> List[ServerConfig]:
        """
        Retorna lista de servidores NTP configurados.
        
        Returns:
            List[ServerConfig]: Lista de configurações de servidores
        """
        return self._servers.copy()
    
    def get_enabled_servers(self) -> List[ServerConfig]:
        """
        Retorna apenas servidores habilitados.
        
        Returns:
            List[ServerConfig]: Lista de servidores habilitados
        """
        return [server for server in self._servers if server.enabled]
    
    def get_email_config(self) -> EmailConfig:
        """
        Retorna configuração de email.
        
        Returns:
            EmailConfig: Configuração de email
        """
        return self._email_config
    
    def get_alert_config(self) -> AlertConfig:
        """
        Retorna configuração de alertas.
        
        Returns:
            AlertConfig: Configuração de alertas
        """
        return self._alert_config
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """
        Retorna configuração de monitoramento.
        
        Returns:
            MonitoringConfig: Configuração de monitoramento
        """
        return self._monitoring_config
    
    def get_ui_config(self) -> UIConfig:
        """
        Retorna configuração da interface.
        
        Returns:
            UIConfig: Configuração da interface
        """
        return self._ui_config
    
    def get_config(self):
        """
        Retorna objeto com todas as configurações.
        
        Returns:
            object: Objeto com todas as configurações
        """
        class Config:
            def __init__(self, email_config, alert_config, monitoring_config, ui_config, servers):
                self.email = email_config
                self.alerts = alert_config
                self.monitoring = monitoring_config
                self.ui = ui_config
                self.servers = servers
        
        return Config(
            self._email_config,
            self._alert_config,
            self._monitoring_config,
            self._ui_config,
            self._servers
        )

    def save_config(self) -> bool:
        """
        Salva as configurações atuais no arquivo.
        
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            config_data = {
                "ntp_servers": [server.to_dict() for server in self._servers],
                "email": self._email_config.to_dict() if self._email_config else {},
                "alerts": self._alert_config.to_dict() if self._alert_config else {},
                "monitoring": self._monitoring_config.to_dict() if self._monitoring_config else {},
                "ui": self._ui_config.to_dict() if self._ui_config else {}
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configurações salvas com sucesso em {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            return False
    
    def validate_config(self) -> Dict[str, List[str]]:
        """
        Valida todas as configurações carregadas.
        
        Returns:
            Dict[str, List[str]]: Dicionário com erros de validação por categoria
        """
        errors = {
            'servers': [],
            'email': [],
            'alerts': [],
            'monitoring': [],
            'ui': []
        }
        
        # Valida servidores
        if not self._servers:
            errors['servers'].append("Nenhum servidor NTP configurado")
        else:
            for server in self._servers:
                if not server.validate():
                    errors['servers'].append(f"Servidor inválido: {server.name}")
        
        # Valida configuração de email se habilitada
        if self._email_config and self._email_config.enabled:
            if not self._email_config.smtp_server:
                errors['email'].append("Servidor SMTP não configurado")
            if not self._email_config.from_address:
                errors['email'].append("Endereço de origem não configurado")
            if not self._email_config.to_addresses:
                errors['email'].append("Nenhum destinatário configurado")
        
        return {k: v for k, v in errors.items() if v}  # Remove categorias sem erros