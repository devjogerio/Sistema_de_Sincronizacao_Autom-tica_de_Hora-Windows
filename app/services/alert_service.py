"""
Serviço de Alertas Inteligentes
Responsável por detectar anomalias e enviar alertas configuráveis
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

from app.services.database_service import DatabaseService
from app.services.ml_service import MLService
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

class AlertSeverity(Enum):
    """Níveis de severidade dos alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Tipos de alertas"""
    ANOMALY = "anomaly"
    THRESHOLD = "threshold"
    CONNECTIVITY = "connectivity"
    PERFORMANCE = "performance"
    TREND = "trend"

class AlertService:
    """Serviço de alertas inteligentes"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.ml_service = MLService()
        
        # Configurações de email (carregadas do .env)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', '')
        
        # Configurações padrão de alertas
        self.default_thresholds = {
            'response_time_ms': 1000,  # 1 segundo
            'offset_seconds': 0.1,     # 100ms
            'success_rate_percent': 95,
            'consecutive_failures': 3
        }
        
        # Cache de alertas recentes para evitar spam
        self._recent_alerts = {}
        self._alert_cooldown = timedelta(minutes=15)
        
        # Configurações de detecção
        self.anomaly_detection_enabled = True
        self.trend_analysis_enabled = True
        
    async def check_all_alerts(self) -> List[Dict[str, Any]]:
        """
        Verificar todos os tipos de alertas para todos os servidores
        
        Returns:
            Lista de alertas gerados
        """
        try:
            logger.info("Iniciando verificação de alertas")
            
            alerts_generated = []
            
            # Obter lista de servidores ativos
            servers = self.db_service.get_active_servers()
            
            for server in servers:
                server_id = server['id']
                server_name = server['name']
                
                logger.debug(f"Verificando alertas para servidor {server_name}")
                
                # Verificar conectividade
                connectivity_alerts = await self._check_connectivity_alerts(server_id, server_name)
                alerts_generated.extend(connectivity_alerts)
                
                # Verificar thresholds
                threshold_alerts = await self._check_threshold_alerts(server_id, server_name)
                alerts_generated.extend(threshold_alerts)
                
                # Verificar anomalias (se habilitado)
                if self.anomaly_detection_enabled:
                    anomaly_alerts = await self._check_anomaly_alerts(server_id, server_name)
                    alerts_generated.extend(anomaly_alerts)
                
                # Verificar tendências (se habilitado)
                if self.trend_analysis_enabled:
                    trend_alerts = await self._check_trend_alerts(server_id, server_name)
                    alerts_generated.extend(trend_alerts)
                
                # Verificar performance
                performance_alerts = await self._check_performance_alerts(server_id, server_name)
                alerts_generated.extend(performance_alerts)
            
            # Processar alertas gerados
            for alert in alerts_generated:
                await self._process_alert(alert)
            
            logger.info(f"Verificação de alertas concluída. {len(alerts_generated)} alertas gerados")
            return alerts_generated
            
        except Exception as e:
            logger.error(f"Erro na verificação de alertas: {e}")
            raise
    
    async def _check_connectivity_alerts(self, server_id: int, server_name: str) -> List[Dict[str, Any]]:
        """Verificar alertas de conectividade"""
        alerts = []
        
        try:
            # Obter últimas verificações
            recent_checks = self.db_service.get_recent_server_checks(server_id, hours=1)
            
            if not recent_checks:
                # Servidor sem verificações recentes
                alert = {
                    'server_id': server_id,
                    'server_name': server_name,
                    'type': AlertType.CONNECTIVITY.value,
                    'severity': AlertSeverity.HIGH.value,
                    'title': f'Servidor {server_name} sem verificações recentes',
                    'message': 'O servidor não possui verificações nas últimas 1 hora',
                    'timestamp': datetime.now(),
                    'data': {'hours_without_checks': 1}
                }
                alerts.append(alert)
                return alerts
            
            # Verificar falhas consecutivas
            consecutive_failures = 0
            for check in recent_checks[:10]:  # Últimas 10 verificações
                if not check.get('success', False):
                    consecutive_failures += 1
                else:
                    break
            
            if consecutive_failures >= self.default_thresholds['consecutive_failures']:
                severity = AlertSeverity.CRITICAL if consecutive_failures >= 5 else AlertSeverity.HIGH
                
                alert = {
                    'server_id': server_id,
                    'server_name': server_name,
                    'type': AlertType.CONNECTIVITY.value,
                    'severity': severity.value,
                    'title': f'Falhas consecutivas no servidor {server_name}',
                    'message': f'Servidor apresentou {consecutive_failures} falhas consecutivas',
                    'timestamp': datetime.now(),
                    'data': {'consecutive_failures': consecutive_failures}
                }
                alerts.append(alert)
            
            # Verificar taxa de sucesso
            success_count = sum(1 for check in recent_checks if check.get('success', False))
            success_rate = (success_count / len(recent_checks)) * 100
            
            if success_rate < self.default_thresholds['success_rate_percent']:
                severity = AlertSeverity.CRITICAL if success_rate < 50 else AlertSeverity.HIGH
                
                alert = {
                    'server_id': server_id,
                    'server_name': server_name,
                    'type': AlertType.CONNECTIVITY.value,
                    'severity': severity.value,
                    'title': f'Taxa de sucesso baixa no servidor {server_name}',
                    'message': f'Taxa de sucesso atual: {success_rate:.1f}% (limite: {self.default_thresholds["success_rate_percent"]}%)',
                    'timestamp': datetime.now(),
                    'data': {'success_rate': success_rate, 'threshold': self.default_thresholds['success_rate_percent']}
                }
                alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas de conectividade para servidor {server_id}: {e}")
        
        return alerts
    
    async def _check_threshold_alerts(self, server_id: int, server_name: str) -> List[Dict[str, Any]]:
        """Verificar alertas de threshold"""
        alerts = []
        
        try:
            # Obter última métrica
            latest_metric = self.db_service.get_latest_server_metric(server_id)
            
            if not latest_metric:
                return alerts
            
            # Verificar tempo de resposta
            response_time = latest_metric.get('response_time', 0)
            if response_time > self.default_thresholds['response_time_ms']:
                severity = AlertSeverity.CRITICAL if response_time > 5000 else AlertSeverity.HIGH
                
                alert = {
                    'server_id': server_id,
                    'server_name': server_name,
                    'type': AlertType.THRESHOLD.value,
                    'severity': severity.value,
                    'title': f'Tempo de resposta alto no servidor {server_name}',
                    'message': f'Tempo de resposta: {response_time}ms (limite: {self.default_thresholds["response_time_ms"]}ms)',
                    'timestamp': datetime.now(),
                    'data': {'response_time': response_time, 'threshold': self.default_thresholds['response_time_ms']}
                }
                alerts.append(alert)
            
            # Verificar offset
            offset = abs(latest_metric.get('offset', 0))
            if offset > self.default_thresholds['offset_seconds']:
                severity = AlertSeverity.CRITICAL if offset > 1.0 else AlertSeverity.HIGH
                
                alert = {
                    'server_id': server_id,
                    'server_name': server_name,
                    'type': AlertType.THRESHOLD.value,
                    'severity': severity.value,
                    'title': f'Offset alto no servidor {server_name}',
                    'message': f'Offset: {offset:.3f}s (limite: {self.default_thresholds["offset_seconds"]}s)',
                    'timestamp': datetime.now(),
                    'data': {'offset': offset, 'threshold': self.default_thresholds['offset_seconds']}
                }
                alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas de threshold para servidor {server_id}: {e}")
        
        return alerts
    
    async def _check_anomaly_alerts(self, server_id: int, server_name: str) -> List[Dict[str, Any]]:
        """Verificar alertas de anomalias usando ML"""
        alerts = []
        
        try:
            # Detectar anomalias usando diferentes métodos
            methods = ['isolation_forest', 'statistical']
            
            for method in methods:
                anomaly_result = await self.ml_service.detect_anomalies(
                    server_id=server_id,
                    lookback_hours=6,
                    method=method
                )
                
                if anomaly_result.get('anomalies_detected', False):
                    anomaly_count = anomaly_result.get('anomaly_count', 0)
                    anomaly_rate = anomaly_result.get('anomaly_rate', 0)
                    
                    # Determinar severidade baseada na taxa de anomalias
                    if anomaly_rate > 0.2:  # Mais de 20% de anomalias
                        severity = AlertSeverity.CRITICAL
                    elif anomaly_rate > 0.1:  # Mais de 10% de anomalias
                        severity = AlertSeverity.HIGH
                    elif anomaly_rate > 0.05:  # Mais de 5% de anomalias
                        severity = AlertSeverity.MEDIUM
                    else:
                        severity = AlertSeverity.LOW
                    
                    alert = {
                        'server_id': server_id,
                        'server_name': server_name,
                        'type': AlertType.ANOMALY.value,
                        'severity': severity.value,
                        'title': f'Anomalias detectadas no servidor {server_name}',
                        'message': f'Detectadas {anomaly_count} anomalias ({anomaly_rate:.1%}) usando método {method}',
                        'timestamp': datetime.now(),
                        'data': {
                            'method': method,
                            'anomaly_count': anomaly_count,
                            'anomaly_rate': anomaly_rate,
                            'anomalies': anomaly_result.get('anomalies', [])[:5]  # Primeiras 5 anomalias
                        }
                    }
                    alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas de anomalias para servidor {server_id}: {e}")
        
        return alerts
    
    async def _check_trend_alerts(self, server_id: int, server_name: str) -> List[Dict[str, Any]]:
        """Verificar alertas de tendências"""
        alerts = []
        
        try:
            # Analisar tendências
            trend_result = await self.ml_service.analyze_trends(
                server_id=server_id,
                lookback_days=3
            )
            
            if not trend_result.get('trends_available', False):
                return alerts
            
            trends = trend_result.get('trends', {})
            
            # Verificar tendências preocupantes
            for metric, trend_data in trends.items():
                direction = trend_data.get('direction')
                confidence = trend_data.get('confidence')
                r_squared = trend_data.get('r_squared', 0)
                
                # Alertar sobre tendências negativas com alta confiança
                if confidence in ['high', 'medium'] and r_squared > 0.5:
                    if metric == 'response_time' and direction == 'increasing':
                        alert = {
                            'server_id': server_id,
                            'server_name': server_name,
                            'type': AlertType.TREND.value,
                            'severity': AlertSeverity.MEDIUM.value,
                            'title': f'Tendência de aumento no tempo de resposta - {server_name}',
                            'message': f'Tempo de resposta apresenta tendência crescente (confiança: {confidence})',
                            'timestamp': datetime.now(),
                            'data': {
                                'metric': metric,
                                'direction': direction,
                                'confidence': confidence,
                                'r_squared': r_squared
                            }
                        }
                        alerts.append(alert)
                    
                    elif metric == 'offset' and direction == 'increasing':
                        alert = {
                            'server_id': server_id,
                            'server_name': server_name,
                            'type': AlertType.TREND.value,
                            'severity': AlertSeverity.MEDIUM.value,
                            'title': f'Tendência de aumento no offset - {server_name}',
                            'message': f'Offset apresenta tendência crescente (confiança: {confidence})',
                            'timestamp': datetime.now(),
                            'data': {
                                'metric': metric,
                                'direction': direction,
                                'confidence': confidence,
                                'r_squared': r_squared
                            }
                        }
                        alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas de tendências para servidor {server_id}: {e}")
        
        return alerts
    
    async def _check_performance_alerts(self, server_id: int, server_name: str) -> List[Dict[str, Any]]:
        """Verificar alertas de performance"""
        alerts = []
        
        try:
            # Obter estatísticas de performance das últimas 24 horas
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            perf_stats = self.db_service.get_server_performance_stats(server_id, start_time, end_time)
            
            if not perf_stats:
                return alerts
            
            # Verificar degradação de performance
            avg_response_time = perf_stats.get('avg_response_time', 0)
            max_response_time = perf_stats.get('max_response_time', 0)
            std_response_time = perf_stats.get('std_response_time', 0)
            
            # Alerta se o tempo médio estiver muito alto
            if avg_response_time > 500:  # 500ms
                severity = AlertSeverity.HIGH if avg_response_time > 1000 else AlertSeverity.MEDIUM
                
                alert = {
                    'server_id': server_id,
                    'server_name': server_name,
                    'type': AlertType.PERFORMANCE.value,
                    'severity': severity.value,
                    'title': f'Performance degradada no servidor {server_name}',
                    'message': f'Tempo médio de resposta nas últimas 24h: {avg_response_time:.0f}ms',
                    'timestamp': datetime.now(),
                    'data': {
                        'avg_response_time': avg_response_time,
                        'max_response_time': max_response_time,
                        'std_response_time': std_response_time
                    }
                }
                alerts.append(alert)
            
            # Alerta se houver muita variabilidade
            if std_response_time > avg_response_time * 0.5:  # Desvio > 50% da média
                alert = {
                    'server_id': server_id,
                    'server_name': server_name,
                    'type': AlertType.PERFORMANCE.value,
                    'severity': AlertSeverity.MEDIUM.value,
                    'title': f'Alta variabilidade na performance - {server_name}',
                    'message': f'Desvio padrão do tempo de resposta: {std_response_time:.0f}ms (média: {avg_response_time:.0f}ms)',
                    'timestamp': datetime.now(),
                    'data': {
                        'avg_response_time': avg_response_time,
                        'std_response_time': std_response_time,
                        'variability_ratio': std_response_time / avg_response_time if avg_response_time > 0 else 0
                    }
                }
                alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas de performance para servidor {server_id}: {e}")
        
        return alerts
    
    async def _process_alert(self, alert: Dict[str, Any]) -> None:
        """Processar um alerta (salvar no banco, enviar notificações, etc.)"""
        try:
            # Verificar cooldown para evitar spam
            alert_key = f"{alert['server_id']}_{alert['type']}_{alert['severity']}"
            
            if self._is_in_cooldown(alert_key):
                logger.debug(f"Alerta em cooldown, ignorando: {alert_key}")
                return
            
            # Salvar alerta no banco de dados
            alert_id = self.db_service.save_alert(alert)
            alert['id'] = alert_id
            
            # Marcar no cache de cooldown
            self._recent_alerts[alert_key] = datetime.now()
            
            # Enviar notificações baseado na severidade
            if alert['severity'] in [AlertSeverity.HIGH.value, AlertSeverity.CRITICAL.value]:
                await self._send_email_notification(alert)
            
            # Log do alerta
            logger.warning(f"Alerta gerado: {alert['title']} - Severidade: {alert['severity']}")
            
        except Exception as e:
            logger.error(f"Erro ao processar alerta: {e}")
    
    def _is_in_cooldown(self, alert_key: str) -> bool:
        """Verificar se um alerta está em período de cooldown"""
        if alert_key not in self._recent_alerts:
            return False
        
        last_alert_time = self._recent_alerts[alert_key]
        return datetime.now() - last_alert_time < self._alert_cooldown
    
    async def _send_email_notification(self, alert: Dict[str, Any]) -> None:
        """Enviar notificação por email"""
        try:
            if not all([self.smtp_username, self.smtp_password, self.from_email]):
                logger.warning("Configurações de email não definidas, pulando notificação")
                return
            
            # Obter lista de destinatários
            recipients = self.db_service.get_alert_recipients(alert['severity'])
            
            if not recipients:
                logger.warning("Nenhum destinatário configurado para alertas")
                return
            
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[NTP Monitor] {alert['title']}"
            
            # Corpo do email
            body = f"""
            Alerta NTP Monitor
            
            Servidor: {alert['server_name']}
            Tipo: {alert['type']}
            Severidade: {alert['severity'].upper()}
            Timestamp: {alert['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}
            
            Mensagem:
            {alert['message']}
            
            Dados adicionais:
            {json.dumps(alert.get('data', {}), indent=2, default=str)}
            
            ---
            Este é um alerta automático do sistema NTP Monitor.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Notificação por email enviada para {len(recipients)} destinatários")
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação por email: {e}")
    
    async def get_active_alerts(self, server_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obter alertas ativos
        
        Args:
            server_id: ID do servidor (opcional)
            
        Returns:
            Lista de alertas ativos
        """
        try:
            return self.db_service.get_active_alerts(server_id)
        except Exception as e:
            logger.error(f"Erro ao obter alertas ativos: {e}")
            raise
    
    async def acknowledge_alert(self, alert_id: int, user_id: Optional[int] = None) -> bool:
        """
        Reconhecer um alerta
        
        Args:
            alert_id: ID do alerta
            user_id: ID do usuário que reconheceu
            
        Returns:
            True se bem-sucedido
        """
        try:
            return self.db_service.acknowledge_alert(alert_id, user_id)
        except Exception as e:
            logger.error(f"Erro ao reconhecer alerta {alert_id}: {e}")
            raise
    
    def update_thresholds(self, new_thresholds: Dict[str, Any]) -> None:
        """
        Atualizar thresholds de alertas
        
        Args:
            new_thresholds: Novos valores de threshold
        """
        try:
            self.default_thresholds.update(new_thresholds)
            logger.info(f"Thresholds atualizados: {new_thresholds}")
        except Exception as e:
            logger.error(f"Erro ao atualizar thresholds: {e}")
            raise