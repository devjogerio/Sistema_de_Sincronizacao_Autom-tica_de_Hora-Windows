"""
Serviço para operações NTP.
Centraliza a lógica de negócio relacionada ao monitoramento NTP.
"""

import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.ntp_metrics import NTPMetrics
from ..models.server_config import ServerConfig
from ntp_client import NTPClient

logger = logging.getLogger(__name__)


class NTPService:
    """
    Serviço para operações de monitoramento NTP.
    
    Centraliza toda a lógica de negócio relacionada ao NTP,
    incluindo coleta de métricas e análise de servidores.
    """
    
    def __init__(self):
        """Inicializa o serviço NTP."""
        self.ntp_client = NTPClient()
    
    def check_server(self, server_config: ServerConfig) -> NTPMetrics:
        """
        Verifica um servidor NTP específico e coleta métricas.
        
        Args:
            server_config: Configuração do servidor a ser verificado
            
        Returns:
            NTPMetrics: Métricas coletadas do servidor
        """
        start_time = time.time()
        
        try:
            # Cria cliente NTP para o servidor específico
            ntp_client = NTPClient(server=server_config.address, timeout=server_config.timeout)
            
            # Obtém hora do servidor
            network_time = ntp_client.get_network_time()
            response_time = time.time() - start_time
            
            if network_time is None:
                return NTPMetrics(
                    server=server_config.address,
                    timestamp=datetime.now(timezone.utc),
                    response_time=response_time,
                    offset=0.0,
                    delay=0.0,
                    precision=0.0,
                    stratum=0,
                    is_available=False,
                    error_message="Falha ao obter hora do servidor"
                )
            
            # Calcula métricas
            local_time = datetime.now(timezone.utc)
            offset = (network_time - local_time).total_seconds()
            
            # Obtém informações adicionais do servidor
            server_info = ntp_client.get_server_info()
            
            return NTPMetrics(
                server=server_config.address,
                timestamp=local_time,
                response_time=response_time,
                offset=offset,
                delay=server_info.get('delay', 0.0),
                precision=server_info.get('precision', 0.0),
                stratum=server_info.get('stratum', 0),
                is_available=True
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Erro ao verificar servidor {server_config.address}: {e}")
            
            return NTPMetrics(
                server=server_config.address,
                timestamp=datetime.now(timezone.utc),
                response_time=response_time,
                offset=0.0,
                delay=0.0,
                precision=0.0,
                stratum=0,
                is_available=False,
                error_message=str(e)
            )
    
    def check_multiple_servers(self, server_configs: List[ServerConfig], 
                             max_workers: int = 10) -> List[NTPMetrics]:
        """
        Verifica múltiplos servidores NTP simultaneamente.
        
        Args:
            server_configs: Lista de configurações de servidores
            max_workers: Número máximo de workers paralelos
            
        Returns:
            List[NTPMetrics]: Lista com métricas de todos os servidores
        """
        if not server_configs:
            logger.warning("Nenhum servidor fornecido para verificação")
            return []
        
        results = []
        actual_max_workers = min(len(server_configs), max_workers)
        
        with ThreadPoolExecutor(max_workers=actual_max_workers) as executor:
            # Submete tarefas para verificação paralela
            future_to_server = {
                executor.submit(self.check_server, server_config): server_config
                for server_config in server_configs
            }
            
            # Coleta resultados conforme completam
            for future in as_completed(future_to_server):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    server_config = future_to_server[future]
                    logger.error(f"Erro na verificação paralela do servidor {server_config.name}: {e}")
                    
                    # Adiciona resultado de erro
                    error_metric = NTPMetrics(
                        server=server_config.address,
                        timestamp=datetime.now(timezone.utc),
                        response_time=0.0,
                        offset=0.0,
                        delay=0.0,
                        precision=0.0,
                        stratum=0,
                        is_available=False,
                        error_message=f"Erro na execução paralela: {str(e)}"
                    )
                    results.append(error_metric)
        
        logger.info(f"Verificação completa: {len(results)} servidores processados")
        return results
    
    def analyze_server_health(self, metrics: List[NTPMetrics]) -> Dict[str, any]:
        """
        Analisa a saúde geral dos servidores baseado nas métricas.
        
        Args:
            metrics: Lista de métricas dos servidores
            
        Returns:
            Dict: Análise da saúde dos servidores
        """
        if not metrics:
            return {
                'total_servers': 0,
                'available_servers': 0,
                'availability_percentage': 0.0,
                'average_response_time': 0.0,
                'average_offset': 0.0,
                'healthy_servers': 0,
                'health_percentage': 0.0
            }
        
        available_metrics = [m for m in metrics if m.is_available]
        healthy_metrics = [m for m in available_metrics if m.is_healthy()]
        
        avg_response_time = 0.0
        avg_offset = 0.0
        
        if available_metrics:
            avg_response_time = sum(m.response_time for m in available_metrics) / len(available_metrics)
            avg_offset = sum(abs(m.offset) for m in available_metrics) / len(available_metrics)
        
        return {
            'total_servers': len(metrics),
            'available_servers': len(available_metrics),
            'availability_percentage': (len(available_metrics) / len(metrics)) * 100,
            'average_response_time': avg_response_time,
            'average_offset': avg_offset,
            'healthy_servers': len(healthy_metrics),
            'health_percentage': (len(healthy_metrics) / len(metrics)) * 100 if metrics else 0.0
        }
    
    def get_best_server(self, metrics: List[NTPMetrics]) -> Optional[NTPMetrics]:
        """
        Identifica o melhor servidor baseado nas métricas.
        
        Args:
            metrics: Lista de métricas dos servidores
            
        Returns:
            Optional[NTPMetrics]: Métrica do melhor servidor ou None
        """
        available_metrics = [m for m in metrics if m.is_available and m.is_healthy()]
        
        if not available_metrics:
            return None
        
        # Ordena por stratum (menor é melhor) e depois por response_time
        best_server = min(available_metrics, 
                         key=lambda m: (m.stratum, m.response_time, abs(m.offset)))
        
        return best_server