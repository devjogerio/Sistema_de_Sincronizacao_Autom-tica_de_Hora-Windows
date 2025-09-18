"""
Modelos de configuração do sistema NTP Monitor.
Define estruturas de dados para diferentes tipos de configuração.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class EmailConfig:
    """
    Configuração de email para notificações.
    
    Attributes:
        enabled: Se o email está habilitado
        smtp_server: Servidor SMTP
        smtp_port: Porta do servidor SMTP
        username: Nome de usuário para autenticação
        password: Senha para autenticação
        use_tls: Se deve usar TLS
        sender_name: Nome do remetente
        recipients: Lista de destinatários
    """
    enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    sender_name: str = "NTP Monitor"
    recipients: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'enabled': self.enabled,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'username': self.username,
            'password': self.password,
            'use_tls': self.use_tls,
            'sender_name': self.sender_name,
            'recipients': self.recipients
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailConfig':
        """Cria instância a partir de dicionário."""
        return cls(**data)


@dataclass
class AlertConfig:
    """
    Configuração de alertas do sistema.
    
    Attributes:
        enabled: Se os alertas estão habilitados
        check_interval: Intervalo de verificação em segundos
        high_offset_threshold: Threshold para offset alto em segundos
        slow_response_threshold: Threshold para resposta lenta em segundos
        availability_threshold: Threshold de disponibilidade em porcentagem
        cooldown_minutes: Tempo de cooldown entre alertas em minutos
    """
    enabled: bool = True
    check_interval: int = 60
    high_offset_threshold: float = 5.0
    slow_response_threshold: float = 10.0
    availability_threshold: float = 95.0
    cooldown_minutes: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'enabled': self.enabled,
            'check_interval': self.check_interval,
            'high_offset_threshold': self.high_offset_threshold,
            'slow_response_threshold': self.slow_response_threshold,
            'availability_threshold': self.availability_threshold,
            'cooldown_minutes': self.cooldown_minutes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertConfig':
        """Cria instância a partir de dicionário."""
        return cls(**data)


@dataclass
class MonitoringConfig:
    """
    Configuração de monitoramento.
    
    Attributes:
        update_interval: Intervalo de atualização em segundos
        history_retention_days: Dias de retenção do histórico
        max_concurrent_checks: Máximo de verificações simultâneas
        auto_start: Se deve iniciar automaticamente
        log_level: Nível de log
    """
    update_interval: int = 30
    history_retention_days: int = 30
    max_concurrent_checks: int = 10
    auto_start: bool = True
    log_level: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'update_interval': self.update_interval,
            'history_retention_days': self.history_retention_days,
            'max_concurrent_checks': self.max_concurrent_checks,
            'auto_start': self.auto_start,
            'log_level': self.log_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitoringConfig':
        """Cria instância a partir de dicionário."""
        return cls(**data)


@dataclass
class UIConfig:
    """
    Configuração da interface do usuário.
    
    Attributes:
        theme: Tema da interface (dark, light)
        auto_refresh: Se deve atualizar automaticamente
        refresh_interval: Intervalo de atualização em segundos
        show_graphs: Se deve mostrar gráficos
        window_width: Largura da janela
        window_height: Altura da janela
    """
    theme: str = "dark"
    auto_refresh: bool = True
    refresh_interval: int = 5
    show_graphs: bool = True
    window_width: int = 1200
    window_height: int = 800
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'theme': self.theme,
            'auto_refresh': self.auto_refresh,
            'refresh_interval': self.refresh_interval,
            'show_graphs': self.show_graphs,
            'window_width': self.window_width,
            'window_height': self.window_height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIConfig':
        """Cria instância a partir de dicionário."""
        return cls(**data)