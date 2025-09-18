"""
Sistema de notificações por email para alertas de monitoramento NTP.
Implementa envio configurável de emails com templates e condições personalizáveis.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
import json
import os
from config_manager import ConfigManager

# Configuração de logging
logger = logging.getLogger(__name__)

@dataclass
class AlertCondition:
    """
    Representa uma condição de alerta configurável.
    """
    name: str
    condition_type: str  # 'availability', 'response_time', 'offset', 'custom'
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '=='
    duration_minutes: int = 5  # Duração mínima da condição
    enabled: bool = True
    
    def check_condition(self, value: float) -> bool:
        """
        Verifica se a condição é atendida.
        
        Args:
            value: Valor a ser verificado
            
        Returns:
            bool: True se a condição for atendida
        """
        try:
            if self.operator == '>':
                return value > self.threshold
            elif self.operator == '<':
                return value < self.threshold
            elif self.operator == '>=':
                return value >= self.threshold
            elif self.operator == '<=':
                return value <= self.threshold
            elif self.operator == '==':
                return value == self.threshold
            else:
                logger.warning(f"Operador desconhecido: {self.operator}")
                return False
        except Exception as e:
            logger.error(f"Erro ao verificar condição {self.name}: {e}")
            return False

@dataclass
class EmailConfig:
    """
    Configuração de email para notificações.
    """
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    sender_email: str
    sender_name: str = "NTP Monitor"
    use_tls: bool = True
    use_ssl: bool = False
    
    def validate(self) -> bool:
        """
        Valida a configuração de email.
        
        Returns:
            bool: True se a configuração é válida
        """
        required_fields = [
            self.smtp_server, self.smtp_port, self.username,
            self.password, self.sender_email
        ]
        
        return all(field for field in required_fields)

class EmailNotifier:
    """
    Sistema de notificações por email para alertas NTP.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Inicializa o notificador de email.
        
        Args:
            config_manager: Gerenciador de configurações
        """
        self.config_manager = config_manager
        self.email_config = config_manager.email
        self.alert_conditions = self._load_alert_conditions()
        self.alert_history = {}  # Histórico de alertas por servidor
        self.cooldown_periods = {}  # Períodos de cooldown por tipo de alerta
        
        # Templates de email
        self.templates = {
            'availability': self._get_availability_template(),
            'response_time': self._get_response_time_template(),
            'offset': self._get_offset_template(),
            'server_down': self._get_server_down_template(),
            'server_recovered': self._get_server_recovered_template(),
            'summary': self._get_summary_template()
        }
    
    def _load_alert_conditions(self) -> List[AlertCondition]:
        """
        Carrega condições de alerta da configuração.
        
        Returns:
            List[AlertCondition]: Lista de condições de alerta
        """
        conditions = []
        
        # Condições padrão baseadas na configuração
        alert_config = self.config_manager.alerts
        
        # Disponibilidade baixa
        if alert_config.availability_threshold > 0:
            conditions.append(AlertCondition(
                name="low_availability",
                condition_type="availability",
                threshold=alert_config.availability_threshold,
                operator="<",
                duration_minutes=alert_config.alert_cooldown_minutes,
                enabled=True
            ))
        
        # Tempo de resposta alto
        if alert_config.slow_response_threshold > 0:
            conditions.append(AlertCondition(
                name="high_response_time",
                condition_type="response_time",
                threshold=alert_config.slow_response_threshold,
                operator=">",
                duration_minutes=alert_config.alert_cooldown_minutes,
                enabled=True
            ))
        
        # Offset alto
        if alert_config.high_offset_threshold > 0:
            conditions.append(AlertCondition(
                name="high_offset",
                condition_type="offset",
                threshold=alert_config.high_offset_threshold,
                operator=">",
                duration_minutes=alert_config.alert_cooldown_minutes,
                enabled=True
            ))
        
        return conditions
    
    def _get_availability_template(self) -> str:
        """Template para alertas de disponibilidade."""
        return """
        <html>
        <body>
            <h2 style="color: #d32f2f;">⚠️ Alerta de Disponibilidade NTP</h2>
            <p><strong>Servidor:</strong> {server_address}</p>
            <p><strong>Disponibilidade:</strong> {availability}%</p>
            <p><strong>Limite:</strong> {threshold}%</p>
            <p><strong>Data/Hora:</strong> {timestamp}</p>
            <p><strong>Duração:</strong> {duration} minutos</p>
            
            <h3>Detalhes:</h3>
            <ul>
                <li>Verificações totais: {total_checks}</li>
                <li>Verificações bem-sucedidas: {successful_checks}</li>
                <li>Verificações falhadas: {failed_checks}</li>
            </ul>
            
            <p style="color: #666; font-size: 12px;">
                Este alerta foi gerado automaticamente pelo sistema de monitoramento NTP.
            </p>
        </body>
        </html>
        """
    
    def _get_response_time_template(self) -> str:
        """Template para alertas de tempo de resposta."""
        return """
        <html>
        <body>
            <h2 style="color: #ff9800;">⏱️ Alerta de Tempo de Resposta NTP</h2>
            <p><strong>Servidor:</strong> {server_address}</p>
            <p><strong>Tempo de Resposta:</strong> {response_time}ms</p>
            <p><strong>Limite:</strong> {threshold}ms</p>
            <p><strong>Data/Hora:</strong> {timestamp}</p>
            
            <h3>Métricas Recentes:</h3>
            <ul>
                <li>Tempo médio: {avg_response_time}ms</li>
                <li>Tempo mínimo: {min_response_time}ms</li>
                <li>Tempo máximo: {max_response_time}ms</li>
            </ul>
            
            <p style="color: #666; font-size: 12px;">
                Este alerta foi gerado automaticamente pelo sistema de monitoramento NTP.
            </p>
        </body>
        </html>
        """
    
    def _get_offset_template(self) -> str:
        """Template para alertas de offset."""
        return """
        <html>
        <body>
            <h2 style="color: #f44336;">🕐 Alerta de Sincronização NTP</h2>
            <p><strong>Servidor:</strong> {server_address}</p>
            <p><strong>Offset:</strong> {offset}ms</p>
            <p><strong>Limite:</strong> {threshold}ms</p>
            <p><strong>Data/Hora:</strong> {timestamp}</p>
            
            <h3>Informações de Sincronização:</h3>
            <ul>
                <li>Delay: {delay}ms</li>
                <li>Stratum: {stratum}</li>
                <li>Precisão: {precision}</li>
            </ul>
            
            <p style="color: #666; font-size: 12px;">
                Este alerta foi gerado automaticamente pelo sistema de monitoramento NTP.
            </p>
        </body>
        </html>
        """
    
    def _get_server_down_template(self) -> str:
        """Template para servidor indisponível."""
        return """
        <html>
        <body>
            <h2 style="color: #d32f2f;">🔴 Servidor NTP Indisponível</h2>
            <p><strong>Servidor:</strong> {server_address}</p>
            <p><strong>Status:</strong> Indisponível</p>
            <p><strong>Data/Hora:</strong> {timestamp}</p>
            <p><strong>Erro:</strong> {error_message}</p>
            
            <h3>Ações Recomendadas:</h3>
            <ul>
                <li>Verificar conectividade de rede</li>
                <li>Confirmar se o servidor está operacional</li>
                <li>Considerar usar servidor alternativo</li>
            </ul>
            
            <p style="color: #666; font-size: 12px;">
                Este alerta foi gerado automaticamente pelo sistema de monitoramento NTP.
            </p>
        </body>
        </html>
        """
    
    def _get_server_recovered_template(self) -> str:
        """Template para recuperação de servidor."""
        return """
        <html>
        <body>
            <h2 style="color: #4caf50;">✅ Servidor NTP Recuperado</h2>
            <p><strong>Servidor:</strong> {server_address}</p>
            <p><strong>Status:</strong> Operacional</p>
            <p><strong>Data/Hora:</strong> {timestamp}</p>
            <p><strong>Tempo Indisponível:</strong> {downtime} minutos</p>
            
            <h3>Métricas Atuais:</h3>
            <ul>
                <li>Tempo de resposta: {response_time}ms</li>
                <li>Offset: {offset}ms</li>
                <li>Disponibilidade: {availability}%</li>
            </ul>
            
            <p style="color: #666; font-size: 12px;">
                Este alerta foi gerado automaticamente pelo sistema de monitoramento NTP.
            </p>
        </body>
        </html>
        """
    
    def _get_summary_template(self) -> str:
        """Template para relatório resumo."""
        return """
        <html>
        <body>
            <h2 style="color: #2196f3;">📊 Relatório de Monitoramento NTP</h2>
            <p><strong>Período:</strong> {period}</p>
            <p><strong>Gerado em:</strong> {timestamp}</p>
            
            <h3>Resumo Geral:</h3>
            <ul>
                <li>Total de servidores: {total_servers}</li>
                <li>Disponibilidade média: {avg_availability}%</li>
                <li>Tempo de resposta médio: {avg_response_time}ms</li>
                <li>Offset médio: {avg_offset}ms</li>
            </ul>
            
            <h3>Top Servidores por Disponibilidade:</h3>
            <ol>
                {top_availability_servers}
            </ol>
            
            <h3>Alertas no Período:</h3>
            <ul>
                {alerts_summary}
            </ul>
            
            <p style="color: #666; font-size: 12px;">
                Este relatório foi gerado automaticamente pelo sistema de monitoramento NTP.
            </p>
        </body>
        </html>
        """
    
    def check_and_send_alerts(self, server_metrics: Dict[str, Dict]) -> List[str]:
        """
        Verifica condições de alerta e envia notificações.
        
        Args:
            server_metrics: Métricas dos servidores
            
        Returns:
            List[str]: Lista de alertas enviados
        """
        sent_alerts = []
        
        try:
            for server_address, metrics in server_metrics.items():
                for condition in self.alert_conditions:
                    if not condition.enabled:
                        continue
                    
                    # Obtém valor da métrica
                    value = self._get_metric_value(metrics, condition.condition_type)
                    
                    if value is None:
                        continue
                    
                    # Verifica se a condição é atendida
                    if condition.check_condition(value):
                        # Verifica cooldown
                        if self._is_in_cooldown(server_address, condition.name):
                            continue
                        
                        # Envia alerta
                        if self._send_alert_email(server_address, condition, metrics, value):
                            sent_alerts.append(f"{server_address}:{condition.name}")
                            self._update_cooldown(server_address, condition.name)
                    
                    else:
                        # Verifica se houve recuperação
                        if self._check_recovery(server_address, condition.name):
                            if self._send_recovery_email(server_address, condition, metrics):
                                sent_alerts.append(f"{server_address}:recovered")
            
            return sent_alerts
            
        except Exception as e:
            logger.error(f"Erro ao verificar e enviar alertas: {e}")
            return []
    
    def _get_metric_value(self, metrics: Dict, condition_type: str) -> Optional[float]:
        """
        Obtém valor da métrica baseado no tipo de condição.
        
        Args:
            metrics: Métricas do servidor
            condition_type: Tipo de condição
            
        Returns:
            Optional[float]: Valor da métrica ou None
        """
        try:
            if condition_type == 'availability':
                return metrics.get('availability_percent', 0.0)
            elif condition_type == 'response_time':
                return (metrics.get('avg_response_time', 0.0) or 0.0) * 1000  # Converte para ms
            elif condition_type == 'offset':
                return abs(metrics.get('avg_offset', 0.0) or 0.0) * 1000  # Converte para ms
            else:
                return None
        except Exception as e:
            logger.error(f"Erro ao obter valor da métrica {condition_type}: {e}")
            return None
    
    def _is_in_cooldown(self, server_address: str, condition_name: str) -> bool:
        """
        Verifica se o alerta está em período de cooldown.
        
        Args:
            server_address: Endereço do servidor
            condition_name: Nome da condição
            
        Returns:
            bool: True se está em cooldown
        """
        key = f"{server_address}:{condition_name}"
        
        if key not in self.cooldown_periods:
            return False
        
        cooldown_until = self.cooldown_periods[key]
        return datetime.now() < cooldown_until
    
    def _update_cooldown(self, server_address: str, condition_name: str):
        """
        Atualiza período de cooldown para um alerta.
        
        Args:
            server_address: Endereço do servidor
            condition_name: Nome da condição
        """
        key = f"{server_address}:{condition_name}"
        cooldown_minutes = self.config_manager.alerts.alert_cooldown_minutes
        
        self.cooldown_periods[key] = datetime.now() + timedelta(minutes=cooldown_minutes)
    
    def _check_recovery(self, server_address: str, condition_name: str) -> bool:
        """
        Verifica se houve recuperação de um alerta.
        
        Args:
            server_address: Endereço do servidor
            condition_name: Nome da condição
            
        Returns:
            bool: True se houve recuperação
        """
        key = f"{server_address}:{condition_name}"
        
        # Se estava em cooldown e agora não está mais em condição de alerta
        if key in self.cooldown_periods:
            # Remove do cooldown para permitir nova verificação
            del self.cooldown_periods[key]
            return True
        
        return False
    
    def _send_alert_email(self, server_address: str, condition: AlertCondition, 
                         metrics: Dict, value: float) -> bool:
        """
        Envia email de alerta.
        
        Args:
            server_address: Endereço do servidor
            condition: Condição de alerta
            metrics: Métricas do servidor
            value: Valor que disparou o alerta
            
        Returns:
            bool: True se o email foi enviado com sucesso
        """
        try:
            # Seleciona template baseado no tipo de condição
            template = self.templates.get(condition.condition_type, self.templates['availability'])
            
            # Prepara dados para o template
            template_data = {
                'server_address': server_address,
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'threshold': condition.threshold,
                'duration': condition.duration_minutes,
                **metrics
            }
            
            # Adiciona dados específicos do tipo de alerta
            if condition.condition_type == 'availability':
                template_data.update({
                    'availability': round(value, 2),
                    'total_checks': metrics.get('total_checks', 0),
                    'successful_checks': metrics.get('successful_checks', 0),
                    'failed_checks': metrics.get('total_checks', 0) - metrics.get('successful_checks', 0)
                })
            elif condition.condition_type == 'response_time':
                template_data.update({
                    'response_time': round(value, 2),
                    'avg_response_time': round((metrics.get('avg_response_time', 0) or 0) * 1000, 2),
                    'min_response_time': round((metrics.get('min_response_time', 0) or 0) * 1000, 2),
                    'max_response_time': round((metrics.get('max_response_time', 0) or 0) * 1000, 2)
                })
            elif condition.condition_type == 'offset':
                template_data.update({
                    'offset': round(value, 2),
                    'delay': round((metrics.get('avg_delay', 0) or 0) * 1000, 2),
                    'stratum': metrics.get('stratum', 'N/A'),
                    'precision': metrics.get('precision', 'N/A')
                })
            
            # Formata conteúdo do email
            subject = f"🚨 Alerta NTP: {condition.name.replace('_', ' ').title()} - {server_address}"
            body = template.format(**template_data)
            
            # Envia email
            return self._send_email(
                recipients=self.config_manager.email.recipients,
                subject=subject,
                body=body,
                is_html=True
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar email de alerta para {server_address}: {e}")
            return False
    
    def _send_recovery_email(self, server_address: str, condition: AlertCondition, 
                           metrics: Dict) -> bool:
        """
        Envia email de recuperação.
        
        Args:
            server_address: Endereço do servidor
            condition: Condição que foi recuperada
            metrics: Métricas atuais do servidor
            
        Returns:
            bool: True se o email foi enviado com sucesso
        """
        try:
            template = self.templates['server_recovered']
            
            template_data = {
                'server_address': server_address,
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'downtime': condition.duration_minutes,
                'response_time': round((metrics.get('avg_response_time', 0) or 0) * 1000, 2),
                'offset': round(abs(metrics.get('avg_offset', 0) or 0) * 1000, 2),
                'availability': round(metrics.get('availability_percent', 0), 2)
            }
            
            subject = f"✅ Recuperação NTP: {server_address}"
            body = template.format(**template_data)
            
            return self._send_email(
                recipients=self.config_manager.email.recipients,
                subject=subject,
                body=body,
                is_html=True
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar email de recuperação para {server_address}: {e}")
            return False
    
    def send_summary_report(self, report_data: Dict) -> bool:
        """
        Envia relatório resumo por email.
        
        Args:
            report_data: Dados do relatório
            
        Returns:
            bool: True se o email foi enviado com sucesso
        """
        try:
            template = self.templates['summary']
            
            # Formata lista de top servidores
            top_servers_html = ""
            for server_data in report_data.get('top_servers', {}).get('availability', []):
                top_servers_html += f"<li>{server_data['server']} - {server_data['availability']}%</li>"
            
            # Formata resumo de alertas (placeholder)
            alerts_html = "<li>Nenhum alerta crítico no período</li>"
            
            template_data = {
                'period': f"{report_data.get('period_days', 7)} dias",
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'total_servers': report_data.get('general_stats', {}).get('total_servers', 0),
                'avg_availability': report_data.get('general_stats', {}).get('avg_availability', 0),
                'avg_response_time': report_data.get('general_stats', {}).get('avg_response_time', 0),
                'avg_offset': report_data.get('general_stats', {}).get('avg_offset', 0),
                'top_availability_servers': top_servers_html,
                'alerts_summary': alerts_html
            }
            
            subject = f"📊 Relatório NTP - {datetime.now().strftime('%d/%m/%Y')}"
            body = template.format(**template_data)
            
            return self._send_email(
                recipients=self.config_manager.email.recipients,
                subject=subject,
                body=body,
                is_html=True
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar relatório resumo: {e}")
            return False
    
    def _send_email(self, recipients: List[str], subject: str, body: str, 
                   is_html: bool = False) -> bool:
        """
        Envia email usando configuração SMTP.
        
        Args:
            recipients: Lista de destinatários
            subject: Assunto do email
            body: Corpo do email
            is_html: Se o corpo é HTML
            
        Returns:
            bool: True se o email foi enviado com sucesso
        """
        try:
            if not self.email_config.validate():
                logger.error("Configuração de email inválida")
                return False
            
            # Cria mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_config.sender_name} <{self.email_config.sender_email}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Adiciona corpo da mensagem
            if is_html:
                msg.attach(MIMEText(body, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Conecta ao servidor SMTP
            if self.email_config.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.email_config.smtp_server, 
                    self.email_config.smtp_port, 
                    context=context
                )
            else:
                server = smtplib.SMTP(
                    self.email_config.smtp_server, 
                    self.email_config.smtp_port
                )
                
                if self.email_config.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # Autentica e envia
            server.login(self.email_config.username, self.email_config.password)
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
            logger.info(f"Email enviado com sucesso para {len(recipients)} destinatários")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
    
    def test_email_configuration(self) -> bool:
        """
        Testa a configuração de email enviando um email de teste.
        
        Returns:
            bool: True se o teste foi bem-sucedido
        """
        try:
            test_subject = "🧪 Teste de Configuração - NTP Monitor"
            test_body = """
            <html>
            <body>
                <h2>Teste de Configuração de Email</h2>
                <p>Este é um email de teste para verificar se as configurações estão corretas.</p>
                <p><strong>Data/Hora:</strong> {timestamp}</p>
                <p>Se você recebeu este email, a configuração está funcionando corretamente!</p>
            </body>
            </html>
            """.format(timestamp=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            
            return self._send_email(
                recipients=self.config_manager.email.recipients,
                subject=test_subject,
                body=test_body,
                is_html=True
            )
            
        except Exception as e:
            logger.error(f"Erro no teste de configuração de email: {e}")
            return False
    
    def add_custom_condition(self, condition: AlertCondition):
        """
        Adiciona uma condição de alerta personalizada.
        
        Args:
            condition: Nova condição de alerta
        """
        self.alert_conditions.append(condition)
        logger.info(f"Condição personalizada adicionada: {condition.name}")
    
    def test_email_connection(self) -> bool:
        """
        Testa a conexão com o servidor de email.
        
        Returns:
            bool: True se conexão for bem-sucedida
        """
        try:
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port) as server:
                if self.email_config.use_tls:
                    server.starttls(context=context)
                
                server.login(self.email_config.username, self.email_config.password)
            
            logger.info("Teste de conexão de email bem-sucedido")
            return True
            
        except Exception as e:
            logger.error(f"Erro no teste de conexão de email: {e}")
            return False