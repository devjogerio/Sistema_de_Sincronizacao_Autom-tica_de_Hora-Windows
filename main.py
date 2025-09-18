#!/usr/bin/env python3
"""
NTP Monitor - Sistema de Monitoramento de Servidores NTP
Arquivo principal da aplicação com arquitetura MVC.

Este arquivo serve como ponto de entrada da aplicação,
inicializando todos os componentes necessários.
"""

import sys
import os
import logging
from pathlib import Path

# Adiciona o diretório da aplicação ao path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.controllers.dashboard_controller import DashboardController
from app.utils.logger import setup_logger

# Configuração global
running = True


def setup_application():
    """
    Configura a aplicação antes da execução.
    
    Returns:
        True se configuração foi bem-sucedida, False caso contrário
    """
    try:
        # Cria diretórios necessários
        directories = [
            'logs',
            'data',
            'config',
            'exports'
        ]
        
        for directory in directories:
            dir_path = app_dir / directory
            dir_path.mkdir(exist_ok=True)
        
        # Configura logging
        log_file = app_dir / 'logs' / 'ntp_monitor.log'
        setup_logger(
            name='ntp_monitor',
            level=logging.INFO,
            log_file=str(log_file)
        )
        
        logger = logging.getLogger('ntp_monitor')
        logger.info("Aplicação NTP Monitor iniciando...")
        logger.info(f"Diretório da aplicação: {app_dir}")
        
        return True
        
    except Exception as e:
        print(f"Erro ao configurar aplicação: {e}")
        return False





def signal_handler(signum, frame):
    """
    Manipulador de sinais para parada graceful do serviço.
    
    Args:
        signum: Número do sinal recebido
        frame: Frame atual de execução
    """
    global running
    logger.info(f"Sinal {signum} recebido. Iniciando parada graceful...")
    running = False

def main():
    """
    Função principal da aplicação.
    Inicializa e executa o dashboard NTP Monitor.
    """
    try:
        # Configura aplicação
        if not setup_application():
            sys.exit(1)
        
        logger = logging.getLogger('ntp_monitor')
        
        # Verifica dependências
        try:
            import tkinter
            import sqlite3
            import ntplib
        except ImportError as e:
            logger.error(f"Dependência não encontrada: {e}")
            print(f"Erro: Dependência não encontrada - {e}")
            print("Instale as dependências necessárias e tente novamente.")
            sys.exit(1)
        
        # Cria e executa controlador principal
        logger.info("Inicializando controlador do dashboard...")
        controller = DashboardController()
        
        # Executa aplicação
        logger.info("Executando aplicação...")
        controller.run()
        
        logger.info("Aplicação finalizada normalmente")
        
    except KeyboardInterrupt:
        logger = logging.getLogger('ntp_monitor')
        logger.info("Aplicação interrompida pelo usuário (Ctrl+C)")
        print("\nAplicação interrompida pelo usuário.")
        
    except Exception as e:
        logger = logging.getLogger('ntp_monitor')
        logger.error(f"Erro fatal na aplicação: {e}", exc_info=True)
        print(f"Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()