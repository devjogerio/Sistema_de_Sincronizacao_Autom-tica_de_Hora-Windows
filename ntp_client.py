"""
Módulo cliente NTP para obter a hora correta de servidores confiáveis.
Implementa funcionalidades para consulta e validação de tempo via protocolo NTP.
"""

import ntplib
import socket
from datetime import datetime, timezone
from typing import Optional, Tuple
import logging

from config import Config

logger = logging.getLogger(__name__)

class NTPClient:
    """Cliente NTP para sincronização de tempo com servidores confiáveis."""
    
    def __init__(self, server: str = None, timeout: int = None):
        """
        Inicializa o cliente NTP.
        
        Args:
            server: Servidor NTP a ser utilizado (padrão: configuração)
            timeout: Timeout para conexão em segundos (padrão: configuração)
        """
        self.server = server or Config.NTP_SERVER
        self.timeout = timeout or Config.NTP_TIMEOUT
        self.ntp_client = ntplib.NTPClient()
        
    def get_network_time(self) -> Optional[datetime]:
        """
        Obtém a hora atual do servidor NTP.
        
        Returns:
            datetime: Hora atual do servidor NTP ou None em caso de erro
        """
        try:
            logger.info(f"Consultando servidor NTP: {self.server}")
            
            # Realiza consulta NTP
            response = self.ntp_client.request(self.server, timeout=self.timeout)
            
            # Converte timestamp para datetime
            network_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
            
            logger.info(f"Hora obtida do servidor NTP: {network_time}")
            return network_time
            
        except ntplib.NTPException as e:
            logger.error(f"Erro NTP ao consultar servidor {self.server}: {e}")
            return None
            
        except socket.timeout:
            logger.error(f"Timeout ao conectar com servidor NTP {self.server}")
            return None
            
        except socket.gaierror as e:
            logger.error(f"Erro de resolução DNS para servidor {self.server}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Erro inesperado ao consultar servidor NTP: {e}")
            return None
    
    def get_system_time(self) -> datetime:
        """
        Obtém a hora atual do sistema local.
        
        Returns:
            datetime: Hora atual do sistema em UTC
        """
        return datetime.now(timezone.utc)
    
    def calculate_time_difference(self, network_time: datetime, system_time: datetime = None) -> float:
        """
        Calcula a diferença entre a hora da rede e do sistema.
        
        Args:
            network_time: Hora obtida do servidor NTP
            system_time: Hora do sistema (padrão: hora atual)
            
        Returns:
            float: Diferença em segundos (positivo se sistema está atrasado)
        """
        if system_time is None:
            system_time = self.get_system_time()
            
        # Calcula diferença em segundos
        difference = (network_time - system_time).total_seconds()
        
        logger.info(f"Diferença de tempo calculada: {difference:.2f} segundos")
        return difference
    
    def needs_synchronization(self, tolerance_seconds: int = None) -> Tuple[bool, Optional[datetime], float]:
        """
        Verifica se o sistema precisa de sincronização.
        
        Args:
            tolerance_seconds: Tolerância em segundos (padrão: configuração)
            
        Returns:
            Tuple[bool, Optional[datetime], float]: 
                - Se precisa sincronizar
                - Hora correta do NTP (None se erro)
                - Diferença em segundos
        """
        tolerance = tolerance_seconds or Config.TIME_TOLERANCE_SECONDS
        
        # Obtém hora da rede
        network_time = self.get_network_time()
        if network_time is None:
            logger.warning("Não foi possível obter hora da rede para verificação")
            return False, None, 0.0
        
        # Calcula diferença
        system_time = self.get_system_time()
        difference = self.calculate_time_difference(network_time, system_time)
        
        # Verifica se está dentro da tolerância
        needs_sync = abs(difference) > tolerance
        
        if needs_sync:
            logger.warning(f"Sistema fora de sincronização: diferença de {difference:.2f}s (tolerância: {tolerance}s)")
        else:
            logger.info(f"Sistema sincronizado: diferença de {difference:.2f}s (dentro da tolerância de {tolerance}s)")
            
        return needs_sync, network_time, difference
    
    def test_connectivity(self) -> bool:
        """
        Testa a conectividade com o servidor NTP.
        
        Returns:
            bool: True se conseguiu conectar, False caso contrário
        """
        try:
            logger.info(f"Testando conectividade com servidor NTP: {self.server}")
            network_time = self.get_network_time()
            
            if network_time is not None:
                logger.info("Conectividade NTP OK")
                return True
            else:
                logger.error("Falha na conectividade NTP")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar conectividade NTP: {e}")
            return False