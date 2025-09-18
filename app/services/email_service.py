"""
Serviço para envio de emails e alertas.
Gerencia o envio de notificações por email.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List

from ..models.config_models import EmailConfig

logger = logging.getLogger(__name__)


class EmailService:
    """
    Serviço para envio de emails e alertas.
    
    Gerencia a configuração SMTP e envio de
    notificações por email para alertas do sistema.
    """
    
    def __init__(self, email_config: EmailConfig = None):
        """
        Inicializa o serviço de email.
        
        Args:
            email_config: Configuração de email
        """
        self.email_config = email_config or EmailConfig()
        logger.info("Serviço de email inicializado")
    
    def configure(self, email_config: EmailConfig):
        """
        Configura o serviço de email.
        
        Args:
            email_config: Configuração de email
        """
        self.email_config = email_config
        logger.info("Serviço de email configurado")
    
    def update_config(self, email_config: EmailConfig):
        """
        Atualiza a configuração de email.
        
        Args:
            email_config: Nova configuração de email
        """
        self.email_config = email_config
        logger.info("Configuração de email atualizada")
    
    def test_connection(self) -> bool:
        """
        Testa a conexão SMTP.
        
        Returns:
            bool: True se conectou com sucesso, False caso contrário
        """
        if not self.email_config.enabled:
            logger.info("Serviço de email desabilitado")
            return False
        
        try:
            with self._get_smtp_connection() as smtp:
                smtp.noop()  # Comando simples para testar conexão
            
            logger.info("Conexão SMTP testada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar conexão SMTP: {e}")
            return False
    
    def send_alert_email(self, alert: Dict) -> bool:
        """
        Envia email de alerta.
        
        Args:
            alert: Dados do alerta
            
        Returns:
            bool: True se enviou com sucesso, False caso contrário
        """
        if not self.email_config.enabled:
            logger.debug("Envio de email desabilitado")
            return False
        
        if not self.email_config.to_addresses:
            logger.warning("Nenhum destinatário configurado para alertas")
            return False
        
        try:
            subject = f"[NTP Monitor] Alerta: {alert['type'].title()}"
            body = self._create_alert_body(alert)
            
            return self._send_email(
                subject=subject,
                body=body,
                recipients=self.email_config.to_addresses
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar email de alerta: {e}")
            return False
    
    def send_status_report(self, status_data: Dict) -> bool:
        """
        Envia relatório de status do sistema.
        
        Args:
            status_data: Dados do status do sistema
            
        Returns:
            bool: True se enviou com sucesso, False caso contrário
        """
        if not self.email_config.enabled:
            logger.debug("Envio de email desabilitado")
            return False
        
        try:
            subject = "[NTP Monitor] Relatório de Status"
            body = self._create_status_report_body(status_data)
            
            return self._send_email(
                subject=subject,
                body=body,
                recipients=self.email_config.to_addresses
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar relatório de status: {e}")
            return False
    
    def _send_email(self, subject: str, body: str, recipients: List[str]) -> bool:
        """
        Envia email usando configuração SMTP.
        
        Args:
            subject: Assunto do email
            body: Corpo do email
            recipients: Lista de destinatários
            
        Returns:
            bool: True se enviou com sucesso, False caso contrário
        """
        try:
            # Cria mensagem
            msg = MIMEMultipart()
            msg['From'] = self.email_config.from_address
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Adiciona corpo da mensagem
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Envia email
            with self._get_smtp_connection() as smtp:
                smtp.send_message(msg)
            
            logger.info(f"Email enviado com sucesso para {len(recipients)} destinatários")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
    
    def _get_smtp_connection(self):
        """
        Cria conexão SMTP baseada na configuração.
        
        Returns:
            smtplib.SMTP: Conexão SMTP configurada
        """
        try:
            # Cria conexão SMTP
            smtp = smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port)
            
            # Habilita TLS se configurado
            if self.email_config.use_tls:
                smtp.starttls()
            
            # Autentica se credenciais fornecidas
            if self.email_config.username and self.email_config.password:
                smtp.login(self.email_config.username, self.email_config.password)
            
            return smtp
            
        except Exception as e:
            logger.error(f"Erro ao criar conexão SMTP: {e}")
            raise
    
    def _create_alert_body(self, alert: Dict) -> str:
        """
        Cria corpo do email de alerta.
        
        Args:
            alert: Dados do alerta
            
        Returns:
            str: Corpo do email em HTML
        """
        severity_colors = {
            'low': '#FFA500',      # Laranja
            'medium': '#FF6B35',   # Vermelho claro
            'high': '#FF0000'      # Vermelho
        }
        
        severity_color = severity_colors.get(alert['severity'], '#808080')
        metric = alert.get('metric')
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: {severity_color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }}
                .metric-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                .metric-table th, .metric-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .metric-table th {{ background-color: #f2f2f2; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 Alerta NTP Monitor</h2>
                <p><strong>Severidade:</strong> {alert['severity'].upper()}</p>
            </div>
            
            <div class="content">
                <h3>Detalhes do Alerta</h3>
                <p><strong>Tipo:</strong> {alert['type'].replace('_', ' ').title()}</p>
                <p><strong>Servidor:</strong> {alert['server']}</p>
                <p><strong>Mensagem:</strong> {alert['message']}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        """
        
        # Adiciona detalhes da métrica se disponível
        if metric:
            html_body += f"""
                <h3>Métricas do Servidor</h3>
                <table class="metric-table">
                    <tr><th>Métrica</th><th>Valor</th></tr>
                    <tr><td>Disponível</td><td>{'✅ Sim' if metric.is_available else '❌ Não'}</td></tr>
                    <tr><td>Tempo de Resposta</td><td>{metric.response_time:.3f}s</td></tr>
                    <tr><td>Offset</td><td>{metric.offset:.3f}s</td></tr>
                    <tr><td>Delay</td><td>{metric.delay:.3f}s</td></tr>
                    <tr><td>Stratum</td><td>{metric.stratum}</td></tr>
                    <tr><td>Precisão</td><td>{metric.precision:.6f}s</td></tr>
                </table>
            """
            
            if metric.error_message:
                html_body += f"""
                    <h3>Erro</h3>
                    <p style="color: red; font-family: monospace; background-color: #f8f8f8; padding: 10px; border-radius: 3px;">
                        {metric.error_message}
                    </p>
                """
        
        html_body += """
            </div>
            
            <div class="footer">
                <p>Este é um alerta automático do sistema NTP Monitor.</p>
                <p>Para mais informações, acesse o dashboard do sistema.</p>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def _create_status_report_body(self, status_data: Dict) -> str:
        """
        Cria corpo do email de relatório de status.
        
        Args:
            status_data: Dados do status do sistema
            
        Returns:
            str: Corpo do email em HTML
        """
        health_analysis = status_data.get('health_analysis', {})
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }}
                .status-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                .status-table th, .status-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .status-table th {{ background-color: #f2f2f2; }}
                .good {{ color: #4CAF50; font-weight: bold; }}
                .warning {{ color: #FF9800; font-weight: bold; }}
                .error {{ color: #F44336; font-weight: bold; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📊 Relatório de Status - NTP Monitor</h2>
                <p>Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
            
            <div class="content">
                <h3>Status Geral do Sistema</h3>
                <table class="status-table">
                    <tr><th>Métrica</th><th>Valor</th></tr>
                    <tr><td>Monitoramento Ativo</td><td>{'✅ Sim' if status_data.get('monitoring_active') else '❌ Não'}</td></tr>
                    <tr><td>Total de Servidores</td><td>{status_data.get('total_servers', 0)}</td></tr>
                    <tr><td>Servidores Habilitados</td><td>{status_data.get('enabled_servers', 0)}</td></tr>
                    <tr><td>Última Verificação</td><td>{status_data.get('last_check', 'N/A')}</td></tr>
                </table>
                
                <h3>Análise de Saúde dos Servidores</h3>
                <table class="status-table">
                    <tr><th>Métrica</th><th>Valor</th></tr>
                    <tr><td>Servidores Disponíveis</td><td>{health_analysis.get('available_servers', 0)}</td></tr>
                    <tr><td>Taxa de Disponibilidade</td><td>{health_analysis.get('availability_percentage', 0):.1f}%</td></tr>
                    <tr><td>Servidores Saudáveis</td><td>{health_analysis.get('healthy_servers', 0)}</td></tr>
                    <tr><td>Taxa de Saúde</td><td>{health_analysis.get('health_percentage', 0):.1f}%</td></tr>
                    <tr><td>Tempo Médio de Resposta</td><td>{health_analysis.get('average_response_time', 0):.3f}s</td></tr>
                    <tr><td>Offset Médio</td><td>{health_analysis.get('average_offset', 0):.3f}s</td></tr>
                </table>
        """
        
        # Adiciona status do banco de dados se disponível
        db_status = status_data.get('database_status', {})
        if db_status:
            html_body += f"""
                <h3>Status do Banco de Dados</h3>
                <table class="status-table">
                    <tr><th>Métrica</th><th>Valor</th></tr>
                    <tr><td>Status</td><td>{db_status.get('status', 'N/A').title()}</td></tr>
                    <tr><td>Total de Registros</td><td>{db_status.get('total_records', 0):,}</td></tr>
                    <tr><td>Registros (24h)</td><td>{db_status.get('recent_records_24h', 0):,}</td></tr>
                    <tr><td>Tamanho do Arquivo</td><td>{db_status.get('file_size_mb', 0):.2f} MB</td></tr>
                </table>
            """
        
        html_body += """
            </div>
            
            <div class="footer">
                <p>Este é um relatório automático do sistema NTP Monitor.</p>
                <p>Para mais detalhes, acesse o dashboard do sistema.</p>
            </div>
        </body>
        </html>
        """
        
        return html_body