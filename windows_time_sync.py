"""
Módulo para sincronização de data e hora do sistema Windows.
Implementa funcionalidades para verificar e atualizar a hora do sistema com privilégios administrativos.
"""

import ctypes
import ctypes.wintypes
import sys
from datetime import datetime, timezone
from typing import Optional, Tuple
import win32api
import win32con
import win32security

from ntp_client import NTPClient
from logger_config import get_logger
from config import Config

logger = get_logger()

class WindowsTimeSync:
    """Classe para sincronização de tempo no Windows."""
    
    def __init__(self):
        """Inicializa o sincronizador de tempo do Windows."""
        self.ntp_client = NTPClient()
        
    def is_admin(self) -> bool:
        """
        Verifica se o script está sendo executado com privilégios administrativos.
        
        Returns:
            bool: True se executando como administrador, False caso contrário
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            logger.error(f"Erro ao verificar privilégios administrativos: {e}")
            return False
    
    def request_admin_privileges(self):
        """
        Solicita privilégios administrativos reiniciando o script como administrador.
        """
        if not self.is_admin():
            logger.warning("Privilégios administrativos necessários. Solicitando elevação...")
            try:
                # Reinicia o script com privilégios administrativos
                ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas", 
                    sys.executable, 
                    " ".join(sys.argv), 
                    None, 
                    1
                )
                sys.exit(0)
            except Exception as e:
                logger.error(f"Falha ao solicitar privilégios administrativos: {e}")
                raise PermissionError("Privilégios administrativos necessários")
    
    def enable_time_privilege(self) -> bool:
        """
        Habilita o privilégio SE_SYSTEMTIME_NAME necessário para alterar a hora do sistema.
        
        Returns:
            bool: True se conseguiu habilitar o privilégio, False caso contrário
        """
        try:
            # Obtém handle do processo atual
            process_handle = win32api.GetCurrentProcess()
            
            # Abre token do processo
            token_handle = win32security.OpenProcessToken(
                process_handle,
                win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
            )
            
            # Obtém LUID do privilégio SE_SYSTEMTIME_NAME
            privilege_luid = win32security.LookupPrivilegeValue(None, "SeSystemtimePrivilege")
            
            # Habilita o privilégio
            win32security.AdjustTokenPrivileges(
                token_handle,
                False,
                [(privilege_luid, win32con.SE_PRIVILEGE_ENABLED)]
            )
            
            logger.info("Privilégio SE_SYSTEMTIME_NAME habilitado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Falha ao habilitar privilégio de alteração de tempo: {e}")
            return False
    
    def set_system_time(self, new_time: datetime) -> bool:
        """
        Define a nova hora do sistema Windows.
        
        Args:
            new_time: Nova data/hora a ser definida
            
        Returns:
            bool: True se conseguiu alterar a hora, False caso contrário
        """
        try:
            # Converte para hora local
            local_time = new_time.astimezone()
            
            # Estrutura SYSTEMTIME do Windows
            class SYSTEMTIME(ctypes.Structure):
                _fields_ = [
                    ('wYear', ctypes.wintypes.WORD),
                    ('wMonth', ctypes.wintypes.WORD),
                    ('wDayOfWeek', ctypes.wintypes.WORD),
                    ('wDay', ctypes.wintypes.WORD),
                    ('wHour', ctypes.wintypes.WORD),
                    ('wMinute', ctypes.wintypes.WORD),
                    ('wSecond', ctypes.wintypes.WORD),
                    ('wMilliseconds', ctypes.wintypes.WORD),
                ]
            
            # Preenche estrutura com nova hora
            system_time = SYSTEMTIME()
            system_time.wYear = local_time.year
            system_time.wMonth = local_time.month
            system_time.wDayOfWeek = local_time.weekday()
            system_time.wDay = local_time.day
            system_time.wHour = local_time.hour
            system_time.wMinute = local_time.minute
            system_time.wSecond = local_time.second
            system_time.wMilliseconds = local_time.microsecond // 1000
            
            # Chama API do Windows para definir hora do sistema
            result = ctypes.windll.kernel32.SetLocalTime(ctypes.byref(system_time))
            
            if result:
                logger.info(f"Hora do sistema alterada com sucesso para: {local_time}")
                return True
            else:
                error_code = ctypes.windll.kernel32.GetLastError()
                logger.error(f"Falha ao alterar hora do sistema. Código de erro: {error_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao definir hora do sistema: {e}")
            return False
    
    def sync_system_time(self) -> Tuple[bool, Optional[str]]:
        """
        Executa sincronização completa da hora do sistema.
        
        Returns:
            Tuple[bool, Optional[str]]: 
                - True se sincronização foi bem-sucedida
                - Mensagem de erro em caso de falha
        """
        try:
            # Verifica privilégios administrativos
            if not self.is_admin():
                error_msg = "Privilégios administrativos necessários"
                logger.error(error_msg)
                return False, error_msg
            
            # Habilita privilégio de alteração de tempo
            if not self.enable_time_privilege():
                error_msg = "Falha ao habilitar privilégio de alteração de tempo"
                logger.error(error_msg)
                return False, error_msg
            
            # Verifica se sincronização é necessária
            needs_sync, network_time, difference = self.ntp_client.needs_synchronization()
            
            if not needs_sync:
                logger.info("Sistema já está sincronizado")
                return True, None
            
            if network_time is None:
                error_msg = "Não foi possível obter hora da rede"
                logger.error(error_msg)
                return False, error_msg
            
            # Registra tentativa de sincronização
            system_time = self.ntp_client.get_system_time()
            logger.info(f"Iniciando sincronização - Diferença: {difference:.2f}s")
            
            # Altera hora do sistema
            if self.set_system_time(network_time):
                logger.info(f"Sincronização concluída com sucesso")
                return True, None
            else:
                error_msg = "Falha ao alterar hora do sistema"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Erro durante sincronização: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def check_sync_status(self) -> dict:
        """
        Verifica o status atual de sincronização sem fazer alterações.
        
        Returns:
            dict: Informações sobre o status de sincronização
        """
        try:
            # Testa conectividade NTP
            connectivity = self.ntp_client.test_connectivity()
            
            # Verifica se sincronização é necessária
            needs_sync, network_time, difference = self.ntp_client.needs_synchronization()
            
            # Obtém hora do sistema
            system_time = self.ntp_client.get_system_time()
            
            status = {
                'system_time': system_time,
                'network_time': network_time,
                'difference_seconds': difference,
                'needs_synchronization': needs_sync,
                'ntp_connectivity': connectivity,
                'is_admin': self.is_admin(),
                'tolerance_seconds': Config.TIME_TOLERANCE_SECONDS,
                'ntp_server': Config.NTP_SERVER
            }
            
            logger.info(f"Status de sincronização: {status}")
            return status
            
        except Exception as e:
            logger.error(f"Erro ao verificar status de sincronização: {e}")
            return {
                'error': str(e),
                'system_time': datetime.now(timezone.utc),
                'needs_synchronization': False,
                'ntp_connectivity': False,
                'is_admin': self.is_admin()
            }