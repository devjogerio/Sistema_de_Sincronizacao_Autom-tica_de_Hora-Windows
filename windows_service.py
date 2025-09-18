"""
Módulo para execução como serviço Windows.
Implementa instalação, desinstalação e execução do sincronizador como serviço do sistema.
"""

import sys
import os
import time
import servicemanager
import win32event
import win32service
import win32serviceutil

from config import Config
from logger_config import setup_logging, get_logger
from windows_time_sync import WindowsTimeSync

class WindowsTimeSyncService(win32serviceutil.ServiceFramework):
    """Serviço Windows para sincronização automática de tempo."""
    
    _svc_name_ = Config.SERVICE_NAME
    _svc_display_name_ = Config.SERVICE_DISPLAY_NAME
    _svc_description_ = Config.SERVICE_DESCRIPTION
    
    def __init__(self, args):
        """
        Inicializa o serviço Windows.
        
        Args:
            args: Argumentos do serviço
        """
        win32serviceutil.ServiceFramework.__init__(self, args)
        
        # Evento para parada do serviço
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        
        # Inicializa componentes
        self.logger = None
        self.time_sync = None
        self.running = False
        
    def SvcStop(self):
        """Para o serviço."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.running = False
        
        if self.logger:
            self.logger.info("Serviço de sincronização parado")
    
    def SvcDoRun(self):
        """Executa o serviço principal."""
        try:
            # Inicializa logging
            setup_logging()
            self.logger = get_logger()
            
            # Log de início do serviço
            self.logger.info("=== SERVIÇO DE SINCRONIZAÇÃO INICIADO ===")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            
            # Inicializa sincronizador
            self.time_sync = WindowsTimeSync()
            self.running = True
            
            # Valida ambiente
            self._validate_service_environment()
            
            # Loop principal do serviço
            self._service_main_loop()
            
        except Exception as e:
            error_msg = f"Erro fatal no serviço: {e}"
            if self.logger:
                self.logger.error(error_msg)
            
            servicemanager.LogErrorMsg(error_msg)
            self.SvcStop()
    
    def _validate_service_environment(self):
        """
        Valida o ambiente de execução do serviço.
        
        Raises:
            Exception: Se validação falhar
        """
        try:
            # Valida configurações
            Config.validate_config()
            self.logger.info("Configurações do serviço validadas")
            
            # Verifica privilégios administrativos
            if not self.time_sync.is_admin():
                raise Exception("Serviço deve ser executado com privilégios administrativos")
            
            # Testa conectividade NTP inicial
            if not self.time_sync.ntp_client.test_connectivity():
                self.logger.warning("Conectividade NTP inicial falhou - continuando execução")
            
            self.logger.info("Ambiente do serviço validado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Falha na validação do ambiente do serviço: {e}")
            raise
    
    def _service_main_loop(self):
        """Loop principal de execução do serviço."""
        last_sync_time = 0
        sync_interval_seconds = Config.SYNC_INTERVAL_MINUTES * 60
        
        self.logger.info(f"Iniciando loop principal - Intervalo: {Config.SYNC_INTERVAL_MINUTES} minutos")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Verifica se é hora de sincronizar
                if current_time - last_sync_time >= sync_interval_seconds:
                    self._perform_service_sync()
                    last_sync_time = current_time
                
                # Verifica se deve parar o serviço
                if win32event.WaitForSingleObject(self.hWaitStop, 1000) == win32event.WAIT_OBJECT_0:
                    break
                    
            except Exception as e:
                self.logger.error(f"Erro no loop principal do serviço: {e}")
                time.sleep(5)  # Pausa antes de tentar novamente
        
        self.logger.info("Loop principal do serviço finalizado")
    
    def _perform_service_sync(self):
        """Executa sincronização no contexto do serviço."""
        try:
            self.logger.info("Iniciando sincronização do serviço")
            
            # Verifica status
            status = self.time_sync.check_sync_status()
            
            if 'error' in status:
                self.logger.error(f"Erro ao verificar status: {status['error']}")
                return
            
            # Log do status
            self.logger.info(f"Status - Diferença: {status['difference_seconds']:.2f}s, "
                           f"Precisa sync: {status['needs_synchronization']}")
            
            # Executa sincronização se necessário
            if status['needs_synchronization'] and status['ntp_connectivity']:
                success, error_msg = self.time_sync.sync_system_time()
                
                if success:
                    self.logger.info("Sincronização do serviço concluída com sucesso")
                    servicemanager.LogInfoMsg(f"Hora sincronizada - Diferença corrigida: {status['difference_seconds']:.2f}s")
                else:
                    self.logger.error(f"Falha na sincronização do serviço: {error_msg}")
                    servicemanager.LogErrorMsg(f"Falha na sincronização: {error_msg}")
            else:
                self.logger.info("Sincronização não necessária ou sem conectividade")
                
        except Exception as e:
            self.logger.error(f"Erro durante sincronização do serviço: {e}")
            servicemanager.LogErrorMsg(f"Erro na sincronização: {e}")

def install_service():
    """
    Instala o serviço Windows.
    """
    try:
        print("Instalando serviço de sincronização de tempo...")
        
        # Instala o serviço
        win32serviceutil.InstallService(
            WindowsTimeSyncService,
            Config.SERVICE_NAME,
            Config.SERVICE_DISPLAY_NAME,
            description=Config.SERVICE_DESCRIPTION,
            startType=win32service.SERVICE_AUTO_START
        )
        
        print(f"Serviço '{Config.SERVICE_DISPLAY_NAME}' instalado com sucesso!")
        print(f"Nome do serviço: {Config.SERVICE_NAME}")
        print("O serviço foi configurado para iniciar automaticamente.")
        print("Use 'net start " + Config.SERVICE_NAME + "' para iniciar o serviço.")
        
    except Exception as e:
        print(f"Erro ao instalar serviço: {e}")
        return False
    
    return True

def uninstall_service():
    """
    Desinstala o serviço Windows.
    """
    try:
        print("Desinstalando serviço de sincronização de tempo...")
        
        # Para o serviço se estiver rodando
        try:
            win32serviceutil.StopService(Config.SERVICE_NAME)
            print("Serviço parado.")
        except:
            pass  # Serviço pode não estar rodando
        
        # Remove o serviço
        win32serviceutil.RemoveService(Config.SERVICE_NAME)
        
        print(f"Serviço '{Config.SERVICE_DISPLAY_NAME}' desinstalado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao desinstalar serviço: {e}")
        return False
    
    return True

def start_service():
    """Inicia o serviço Windows."""
    try:
        print("Iniciando serviço...")
        win32serviceutil.StartService(Config.SERVICE_NAME)
        print("Serviço iniciado com sucesso!")
    except Exception as e:
        print(f"Erro ao iniciar serviço: {e}")

def stop_service():
    """Para o serviço Windows."""
    try:
        print("Parando serviço...")
        win32serviceutil.StopService(Config.SERVICE_NAME)
        print("Serviço parado com sucesso!")
    except Exception as e:
        print(f"Erro ao parar serviço: {e}")

def main():
    """Função principal para gerenciamento do serviço."""
    if len(sys.argv) == 1:
        # Executa como serviço
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(WindowsTimeSyncService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Gerenciamento do serviço via linha de comando
        command = sys.argv[1].lower()
        
        if command == 'install':
            install_service()
        elif command == 'uninstall' or command == 'remove':
            uninstall_service()
        elif command == 'start':
            start_service()
        elif command == 'stop':
            stop_service()
        elif command == 'restart':
            stop_service()
            time.sleep(2)
            start_service()
        else:
            print("Uso: python windows_service.py [install|uninstall|start|stop|restart]")
            print("Sem argumentos: executa como serviço")

if __name__ == '__main__':
    main()