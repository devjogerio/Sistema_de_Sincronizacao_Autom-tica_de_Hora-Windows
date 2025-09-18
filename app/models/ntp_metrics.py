"""
Modelo de dados para métricas NTP.
Define a estrutura de dados para armazenar informações de servidores NTP.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NTPMetrics:
    """
    Classe para armazenar métricas de um servidor NTP.
    
    Attributes:
        server: Endereço do servidor NTP
        timestamp: Momento da coleta da métrica
        response_time: Tempo de resposta em segundos
        offset: Diferença de tempo em segundos
        delay: Atraso de rede em segundos
        precision: Precisão do servidor
        stratum: Nível do servidor na hierarquia NTP
        is_available: Status de disponibilidade do servidor
        error_message: Mensagem de erro, se houver
    """
    server: str
    timestamp: datetime
    response_time: float
    offset: float
    delay: float
    precision: float
    stratum: int
    is_available: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """
        Converte a métrica para dicionário.
        
        Returns:
            dict: Representação em dicionário da métrica
        """
        return {
            'server': self.server,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'response_time': self.response_time,
            'offset': self.offset,
            'delay': self.delay,
            'precision': self.precision,
            'stratum': self.stratum,
            'is_available': self.is_available,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NTPMetrics':
        """
        Cria uma instância a partir de um dicionário.
        
        Args:
            data: Dicionário com os dados da métrica
            
        Returns:
            NTPMetrics: Nova instância da métrica
        """
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)
    
    def is_healthy(self, max_offset: float = 1.0, max_response_time: float = 5.0) -> bool:
        """
        Verifica se o servidor está saudável baseado nos thresholds.
        
        Args:
            max_offset: Offset máximo aceitável em segundos
            max_response_time: Tempo de resposta máximo aceitável em segundos
            
        Returns:
            bool: True se o servidor está saudável
        """
        if not self.is_available:
            return False
            
        return (abs(self.offset) <= max_offset and 
                self.response_time <= max_response_time and
                self.stratum > 0)