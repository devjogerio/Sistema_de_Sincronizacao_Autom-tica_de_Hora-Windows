"""
Gerenciador de configurações avançado para o sistema de monitoramento NTP.
Implementa configurações para múltiplos servidores, email e interface.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    """Configuração de um servidor NTP."""
    name: str
    address: str
    timeout: int = 5
    priority: int = 1  # 1=alta, 2=média, 3=baixa
    enabled: bool = True
    description: str = ""

@dataclass
class EmailConfig:
    """Configuração de email."""
    enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    sender_name: str = "NTP Monitor"
    recipients: List[str] = None
    
    def __post_init__(self):
        if self.recipients is None:
            self.recipients = []

@dataclass
class AlertConfig:
    """Configuração de alertas."""
    enabled: bool = True
    check_interval: int = 60  # segundos
    high_offset_threshold: float = 5.0  # segundos
    slow_response_threshold: float = 10.0  # segundos
    availability_threshold: float = 95.0  # porcentagem
    cooldown_minutes: int = 30

@dataclass
class MonitoringConfig:
    """Configuração de monitoramento."""
    update_interval: int = 30  # segundos
    history_retention_days: int = 30
    max_concurrent_checks: int = 10
    auto_start: bool = True
    log_level: str = "INFO"

@dataclass
class UIConfig:
    """Configuração da interface."""
    theme: str = "dark"  # dark, light
    auto_refresh: bool = True
    refresh_interval: int = 5  # segundos
    show_graphs: bool = True
    window_width: int = 1200
    window_height: int = 800

class ConfigManager:
    """Gerenciador centralizado de configurações."""
    
    def __init__(self, config_file: str = "ntp_monitor_config.json"):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            config_file: Caminho para o arquivo de configuração
        """
        self.config_file = config_file
        self.servers: List[ServerConfig] = []
        self.email: EmailConfig = EmailConfig()
        self.alerts: AlertConfig = AlertConfig()
        self.monitoring: MonitoringConfig = MonitoringConfig()
        self.ui: UIConfig = UIConfig()
        
        # Carrega configurações existentes ou cria padrão
        self.load_config()
    
    def get_default_servers(self) -> List[ServerConfig]:
        """
        Retorna lista de servidores NTP padrão.
        
        Returns:
            List[ServerConfig]: Lista de servidores padrão
        """
        return [
            ServerConfig(
                name="Pool NTP Brasil",
                address="br.pool.ntp.org",
                priority=1,
                description="Pool de servidores NTP do Brasil"
            ),
            ServerConfig(
                name="NIST Time Server",
                address="time.nist.gov",
                priority=1,
                description="Servidor oficial do NIST (EUA)"
            ),
            ServerConfig(
                name="Google Time",
                address="time.google.com",
                priority=2,
                description="Servidor de tempo do Google"
            ),
            ServerConfig(
                name="Cloudflare Time",
                address="time.cloudflare.com",
                priority=2,
                description="Servidor de tempo da Cloudflare"
            ),
            ServerConfig(
                name="Ubuntu NTP",
                address="ntp.ubuntu.com",
                priority=3,
                description="Servidor NTP do Ubuntu"
            ),
            ServerConfig(
                name="Pool NTP Global",
                address="pool.ntp.org",
                priority=2,
                description="Pool global de servidores NTP"
            )
        ]
    
    def load_config(self):
        """Carrega configurações do arquivo."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Carrega servidores
                if 'servers' in config_data:
                    self.servers = [
                        ServerConfig(**server_data) 
                        for server_data in config_data['servers']
                    ]
                else:
                    self.servers = self.get_default_servers()
                
                # Carrega configurações de email
                if 'email' in config_data:
                    self.email = EmailConfig(**config_data['email'])
                
                # Carrega configurações de alertas
                if 'alerts' in config_data:
                    self.alerts = AlertConfig(**config_data['alerts'])
                
                # Carrega configurações de monitoramento
                if 'monitoring' in config_data:
                    self.monitoring = MonitoringConfig(**config_data['monitoring'])
                
                # Carrega configurações de UI
                if 'ui' in config_data:
                    self.ui = UIConfig(**config_data['ui'])
                
                logger.info(f"Configurações carregadas de {self.config_file}")
            
            else:
                # Cria configuração padrão
                self.servers = self.get_default_servers()
                self.save_config()
                logger.info("Configuração padrão criada")
        
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            # Em caso de erro, usa configuração padrão
            self.servers = self.get_default_servers()
    
    def save_config(self):
        """Salva configurações no arquivo."""
        try:
            config_data = {
                'servers': [asdict(server) for server in self.servers],
                'email': asdict(self.email),
                'alerts': asdict(self.alerts),
                'monitoring': asdict(self.monitoring),
                'ui': asdict(self.ui)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configurações salvas em {self.config_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            raise
    
    def get_enabled_servers(self) -> List[ServerConfig]:
        """
        Retorna apenas servidores habilitados.
        
        Returns:
            List[ServerConfig]: Lista de servidores habilitados
        """
        return [server for server in self.servers if server.enabled]
    
    def get_servers_by_priority(self, priority: int = None) -> List[ServerConfig]:
        """
        Retorna servidores filtrados por prioridade.
        
        Args:
            priority: Prioridade desejada (1=alta, 2=média, 3=baixa)
            
        Returns:
            List[ServerConfig]: Lista de servidores filtrados
        """
        enabled_servers = self.get_enabled_servers()
        
        if priority is None:
            return sorted(enabled_servers, key=lambda s: s.priority)
        
        return [server for server in enabled_servers if server.priority == priority]
    
    def add_server(self, server: ServerConfig) -> bool:
        """
        Adiciona um novo servidor.
        
        Args:
            server: Configuração do servidor
            
        Returns:
            bool: True se adicionado com sucesso
        """
        try:
            # Verifica se já existe servidor com mesmo endereço
            existing = next((s for s in self.servers if s.address == server.address), None)
            if existing:
                logger.warning(f"Servidor {server.address} já existe")
                return False
            
            self.servers.append(server)
            self.save_config()
            logger.info(f"Servidor {server.name} ({server.address}) adicionado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar servidor: {e}")
            return False
    
    def remove_server(self, address: str) -> bool:
        """
        Remove um servidor pelo endereço.
        
        Args:
            address: Endereço do servidor
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            original_count = len(self.servers)
            self.servers = [s for s in self.servers if s.address != address]
            
            if len(self.servers) < original_count:
                self.save_config()
                logger.info(f"Servidor {address} removido")
                return True
            else:
                logger.warning(f"Servidor {address} não encontrado")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao remover servidor: {e}")
            return False
    
    def update_server(self, address: str, **kwargs) -> bool:
        """
        Atualiza configurações de um servidor.
        
        Args:
            address: Endereço do servidor
            **kwargs: Campos a serem atualizados
            
        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            server = next((s for s in self.servers if s.address == address), None)
            if not server:
                logger.warning(f"Servidor {address} não encontrado")
                return False
            
            # Atualiza campos fornecidos
            for key, value in kwargs.items():
                if hasattr(server, key):
                    setattr(server, key, value)
            
            self.save_config()
            logger.info(f"Servidor {address} atualizado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar servidor: {e}")
            return False
    
    def update_email_config(self, **kwargs):
        """
        Atualiza configurações de email.
        
        Args:
            **kwargs: Campos a serem atualizados
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.email, key):
                    setattr(self.email, key, value)
            
            self.save_config()
            logger.info("Configurações de email atualizadas")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configurações de email: {e}")
            raise
    
    def update_alert_config(self, **kwargs):
        """
        Atualiza configurações de alertas.
        
        Args:
            **kwargs: Campos a serem atualizados
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.alerts, key):
                    setattr(self.alerts, key, value)
            
            self.save_config()
            logger.info("Configurações de alertas atualizadas")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configurações de alertas: {e}")
            raise
    
    def update_monitoring_config(self, **kwargs):
        """
        Atualiza configurações de monitoramento.
        
        Args:
            **kwargs: Campos a serem atualizados
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.monitoring, key):
                    setattr(self.monitoring, key, value)
            
            self.save_config()
            logger.info("Configurações de monitoramento atualizadas")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configurações de monitoramento: {e}")
            raise
    
    def update_ui_config(self, **kwargs):
        """
        Atualiza configurações da interface.
        
        Args:
            **kwargs: Campos a serem atualizados
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.ui, key):
                    setattr(self.ui, key, value)
            
            self.save_config()
            logger.info("Configurações da interface atualizadas")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configurações da interface: {e}")
            raise
    
    def get_server_addresses(self) -> List[str]:
        """
        Retorna lista de endereços dos servidores habilitados.
        
        Returns:
            List[str]: Lista de endereços
        """
        return [server.address for server in self.get_enabled_servers()]
    
    def validate_config(self) -> Dict[str, List[str]]:
        """
        Valida todas as configurações.
        
        Returns:
            Dict[str, List[str]]: Dicionário com erros encontrados por categoria
        """
        errors = {
            'servers': [],
            'email': [],
            'alerts': [],
            'monitoring': [],
            'ui': []
        }
        
        # Valida servidores
        if not self.servers:
            errors['servers'].append("Nenhum servidor configurado")
        
        enabled_servers = self.get_enabled_servers()
        if not enabled_servers:
            errors['servers'].append("Nenhum servidor habilitado")
        
        for server in self.servers:
            if not server.address:
                errors['servers'].append(f"Servidor '{server.name}' sem endereço")
            if server.timeout <= 0:
                errors['servers'].append(f"Timeout inválido para '{server.name}'")
        
        # Valida email (se habilitado)
        if self.email.enabled:
            if not self.email.smtp_server:
                errors['email'].append("Servidor SMTP não configurado")
            if not self.email.username:
                errors['email'].append("Usuário de email não configurado")
            if not self.email.recipients:
                errors['email'].append("Nenhum destinatário configurado")
        
        # Valida alertas
        if self.alerts.check_interval <= 0:
            errors['alerts'].append("Intervalo de verificação inválido")
        if self.alerts.high_offset_threshold <= 0:
            errors['alerts'].append("Limite de offset inválido")
        
        # Valida monitoramento
        if self.monitoring.update_interval <= 0:
            errors['monitoring'].append("Intervalo de atualização inválido")
        if self.monitoring.history_retention_days <= 0:
            errors['monitoring'].append("Retenção de histórico inválida")
        
        return errors
    
    def export_config(self, file_path: str) -> bool:
        """
        Exporta configurações para arquivo.
        
        Args:
            file_path: Caminho do arquivo de destino
            
        Returns:
            bool: True se exportado com sucesso
        """
        try:
            config_data = {
                'servers': [asdict(server) for server in self.servers],
                'email': asdict(self.email),
                'alerts': asdict(self.alerts),
                'monitoring': asdict(self.monitoring),
                'ui': asdict(self.ui),
                'export_timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configurações exportadas para {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar configurações: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """
        Importa configurações de arquivo.
        
        Args:
            file_path: Caminho do arquivo de origem
            
        Returns:
            bool: True se importado com sucesso
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Backup da configuração atual
            backup_file = f"{self.config_file}.backup"
            self.export_config(backup_file)
            
            # Importa nova configuração
            if 'servers' in config_data:
                self.servers = [
                    ServerConfig(**server_data) 
                    for server_data in config_data['servers']
                ]
            
            if 'email' in config_data:
                self.email = EmailConfig(**config_data['email'])
            
            if 'alerts' in config_data:
                self.alerts = AlertConfig(**config_data['alerts'])
            
            if 'monitoring' in config_data:
                self.monitoring = MonitoringConfig(**config_data['monitoring'])
            
            if 'ui' in config_data:
                self.ui = UIConfig(**config_data['ui'])
            
            # Salva configuração importada
            self.save_config()
            
            logger.info(f"Configurações importadas de {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao importar configurações: {e}")
            return False