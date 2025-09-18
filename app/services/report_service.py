"""
Serviço de Geração de Relatórios
Responsável por criar relatórios em PDF com métricas e gráficos
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import io
import base64

from app.services.database_service import DatabaseService
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

class ReportService:
    """Serviço para geração de relatórios em PDF"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'exports')
        
        # Criar diretório de relatórios se não existir
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Configurar estilos
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12
        )
    
    async def generate_report(
        self,
        report_id: str,
        title: str,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        server_ids: Optional[List[int]] = None,
        include_charts: bool = True
    ) -> str:
        """
        Gerar relatório em PDF
        
        Args:
            report_id: ID único do relatório
            title: Título do relatório
            report_type: Tipo de relatório (summary, detailed, performance)
            period_start: Data de início do período
            period_end: Data de fim do período
            server_ids: IDs dos servidores (opcional)
            include_charts: Incluir gráficos no relatório
            
        Returns:
            Caminho do arquivo PDF gerado
        """
        try:
            logger.info(f"Gerando relatório {report_type}: {title}")
            
            # Definir nome do arquivo
            filename = f"relatorio_{report_id}.pdf"
            file_path = os.path.join(self.reports_dir, filename)
            
            # Criar documento PDF
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            story = []
            
            # Adicionar título
            story.append(Paragraph(title, self.title_style))
            story.append(Spacer(1, 12))
            
            # Adicionar informações do relatório
            info_data = [
                ['Tipo de Relatório:', report_type.title()],
                ['Período:', f"{period_start.strftime('%d/%m/%Y %H:%M')} - {period_end.strftime('%d/%m/%Y %H:%M')}"],
                ['Gerado em:', datetime.now().strftime('%d/%m/%Y %H:%M:%S')],
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # Gerar conteúdo baseado no tipo de relatório
            if report_type == 'summary':
                await self._add_summary_content(story, period_start, period_end, server_ids, include_charts)
            elif report_type == 'detailed':
                await self._add_detailed_content(story, period_start, period_end, server_ids, include_charts)
            elif report_type == 'performance':
                await self._add_performance_content(story, period_start, period_end, server_ids, include_charts)
            else:
                # Relatório genérico
                await self._add_generic_content(story, period_start, period_end, server_ids, include_charts)
            
            # Construir PDF
            doc.build(story)
            
            logger.info(f"Relatório gerado com sucesso: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            raise
    
    async def _add_summary_content(self, story, period_start, period_end, server_ids, include_charts):
        """Adicionar conteúdo do relatório resumido"""
        story.append(Paragraph("Resumo Executivo", self.heading_style))
        
        # Obter estatísticas gerais
        stats = self.db_service.get_period_summary(period_start, period_end, server_ids)
        
        # Tabela de resumo
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total de Servidores', str(stats.get('total_servers', 0))],
            ['Servidores Ativos', str(stats.get('active_servers', 0))],
            ['Total de Verificações', str(stats.get('total_checks', 0))],
            ['Verificações com Sucesso', str(stats.get('successful_checks', 0))],
            ['Taxa de Sucesso', f"{stats.get('success_rate', 0):.1f}%"],
            ['Tempo Médio de Resposta', f"{stats.get('avg_response_time', 0):.2f}ms"],
            ['Offset Médio', f"{stats.get('avg_offset', 0):.3f}s"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white])
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Adicionar gráfico se solicitado
        if include_charts:
            chart_path = await self._create_summary_chart(period_start, period_end, server_ids)
            if chart_path and os.path.exists(chart_path):
                story.append(Paragraph("Gráfico de Desempenho", self.heading_style))
                story.append(Image(chart_path, width=6*inch, height=4*inch))
                story.append(Spacer(1, 20))
    
    async def _add_detailed_content(self, story, period_start, period_end, server_ids, include_charts):
        """Adicionar conteúdo do relatório detalhado"""
        story.append(Paragraph("Relatório Detalhado", self.heading_style))
        
        # Obter dados detalhados por servidor
        servers_data = self.db_service.get_detailed_server_stats(period_start, period_end, server_ids)
        
        for server_data in servers_data:
            story.append(Paragraph(f"Servidor: {server_data['name']}", self.heading_style))
            
            # Tabela de métricas do servidor
            server_metrics = [
                ['Métrica', 'Valor'],
                ['Host', server_data['host']],
                ['Status', server_data['status']],
                ['Última Verificação', server_data['last_check'].strftime('%d/%m/%Y %H:%M') if server_data['last_check'] else 'N/A'],
                ['Total de Verificações', str(server_data['total_checks'])],
                ['Verificações com Sucesso', str(server_data['successful_checks'])],
                ['Taxa de Sucesso', f"{server_data['success_rate']:.1f}%"],
                ['Tempo Médio de Resposta', f"{server_data['avg_response_time']:.2f}ms"],
                ['Tempo Mín. de Resposta', f"{server_data['min_response_time']:.2f}ms"],
                ['Tempo Máx. de Resposta', f"{server_data['max_response_time']:.2f}ms"],
                ['Offset Médio', f"{server_data['avg_offset']:.3f}s"],
                ['Desvio Padrão do Offset', f"{server_data['std_offset']:.3f}s"],
            ]
            
            server_table = Table(server_metrics, colWidths=[3*inch, 2*inch])
            server_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightcyan, colors.white])
            ]))
            
            story.append(server_table)
            story.append(Spacer(1, 15))
        
        # Adicionar gráficos se solicitado
        if include_charts:
            chart_path = await self._create_detailed_chart(period_start, period_end, server_ids)
            if chart_path and os.path.exists(chart_path):
                story.append(Paragraph("Análise Temporal", self.heading_style))
                story.append(Image(chart_path, width=7*inch, height=5*inch))
                story.append(Spacer(1, 20))
    
    async def _add_performance_content(self, story, period_start, period_end, server_ids, include_charts):
        """Adicionar conteúdo do relatório de performance"""
        story.append(Paragraph("Análise de Performance", self.heading_style))
        
        # Obter dados de performance
        perf_data = self.db_service.get_performance_analysis(period_start, period_end, server_ids)
        
        # Análise de tendências
        story.append(Paragraph("Tendências de Performance", self.heading_style))
        
        trends_data = [
            ['Servidor', 'Tendência Tempo Resposta', 'Tendência Offset', 'Estabilidade'],
        ]
        
        for server_perf in perf_data:
            trends_data.append([
                server_perf['name'],
                server_perf['response_time_trend'],
                server_perf['offset_trend'],
                server_perf['stability_score']
            ])
        
        trends_table = Table(trends_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
        trends_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightsteelblue, colors.white])
        ]))
        
        story.append(trends_table)
        story.append(Spacer(1, 20))
        
        # Adicionar gráficos de performance
        if include_charts:
            chart_path = await self._create_performance_chart(period_start, period_end, server_ids)
            if chart_path and os.path.exists(chart_path):
                story.append(Paragraph("Gráficos de Performance", self.heading_style))
                story.append(Image(chart_path, width=7*inch, height=6*inch))
    
    async def _add_generic_content(self, story, period_start, period_end, server_ids, include_charts):
        """Adicionar conteúdo genérico"""
        story.append(Paragraph("Relatório de Monitoramento NTP", self.heading_style))
        
        # Adicionar resumo básico
        await self._add_summary_content(story, period_start, period_end, server_ids, include_charts)
    
    async def _create_summary_chart(self, period_start, period_end, server_ids):
        """Criar gráfico de resumo"""
        try:
            # Obter dados para o gráfico
            chart_data = self.db_service.get_chart_data_summary(period_start, period_end, server_ids)
            
            if not chart_data:
                return None
            
            # Criar gráfico com matplotlib
            plt.figure(figsize=(10, 6))
            
            # Gráfico de barras com taxa de sucesso por servidor
            servers = [d['name'] for d in chart_data]
            success_rates = [d['success_rate'] for d in chart_data]
            
            plt.bar(servers, success_rates, color='skyblue', edgecolor='navy')
            plt.title('Taxa de Sucesso por Servidor')
            plt.xlabel('Servidores')
            plt.ylabel('Taxa de Sucesso (%)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Salvar gráfico
            chart_path = os.path.join(self.reports_dir, f'chart_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            logger.error(f"Erro ao criar gráfico de resumo: {e}")
            return None
    
    async def _create_detailed_chart(self, period_start, period_end, server_ids):
        """Criar gráfico detalhado"""
        try:
            # Obter dados temporais
            time_data = self.db_service.get_time_series_data(period_start, period_end, server_ids)
            
            if not time_data:
                return None
            
            # Criar gráfico de linha temporal
            plt.figure(figsize=(12, 8))
            
            # Subplot para tempo de resposta
            plt.subplot(2, 1, 1)
            for server_id in set(d['server_id'] for d in time_data):
                server_data = [d for d in time_data if d['server_id'] == server_id]
                timestamps = [d['timestamp'] for d in server_data]
                response_times = [d['response_time'] for d in server_data]
                server_name = server_data[0]['server_name']
                
                plt.plot(timestamps, response_times, label=server_name, marker='o', markersize=2)
            
            plt.title('Tempo de Resposta ao Longo do Tempo')
            plt.xlabel('Tempo')
            plt.ylabel('Tempo de Resposta (ms)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Subplot para offset
            plt.subplot(2, 1, 2)
            for server_id in set(d['server_id'] for d in time_data):
                server_data = [d for d in time_data if d['server_id'] == server_id]
                timestamps = [d['timestamp'] for d in server_data]
                offsets = [d['offset'] for d in server_data]
                server_name = server_data[0]['server_name']
                
                plt.plot(timestamps, offsets, label=server_name, marker='o', markersize=2)
            
            plt.title('Offset ao Longo do Tempo')
            plt.xlabel('Tempo')
            plt.ylabel('Offset (s)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Salvar gráfico
            chart_path = os.path.join(self.reports_dir, f'chart_detailed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            logger.error(f"Erro ao criar gráfico detalhado: {e}")
            return None
    
    async def _create_performance_chart(self, period_start, period_end, server_ids):
        """Criar gráfico de performance"""
        try:
            # Obter dados de performance
            perf_data = self.db_service.get_performance_chart_data(period_start, period_end, server_ids)
            
            if not perf_data:
                return None
            
            # Criar gráfico combinado
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
            
            servers = [d['name'] for d in perf_data]
            
            # Gráfico 1: Tempo médio de resposta
            avg_response = [d['avg_response_time'] for d in perf_data]
            ax1.bar(servers, avg_response, color='lightcoral')
            ax1.set_title('Tempo Médio de Resposta')
            ax1.set_ylabel('Tempo (ms)')
            ax1.tick_params(axis='x', rotation=45)
            
            # Gráfico 2: Offset médio
            avg_offset = [d['avg_offset'] for d in perf_data]
            ax2.bar(servers, avg_offset, color='lightgreen')
            ax2.set_title('Offset Médio')
            ax2.set_ylabel('Offset (s)')
            ax2.tick_params(axis='x', rotation=45)
            
            # Gráfico 3: Taxa de sucesso
            success_rate = [d['success_rate'] for d in perf_data]
            ax3.bar(servers, success_rate, color='skyblue')
            ax3.set_title('Taxa de Sucesso')
            ax3.set_ylabel('Taxa (%)')
            ax3.tick_params(axis='x', rotation=45)
            
            # Gráfico 4: Estabilidade
            stability = [d['stability_score'] for d in perf_data]
            ax4.bar(servers, stability, color='gold')
            ax4.set_title('Pontuação de Estabilidade')
            ax4.set_ylabel('Pontuação')
            ax4.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Salvar gráfico
            chart_path = os.path.join(self.reports_dir, f'chart_performance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            logger.error(f"Erro ao criar gráfico de performance: {e}")
            return None