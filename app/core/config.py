"""
Configurações da aplicação NTP Monitor
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Configurações da aplicação
    """
    
    # Configurações do servidor
    host: str = Field(default="localhost", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Configurações do banco de dados
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/ntp_monitor.db",
        env="DATABASE_URL"
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Configurações de segurança
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        env="SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    
    # Configurações de email
    smtp_server: Optional[str] = Field(default=None, env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    email_from: Optional[str] = Field(default=None, env="EMAIL_FROM")
    email_from_name: str = Field(default="NTP Monitor", env="EMAIL_FROM_NAME")
    
    # Configurações de monitoramento
    auto_monitoring_enabled: bool = Field(default=True, env="AUTO_MONITORING_ENABLED")
    monitoring_interval: int = Field(default=300, env="MONITORING_INTERVAL")
    max_concurrent_checks: int = Field(default=10, env="MAX_CONCURRENT_CHECKS")
    request_timeout: int = Field(default=10, env="REQUEST_TIMEOUT")
    
    # Configurações de alertas
    alert_email_enabled: bool = Field(default=False, env="ALERT_EMAIL_ENABLED")
    alert_threshold_offset: float = Field(default=100.0, env="ALERT_THRESHOLD_OFFSET")
    alert_threshold_delay: float = Field(default=1000.0, env="ALERT_THRESHOLD_DELAY")
    alert_threshold_jitter: float = Field(default=50.0, env="ALERT_THRESHOLD_JITTER")
    
    # Configurações de relatórios
    reports_dir: str = Field(default="./exports", env="REPORTS_DIR")
    report_retention_days: int = Field(default=30, env="REPORT_RETENTION_DAYS")
    
    # Configurações de cache
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    
    # Configurações de desenvolvimento
    reload: bool = Field(default=False, env="RELOAD")
    workers: int = Field(default=1, env="WORKERS")
    
    # Configurações de CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE"],
        env="CORS_METHODS"
    )
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância global das configurações
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Retorna a instância das configurações (singleton)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Recarrega as configurações
    """
    global _settings
    _settings = Settings()
    return _settings