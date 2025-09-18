"""
Controlador principal para operações NTP.
Coordena as operações entre serviços e views.
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Callable

from ..services.ntp_service import NTPService
from ..services.config_service import ConfigService
from ..services.database_service import DatabaseService
from ..services.email_service import EmailService
from ..models.ntp_metrics import NTPMetrics

logger = logging.getLogger(__name__)


class NTPController:
    """
    Controlador principal para operações NTP.
    
    Coordena o monitoramento contínuo, coleta de métricas,
    armazenamento de dados e envio de alertas.
    """
    
    def __init__(self):
        """Inicializa o controlador NTP."""
        self.ntp_service = NTPService()
        self.config_service = ConfigService()
        self.database_service = DatabaseService()
        self.email_service = EmailService()
        
        self._monitoring_thread = None
        self._is_monitoring = False
        self._callbacks = {
            'metrics_updated': [],
            'alert_triggered': [],
            'status_changed': []
        }
        
        # Configurações de monitoramento
        self.monitoring_config = self.config_service.get_monitoring_config()
        self.alert_config = self.config_service.get_alert_config()
        
        logger.info("Controlador NTP inicializado")
    
    def start_monitoring(self) -> bool:
        """
        Inicia o monitoramento contínuo dos servidores NTP.
        
        Returns:
            bool: True se iniciou com sucesso, False caso contrário
        """
        if self._is_monitoring:
            logger.warning("Monitoramento já está em execução")
            return False
        
        try:
            self._is_monitoring = True
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="NTPMonitoringThread"
            )
            self._monitoring_thread.start()
            
            logger.info("Monitoramento NTP iniciado")
            self._notify_callbacks('status_changed', {'status': 'started'})
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento: {e}")
            self._is_monitoring = False
            return False
    
    def stop_monitoring(self):
        """Para o monitoramento contínuo."""
        if not self._is_monitoring:
            logger.warning("Monitoramento não está em execução")
            return
        
        self._is_monitoring = False
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=10)
        
        logger.info("Monitoramento NTP parado")
        self._notify_callbacks('status_changed', {'status': 'stopped'})
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento."""
        logger.info("Loop de monitoramento iniciado")
        
        while self._is_monitoring:
            try:
                # Coleta métricas de todos os servidores
                metrics = self.collect_metrics()
                
                if metrics:
                    # Armazena métricas no banco de dados
                    self.database_service.store_metrics(metrics)
                    
                    # Verifica alertas
                    self._check_alerts(metrics)
                    
                    # Notifica callbacks
                    self._notify_callbacks('metrics_updated', {'metrics': metrics})
                
                # Aguarda próximo ciclo
                time.sleep(self.monitoring_config.check_interval)
                
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(5)  # Aguarda antes de tentar novamente
        
        logger.info("Loop de monitoramento finalizado")
    
    def collect_metrics(self) -> List[NTPMetrics]:
        """
        Coleta métricas de todos os servidores habilitados.
        
        Returns:
            List[NTPMetrics]: Lista com métricas coletadas
        """
        try:
            servers = self.config_service.get_enabled_servers()
            
            if not servers:
                logger.warning("Nenhum servidor habilitado para monitoramento")
                return []
            
            logger.debug(f"Coletando métricas de {len(servers)} servidores")
            
            metrics = self.ntp_service.check_multiple_servers(
                servers, 
                max_workers=self.monitoring_config.max_workers
            )
            
            logger.info(f"Métricas coletadas: {len(metrics)} servidores processados")
            return metrics
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas: {e}")
            return []
    
    def get_latest_metrics(self) -> List[NTPMetrics]:
        """
        Obtém as métricas mais recentes do banco de dados.
        
        Returns:
            List[NTPMetrics]: Lista com métricas mais recentes
        """
        try:
            return self.database_service.get_latest_metrics()
        except Exception as e:
            logger.error(f"Erro ao obter métricas mais recentes: {e}")
            return []
    
    def get_historical_metrics(self, hours: int = 24) -> List[NTPMetrics]:
        """
        Obtém métricas históricas do banco de dados.
        
        Args:
            hours: Número de horas de histórico
            
        Returns:
            List[NTPMetrics]: Lista com métricas históricas
        """
        try:
            return self.database_service.get_historical_metrics(hours)
        except Exception as e:
            logger.error(f"Erro ao obter métricas históricas: {e}")
            return []
    
    def get_server_statistics(self, server_address: str, hours: int = 24) -> Dict:
        """
        Obtém estatísticas de um servidor específico.
        
        Args:
            server_address: Endereço do servidor
            hours: Período em horas para análise
            
        Returns:
            Dict: Estatísticas do servidor
        """
        try:
            return self.database_service.get_server_statistics(server_address, hours)
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do servidor {server_address}: {e}")
            return {}
    
    def _check_alerts(self, metrics: List[NTPMetrics]):
        """
        Verifica se alguma métrica disparou alertas.
        
        Args:
            metrics: Lista de métricas para verificação
        """
        if not self.alert_config.email_enabled and not self.alert_config.console_enabled:
            return
        
        alerts = []
        
        for metric in metrics:
            # Verifica disponibilidade
            if not metric.is_available:
                alerts.append({
                    'type': 'availability',
                    'server': metric.server,
                    'message': f"Servidor {metric.server} indisponível",
                    'severity': 'high',
                    'metric': metric
                })
            
            # Verifica offset
            elif abs(metric.offset) > self.alert_config.offset_threshold:
                alerts.append({
                    'type': 'offset',
                    'server': metric.server,
                    'message': f"Offset alto no servidor {metric.server}: {metric.offset:.3f}s",
                    'severity': 'medium',
                    'metric': metric
                })
            
            # Verifica tempo de resposta
            elif metric.response_time > self.alert_config.response_time_threshold:
                alerts.append({
                    'type': 'response_time',
                    'server': metric.server,
                    'message': f"Tempo de resposta alto no servidor {metric.server}: {metric.response_time:.3f}s",
                    'severity': 'low',
                    'metric': metric
                })
        
        # Processa alertas
        for alert in alerts:
            self._process_alert(alert)
    
    def _process_alert(self, alert: Dict):
        """
        Processa um alerta específico.
        
        Args:
            alert: Dados do alerta
        """
        try:
            # Log do alerta
            if self.alert_config.console_enabled:
                logger.warning(f"ALERTA [{alert['severity'].upper()}]: {alert['message']}")
            
            # Envio por email
            if self.alert_config.email_enabled:
                self.email_service.send_alert_email(alert)
            
            # Notifica callbacks
            self._notify_callbacks('alert_triggered', alert)
            
        except Exception as e:
            logger.error(f"Erro ao processar alerta: {e}")
    
    def add_callback(self, event: str, callback: Callable):
        """
        Adiciona callback para eventos do controlador.
        
        Args:
            event: Tipo de evento ('metrics_updated', 'alert_triggered', 'status_changed')
            callback: Função callback
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)
        else:
            logger.warning(f"Evento desconhecido: {event}")
    
    def remove_callback(self, event: str, callback: Callable):
        """
        Remove callback de eventos do controlador.
        
        Args:
            event: Tipo de evento
            callback: Função callback
        """
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    def _notify_callbacks(self, event: str, data: Dict):
        """
        Notifica todos os callbacks de um evento.
        
        Args:
            event: Tipo de evento
            data: Dados do evento
        """
        for callback in self._callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Erro ao executar callback para evento {event}: {e}")
    
    def is_monitoring(self) -> bool:
        """
        Verifica se o monitoramento está ativo.
        
        Returns:
            bool: True se está monitorando, False caso contrário
        """
        return self._is_monitoring
    
    def get_system_status(self) -> Dict:
        """
        Obtém status geral do sistema.
        
        Returns:
            Dict: Status do sistema
        """
        try:
            latest_metrics = self.get_latest_metrics()
            health_analysis = self.ntp_service.analyze_server_health(latest_metrics)
            
            return {
                'monitoring_active': self._is_monitoring,
                'total_servers': len(self.config_service.get_servers()),
                'enabled_servers': len(self.config_service.get_enabled_servers()),
                'last_check': datetime.now(timezone.utc).isoformat(),
                'health_analysis': health_analysis,
                'database_status': self.database_service.get_status()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status do sistema: {e}")
            return {
                'monitoring_active': self._is_monitoring,
                'error': str(e)
            }