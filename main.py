"""
Script principal para sincronização automática de data e hora do Windows.
Implementa execução contínua, tratamento de erros e validações de segurança.
"""

import sys
import time
import signal
import argparse
from datetime import datetime
from typing import Optional
import schedule

from config import Config
from logger_config import setup_logging, get_logger
from ntp_client import NTPClient
from windows_time_sync import WindowsTimeSync

# Configuração global
logger = None
time_sync = None
running = True

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

def validate_environment():
    """
    Valida o ambiente de execução e configurações.
    
    Raises:
        SystemExit: Se validação falhar
    """
    try:
        # Valida configurações
        Config.validate_config()
        logger.info("Configurações validadas com sucesso")
        
        # Testa conectividade NTP
        ntp_client = NTPClient()
        if not ntp_client.test_connectivity():
            logger.warning("Falha na conectividade NTP inicial - continuando execução")
        
        # Verifica privilégios administrativos
        time_sync = WindowsTimeSync()
        if not time_sync.is_admin():
            logger.error("Privilégios administrativos necessários")
            logger.error("Execute o script como administrador")
            sys.exit(1)
        
        logger.info("Ambiente validado com sucesso")
        
    except ValueError as e:
        logger.error(f"Erro de configuração: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro na validação do ambiente: {e}")
        sys.exit(1)

def perform_sync():
    """
    Executa uma sincronização de tempo com tratamento completo de erros.
    """
    try:
        logger.info("Iniciando ciclo de sincronização")
        
        # Verifica status atual
        status = time_sync.check_sync_status()
        
        if 'error' in status:
            logger.error(f"Erro ao verificar status: {status['error']}")
            return
        
        # Log do status atual
        logger.info(f"Status atual - Sistema: {status['system_time']}, "
                   f"Rede: {status['network_time']}, "
                   f"Diferença: {status['difference_seconds']:.2f}s")
        
        # Verifica se sincronização é necessária
        if not status['needs_synchronization']:
            logger.info("Sistema já está sincronizado")
            return
        
        if not status['ntp_connectivity']:
            logger.warning("Sem conectividade NTP - pulando sincronização")
            return
        
        # Executa sincronização
        success, error_msg = time_sync.sync_system_time()
        
        if success:
            logger.info("Sincronização concluída com sucesso")
        else:
            logger.error(f"Falha na sincronização: {error_msg}")
            
    except Exception as e:
        logger.error(f"Erro durante sincronização: {e}")

def run_once():
    """
    Executa uma única sincronização e sai.
    """
    logger.info("Modo execução única")
    perform_sync()
    logger.info("Execução única concluída")

def run_continuous():
    """
    Executa sincronização contínua baseada no intervalo configurado.
    """
    global running
    
    logger.info(f"Iniciando execução contínua - Intervalo: {Config.SYNC_INTERVAL_MINUTES} minutos")
    
    # Agenda sincronização periódica
    schedule.every(Config.SYNC_INTERVAL_MINUTES).minutes.do(perform_sync)
    
    # Executa sincronização inicial
    perform_sync()
    
    # Loop principal
    while running:
        try:
            schedule.run_pending()
            time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("Interrupção por teclado recebida")
            break
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            time.sleep(5)  # Pausa antes de tentar novamente
    
    logger.info("Execução contínua finalizada")

def run_status_check():
    """
    Executa verificação de status sem fazer sincronização.
    """
    logger.info("Verificando status de sincronização")
    
    try:
        status = time_sync.check_sync_status()
        
        print("\n=== STATUS DE SINCRONIZAÇÃO ===")
        print(f"Hora do Sistema: {status.get('system_time', 'N/A')}")
        print(f"Hora da Rede: {status.get('network_time', 'N/A')}")
        print(f"Diferença: {status.get('difference_seconds', 0):.2f} segundos")
        print(f"Precisa Sincronizar: {'Sim' if status.get('needs_synchronization', False) else 'Não'}")
        print(f"Conectividade NTP: {'OK' if status.get('ntp_connectivity', False) else 'Falha'}")
        print(f"Privilégios Admin: {'Sim' if status.get('is_admin', False) else 'Não'}")
        print(f"Tolerância: {status.get('tolerance_seconds', 0)} segundos")
        print(f"Servidor NTP: {status.get('ntp_server', 'N/A')}")
        
        if 'error' in status:
            print(f"Erro: {status['error']}")
        
        print("===============================\n")
        
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        print(f"Erro ao verificar status: {e}")

def main():
    """
    Função principal do script.
    """
    global logger, time_sync
    
    # Configura argumentos da linha de comando
    parser = argparse.ArgumentParser(description='Sincronização automática de hora do Windows')
    parser.add_argument('--once', action='store_true', 
                       help='Executa sincronização uma vez e sai')
    parser.add_argument('--status', action='store_true',
                       help='Verifica status de sincronização sem alterar')
    parser.add_argument('--service', action='store_true',
                       help='Executa em modo serviço (contínuo)')
    
    args = parser.parse_args()
    
    try:
        # Inicializa logging
        setup_logging()
        logger = get_logger()
        
        logger.info("=== INICIANDO SISTEMA DE SINCRONIZAÇÃO DE TEMPO ===")
        logger.info(f"Versão Python: {sys.version}")
        logger.info(f"Argumentos: {sys.argv}")
        
        # Inicializa sincronizador
        time_sync = WindowsTimeSync()
        
        # Configura manipuladores de sinal
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Valida ambiente
        validate_environment()
        
        # Executa modo apropriado
        if args.status:
            run_status_check()
        elif args.once:
            run_once()
        else:
            run_continuous()
            
    except KeyboardInterrupt:
        logger.info("Execução interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)
    finally:
        logger.info("=== FINALIZANDO SISTEMA DE SINCRONIZAÇÃO ===")

if __name__ == "__main__":
    main()