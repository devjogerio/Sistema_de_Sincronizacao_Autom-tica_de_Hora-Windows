"""
Utilitários para configuração de logging.
Centraliza a configuração de logs da aplicação.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional


def setup_logger(name: str = 'ntp_monitor', 
                level: int = logging.INFO,
                log_file: Optional[str] = None,
                max_bytes: int = 10 * 1024 * 1024,  # 10MB
                backup_count: int = 5) -> logging.Logger:
    """
    Configura logger para a aplicação.
    
    Args:
        name: Nome do logger
        level: Nível de logging
        log_file: Arquivo de log (opcional)
        max_bytes: Tamanho máximo do arquivo de log
        backup_count: Número de backups a manter
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Remove handlers existentes para evitar duplicação
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    logger.setLevel(level)
    
    # Formato das mensagens
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se especificado)
    if log_file:
        # Cria diretório se não existir
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Handler rotativo para arquivo
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtém logger existente ou cria um novo.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger
    """
    return logging.getLogger(name)


class ContextLogger:
    """
    Logger com contexto adicional.
    Permite adicionar informações contextuais às mensagens.
    """
    
    def __init__(self, logger: logging.Logger, context: dict = None):
        """
        Inicializa logger com contexto.
        
        Args:
            logger: Logger base
            context: Dicionário com informações contextuais
        """
        self.logger = logger
        self.context = context or {}
    
    def _format_message(self, message: str) -> str:
        """
        Formata mensagem com contexto.
        
        Args:
            message: Mensagem original
            
        Returns:
            Mensagem formatada com contexto
        """
        if not self.context:
            return message
        
        context_str = " | ".join([f"{k}={v}" for k, v in self.context.items()])
        return f"[{context_str}] {message}"
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug com contexto."""
        self.logger.debug(self._format_message(message), *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info com contexto."""
        self.logger.info(self._format_message(message), *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning com contexto."""
        self.logger.warning(self._format_message(message), *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error com contexto."""
        self.logger.error(self._format_message(message), *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical com contexto."""
        self.logger.critical(self._format_message(message), *args, **kwargs)
    
    def add_context(self, **kwargs):
        """
        Adiciona informações ao contexto.
        
        Args:
            **kwargs: Pares chave-valor para adicionar ao contexto
        """
        self.context.update(kwargs)
    
    def remove_context(self, *keys):
        """
        Remove informações do contexto.
        
        Args:
            *keys: Chaves a remover do contexto
        """
        for key in keys:
            self.context.pop(key, None)
    
    def clear_context(self):
        """Limpa todo o contexto."""
        self.context.clear()


class TimedLogger:
    """
    Logger para medir tempo de execução.
    Útil para profiling e debugging de performance.
    """
    
    def __init__(self, logger: logging.Logger, operation: str):
        """
        Inicializa logger temporizado.
        
        Args:
            logger: Logger base
            operation: Nome da operação sendo medida
        """
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        """Inicia medição de tempo."""
        self.start_time = datetime.now()
        self.logger.debug(f"Iniciando operação: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza medição de tempo."""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            
            if exc_type:
                self.logger.error(f"Operação '{self.operation}' falhou após {duration:.3f}s: {exc_val}")
            else:
                self.logger.debug(f"Operação '{self.operation}' concluída em {duration:.3f}s")


def log_function_calls(logger: logging.Logger):
    """
    Decorator para logar chamadas de função.
    
    Args:
        logger: Logger a usar
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Chamando função: {func_name}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Função {func_name} executada com sucesso")
                return result
            except Exception as e:
                logger.error(f"Erro na função {func_name}: {e}")
                raise
        
        return wrapper
    return decorator


def log_exceptions(logger: logging.Logger):
    """
    Decorator para logar exceções automaticamente.
    
    Args:
        logger: Logger a usar
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exceção em {func.__name__}: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator