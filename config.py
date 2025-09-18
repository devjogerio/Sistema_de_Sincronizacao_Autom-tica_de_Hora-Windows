"""
Módulo de configuração para o sistema de sincronização de hora do Windows.
Gerencia variáveis de ambiente e configurações padrão.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Classe para gerenciar configurações do sistema."""
    
    # Configurações do servidor NTP
    NTP_SERVER = os.getenv('NTP_SERVER', 'pool.ntp.org')
    NTP_TIMEOUT = int(os.getenv('NTP_TIMEOUT', '10'))
    
    # Configurações de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/time_sync.log')
    LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Configurações de sincronização
    SYNC_INTERVAL_MINUTES = int(os.getenv('SYNC_INTERVAL_MINUTES', '60'))
    TIME_TOLERANCE_SECONDS = int(os.getenv('TIME_TOLERANCE_SECONDS', '5'))
    
    # Configurações do serviço
    SERVICE_NAME = os.getenv('SERVICE_NAME', 'WindowsTimeSyncService')
    SERVICE_DISPLAY_NAME = os.getenv('SERVICE_DISPLAY_NAME', 'Windows Time Synchronization Service')
    SERVICE_DESCRIPTION = os.getenv('SERVICE_DESCRIPTION', 'Serviço para sincronização automática de data e hora do Windows')
    
    @classmethod
    def ensure_log_directory(cls):
        """Garante que o diretório de logs existe."""
        log_dir = Path(cls.LOG_FILE_PATH).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
    @classmethod
    def validate_config(cls):
        """Valida as configurações carregadas."""
        errors = []
        
        if cls.NTP_TIMEOUT <= 0:
            errors.append("NTP_TIMEOUT deve ser maior que 0")
            
        if cls.SYNC_INTERVAL_MINUTES <= 0:
            errors.append("SYNC_INTERVAL_MINUTES deve ser maior que 0")
            
        if cls.TIME_TOLERANCE_SECONDS < 0:
            errors.append("TIME_TOLERANCE_SECONDS deve ser maior ou igual a 0")
            
        if errors:
            raise ValueError(f"Configurações inválidas: {', '.join(errors)}")
        
        return True