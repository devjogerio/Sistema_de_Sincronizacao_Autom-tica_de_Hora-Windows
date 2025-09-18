"""
Controlador do dashboard NTP Monitor.
Gerencia interação entre view e serviços.
"""

import logging
import threading
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ..views.dashboard_view import DashboardView
from ..services.ntp_service import NTPService
from ..services.config_service import ConfigService
from ..services.database_service import DatabaseService
from ..services.email_service import EmailService
from ..models.ntp_metrics import NTPMetrics

logger = logging.getLogger(__name__)


class DashboardController:
    """
    Controlador principal do dashboard.
    
    Coordena a interação entre a interface gráfica
    e os serviços de backend da aplicação.
    """
    
    def __init__(self):
        """Inicializa o controlador do dashboard."""
        # Serviços
        self.config_service = ConfigService()
        self.ntp_service = NTPService()
        self.database_service = DatabaseService()
        self.email_service = EmailService()
        
        # View
        self.view = None
        
        # Estado do monitoramento
        self.is_monitoring = False
        self.monitoring_thread = None
        self.stop_monitoring_event = threading.Event()
        
        # Configurações
        self.config = None
        self.last_alert_time = {}
        
        logger.info("Dashboard controller inicializado")
    
    def initialize(self):
        """Inicializa o controlador e seus componentes."""
        try:
            # Carrega configurações
            if not self.config_service.load_config():
                logger.error("Falha ao carregar configurações")
                return False
            
            self.config = self.config_service.get_config()
            
            # Inicializa serviços
            self.database_service.initialize()
            
            # Configura email service
            if self.config.email:
                self.email_service.configure(self.config.email)
            
            # View será criada no método run() para evitar problemas de inicialização do Tkinter
            self.view = None
            
            logger.info("Controlador inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar controlador: {e}")
            return False
            raise
    
    def _setup_view_callbacks(self):
        """Configura callbacks da view."""
        if not self.view:
            return
        
        self.view.set_callback('start_monitoring', self.start_monitoring)
        self.view.set_callback('stop_monitoring', self.stop_monitoring)
        self.view.set_callback('refresh_data', self.refresh_data)
        self.view.set_callback('export_data', self.export_data)
    
    def start_monitoring(self):
        """Inicia o monitoramento contínuo."""
        if self.is_monitoring:
            logger.warning("Monitoramento já está ativo")
            return
        
        try:
            # Valida configuração
            if not self.config or not self.config.servers:
                self.view.show_message("Erro", 
                                     "Nenhum servidor NTP configurado", 
                                     "error")
                return
            
            # Inicia thread de monitoramento
            self.stop_monitoring_event.clear()
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            
            self.is_monitoring = True
            self.monitoring_thread.start()
            
            # Atualiza interface
            self.view.set_monitoring_status(True)
            self.view.show_message("Sucesso", 
                                 "Monitoramento iniciado com sucesso", 
                                 "info")
            
            logger.info("Monitoramento iniciado")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento: {e}")
            self.view.show_message("Erro", 
                                 f"Erro ao iniciar monitoramento: {e}", 
                                 "error")
    
    def stop_monitoring(self):
        """Para o monitoramento contínuo."""
        if not self.is_monitoring:
            logger.warning("Monitoramento não está ativo")
            return
        
        try:
            # Sinaliza parada
            self.stop_monitoring_event.set()
            self.is_monitoring = False
            
            # Aguarda thread terminar
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)
            
            # Atualiza interface
            self.view.set_monitoring_status(False)
            self.view.show_message("Sucesso", 
                                 "Monitoramento parado com sucesso", 
                                 "info")
            
            logger.info("Monitoramento parado")
            
        except Exception as e:
            logger.error(f"Erro ao parar monitoramento: {e}")
            self.view.show_message("Erro", 
                                 f"Erro ao parar monitoramento: {e}", 
                                 "error")
    
    def refresh_data(self):
        """Atualiza dados na interface."""
        try:
            # Executa verificação única
            threading.Thread(
                target=self._single_check,
                daemon=True
            ).start()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar dados: {e}")
            self.view.show_message("Erro", 
                                 f"Erro ao atualizar dados: {e}", 
                                 "error")
    
    def export_data(self):
        """Exporta dados históricos."""
        try:
            # Obtém dados do banco
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)  # Últimos 7 dias
            
            metrics_data = self.database_service.get_metrics_history(
                start_time, end_time
            )
            
            if not metrics_data:
                self.view.show_message("Aviso", 
                                     "Nenhum dado disponível para exportação", 
                                     "warning")
                return
            
            # Gera arquivo CSV
            filename = f"ntp_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self._export_to_csv(metrics_data, filename)
            
            self.view.show_message("Sucesso", 
                                 f"Dados exportados para {filename}", 
                                 "info")
            
            logger.info(f"Dados exportados para {filename}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {e}")
            self.view.show_message("Erro", 
                                 f"Erro ao exportar dados: {e}", 
                                 "error")
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento."""
        logger.info("Iniciando loop de monitoramento")
        
        while not self.stop_monitoring_event.is_set():
            try:
                # Executa verificação
                self._perform_monitoring_check()
                
                # Aguarda próximo ciclo
                interval = self.config.monitoring.update_interval if self.config.monitoring else 60
                self.stop_monitoring_event.wait(interval)
                
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                # Continua o loop mesmo com erro
                self.stop_monitoring_event.wait(10)  # Aguarda 10s antes de tentar novamente
        
        logger.info("Loop de monitoramento finalizado")
    
    def _perform_monitoring_check(self):
        """Executa uma verificação completa de monitoramento."""
        try:
            # Verifica todos os servidores
            servers = [server.address for server in self.config.servers]
            results = self.ntp_service.check_multiple_servers(servers)
            
            # Processa resultados
            metrics_list = []
            for server, result in results.items():
                if result:
                    metrics = NTPMetrics(
                        server=server,
                        timestamp=datetime.now(),
                        response_time=result.get('response_time', 0.0),
                        offset=result.get('offset', 0.0),
                        delay=result.get('delay', 0.0),
                        stratum=result.get('stratum', 0),
                        is_available=True
                    )
                else:
                    # Servidor indisponível
                    metrics = NTPMetrics(
                        server=server,
                        timestamp=datetime.now(),
                        response_time=0.0,
                        offset=0.0,
                        delay=0.0,
                        stratum=0,
                        is_available=False
                    )
                
                metrics_list.append(metrics)
            
            # Armazena no banco de dados
            for metrics in metrics_list:
                self.database_service.store_metrics(metrics)
            
            # Atualiza interface (thread-safe)
            if self.view:
                self.view.root.after(0, lambda: self.view.update_metrics(metrics_list))
            
            # Verifica alertas
            self._check_alerts(metrics_list)
            
        except Exception as e:
            logger.error(f"Erro na verificação de monitoramento: {e}")
    
    def _single_check(self):
        """Executa uma verificação única (não contínua)."""
        try:
            if not self.config or not self.config.servers:
                return
            
            # Verifica servidores
            servers = [server.address for server in self.config.servers]
            results = self.ntp_service.check_multiple_servers(servers)
            
            # Processa resultados
            metrics_list = []
            for server, result in results.items():
                if result:
                    metrics = NTPMetrics(
                        server=server,
                        timestamp=datetime.now(),
                        response_time=result.get('response_time', 0.0),
                        offset=result.get('offset', 0.0),
                        delay=result.get('delay', 0.0),
                        stratum=result.get('stratum', 0),
                        is_available=True
                    )
                else:
                    metrics = NTPMetrics(
                        server=server,
                        timestamp=datetime.now(),
                        response_time=0.0,
                        offset=0.0,
                        delay=0.0,
                        stratum=0,
                        is_available=False
                    )
                
                metrics_list.append(metrics)
            
            # Atualiza interface
            if self.view:
                self.view.root.after(0, lambda: self.view.update_metrics(metrics_list))
            
        except Exception as e:
            logger.error(f"Erro na verificação única: {e}")
    
    def _check_alerts(self, metrics_list: List[NTPMetrics]):
        """
        Verifica condições de alerta.
        
        Args:
            metrics_list: Lista de métricas coletadas
        """
        if not self.config.alerts or not self.config.alerts.enabled:
            return
        
        try:
            current_time = datetime.now()
            
            for metrics in metrics_list:
                server = metrics.server
                
                # Verifica se deve enviar alerta (cooldown)
                last_alert = self.last_alert_time.get(server)
                if last_alert:
                    time_diff = (current_time - last_alert).total_seconds()
                    if time_diff < self.config.alerts.cooldown_minutes * 60:
                        continue  # Ainda em cooldown
                
                # Verifica condições de alerta
                alert_triggered = False
                alert_message = ""
                
                if not metrics.is_available:
                    alert_triggered = True
                    alert_message = f"Servidor {server} está indisponível"
                
                elif not metrics.is_healthy():
                    alert_triggered = True
                    alert_message = f"Servidor {server} apresenta problemas de sincronização"
                
                elif metrics.response_time > self.config.alerts.max_response_time:
                    alert_triggered = True
                    alert_message = f"Servidor {server} com tempo de resposta alto: {metrics.response_time:.3f}s"
                
                elif abs(metrics.offset) > self.config.alerts.max_offset:
                    alert_triggered = True
                    alert_message = f"Servidor {server} com offset alto: {metrics.offset:.3f}s"
                
                # Envia alerta se necessário
                if alert_triggered:
                    self._send_alert(server, alert_message, metrics)
                    self.last_alert_time[server] = current_time
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas: {e}")
    
    def _send_alert(self, server: str, message: str, metrics: NTPMetrics):
        """
        Envia alerta por email.
        
        Args:
            server: Endereço do servidor
            message: Mensagem do alerta
            metrics: Métricas do servidor
        """
        try:
            if not self.config.email or not self.email_service:
                return
            
            # Prepara dados do alerta
            alert_data = {
                'server': server,
                'message': message,
                'timestamp': metrics.timestamp,
                'metrics': metrics.to_dict()
            }
            
            # Envia email
            self.email_service.send_alert(alert_data)
            
            logger.info(f"Alerta enviado para {server}: {message}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar alerta: {e}")
    
    def _export_to_csv(self, metrics_data: List[Dict], filename: str):
        """
        Exporta dados para arquivo CSV.
        
        Args:
            metrics_data: Lista de dados de métricas
            filename: Nome do arquivo
        """
        import csv
        
        if not metrics_data:
            return
        
        # Cabeçalhos do CSV
        headers = ['timestamp', 'server', 'response_time', 'offset', 
                  'delay', 'stratum', 'is_available']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for data in metrics_data:
                # Converte timestamp para string legível
                if isinstance(data.get('timestamp'), datetime):
                    data['timestamp'] = data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                writer.writerow(data)
    
    def run(self):
        """Executa o dashboard."""
        try:
            # Inicializa o controlador
            if not self.initialize():
                logger.error("Falha na inicialização do controlador")
                return
            
            # Cria e configura view após inicialização
            self.view = DashboardView("NTP Monitor Dashboard")
            self._setup_view_callbacks()
            
            # Inicia o loop da interface
            self.view.run()
            
        except KeyboardInterrupt:
            logger.info("Interrupção pelo usuário")
        except Exception as e:
            logger.error(f"Erro ao executar dashboard: {e}")
            raise
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpa recursos utilizados."""
        try:
            # Para monitoramento se estiver ativo
            if self.is_monitoring:
                self.stop_monitoring()
            
            # Fecha conexões do banco
            if self.database_service:
                self.database_service.close()
            
            logger.info("Cleanup do controlador concluído")
            
        except Exception as e:
            logger.error(f"Erro no cleanup: {e}")


def main():
    """Função principal para executar o dashboard."""
    # Configuração de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ntp_monitor.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Cria e executa controlador
        controller = DashboardController()
        controller.run()
        
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal na aplicação: {e}")
        raise


if __name__ == "__main__":
    main()