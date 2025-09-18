"""
Módulo de configuração de logging para auditoria do sistema de sincronização.
Implementa logging rotativo com diferentes níveis e formatação adequada.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import Config

class TimeSyncLogger:
    """Configurador de logging para o sistema de sincronização de tempo."""
    
    def __init__(self):
        """Inicializa o configurador de logging."""
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Configura o sistema de logging com rotação de arquivos."""
        # Garante que o diretório de logs existe
        Config.ensure_log_directory()
        
        # Cria logger principal
        self.logger = logging.getLogger('time_sync')
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
        
        # Remove handlers existentes para evitar duplicação
        self.logger.handlers.clear()
        
        # Configura handler para arquivo com rotação
        file_handler = logging.handlers.RotatingFileHandler(
            filename=Config.LOG_FILE_PATH,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        
        # Configura handler para console
        console_handler = logging.StreamHandler()
        
        # Define formatação detalhada
        detailed_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Define formatação simples para console
        simple_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Aplica formatadores
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        # Adiciona handlers ao logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Log inicial de configuração
        self.logger.info("Sistema de logging inicializado")
        self.logger.info(f"Arquivo de log: {Config.LOG_FILE_PATH}")
        self.logger.info(f"Nível de log: {Config.LOG_LEVEL}")
    
    def get_logger(self) -> logging.Logger:
        """
        Retorna o logger configurado.
        
        Returns:
            logging.Logger: Logger configurado para o sistema
        """
        return self.logger
    
    def log_sync_attempt(self, server: str, system_time: datetime, network_time: Optional[datetime], difference: float):
        """
        Registra uma tentativa de sincronização.
        
        Args:
            server: Servidor NTP utilizado
            system_time: Hora do sistema antes da sincronização
            network_time: Hora obtida do servidor NTP
            difference: Diferença calculada em segundos
        """
        self.logger.info(f"SYNC_ATTEMPT | Servidor: {server} | Sistema: {system_time} | "
                        f"Rede: {network_time} | Diferença: {difference:.2f}s")
    
    def log_sync_success(self, old_time: datetime, new_time: datetime, difference: float):
        """
        Registra uma sincronização bem-sucedida.
        
        Args:
            old_time: Hora anterior do sistema
            new_time: Nova hora definida no sistema
            difference: Diferença corrigida em segundos
        """
        self.logger.info(f"SYNC_SUCCESS | Hora anterior: {old_time} | "
                        f"Nova hora: {new_time} | Correção: {difference:.2f}s")
    
    def log_sync_failure(self, reason: str, error: Optional[Exception] = None):
        """
        Registra uma falha na sincronização.
        
        Args:
            reason: Motivo da falha
            error: Exceção capturada (opcional)
        """
        error_msg = f" | Erro: {str(error)}" if error else ""
        self.logger.error(f"SYNC_FAILURE | Motivo: {reason}{error_msg}")
    
    def log_permission_error(self, operation: str):
        """
        Registra erro de permissão.
        
        Args:
            operation: Operação que falhou por falta de permissão
        """
        self.logger.error(f"PERMISSION_ERROR | Operação: {operation} | "
                         f"Execute como administrador")
    
    def log_network_error(self, server: str, error: Exception):
        """
        Registra erro de rede.
        
        Args:
            server: Servidor que falhou
            error: Exceção de rede capturada
        """
        self.logger.error(f"NETWORK_ERROR | Servidor: {server} | Erro: {str(error)}")
    
    def log_service_event(self, event: str, details: str = ""):
        """
        Registra eventos do serviço.
        
        Args:
            event: Tipo de evento (START, STOP, INSTALL, etc.)
            details: Detalhes adicionais do evento
        """
        details_msg = f" | {details}" if details else ""
        self.logger.info(f"SERVICE_EVENT | {event}{details_msg}")
    
    def log_config_validation(self, valid: bool, errors: list = None):
        """
        Registra resultado da validação de configuração.
        
        Args:
            valid: Se a configuração é válida
            errors: Lista de erros encontrados
        """
        if valid:
            self.logger.info("CONFIG_VALIDATION | Configuração válida")
        else:
            error_list = ", ".join(errors) if errors else "Erros não especificados"
            self.logger.error(f"CONFIG_VALIDATION | Configuração inválida: {error_list}")

# Instância global do logger
_logger_instance = None

def get_logger() -> logging.Logger:
    """
    Retorna a instância global do logger configurado.
    
    Returns:
        logging.Logger: Logger configurado para o sistema
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TimeSyncLogger()
    return _logger_instance.get_logger()

def setup_logging():
    """Inicializa o sistema de logging."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TimeSyncLogger()
    return _logger_instance