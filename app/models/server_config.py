"""
Modelo de configuração de servidores NTP.
Define a estrutura de dados para configuração de servidores.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ServerConfig:
    """
    Configuração de um servidor NTP.
    
    Attributes:
        name: Nome identificador do servidor
        address: Endereço IP ou hostname do servidor
        timeout: Timeout para conexão em segundos
        priority: Prioridade do servidor (1=alta, 2=média, 3=baixa)
        enabled: Se o servidor está habilitado para monitoramento
        description: Descrição opcional do servidor
    """
    name: str
    address: str
    timeout: int = 5
    priority: int = 1
    enabled: bool = True
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a configuração para dicionário.
        
        Returns:
            Dict[str, Any]: Representação em dicionário da configuração
        """
        return {
            'name': self.name,
            'address': self.address,
            'timeout': self.timeout,
            'priority': self.priority,
            'enabled': self.enabled,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        """
        Cria uma instância a partir de um dicionário.
        
        Args:
            data: Dicionário com os dados da configuração
            
        Returns:
            ServerConfig: Nova instância da configuração
        """
        return cls(**data)
    
    def validate(self) -> bool:
        """
        Valida se a configuração do servidor está correta.
        
        Returns:
            bool: True se a configuração é válida
        """
        if not self.name or not self.address:
            return False
            
        if self.timeout <= 0 or self.timeout > 60:
            return False
            
        if self.priority not in [1, 2, 3]:
            return False
            
        return True
    
    def get_priority_text(self) -> str:
        """
        Retorna o texto da prioridade.
        
        Returns:
            str: Texto da prioridade
        """
        priority_map = {
            1: "Alta",
            2: "Média", 
            3: "Baixa"
        }
        return priority_map.get(self.priority, "Desconhecida")