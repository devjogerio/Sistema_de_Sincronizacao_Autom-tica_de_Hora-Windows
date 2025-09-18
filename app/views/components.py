"""
Componentes visuais reutilizáveis para a interface.
Contém widgets e elementos de UI modulares.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from ..models.ntp_metrics import NTPMetrics


class MetricsChart:
    """
    Componente para exibição de gráficos de métricas NTP.
    
    Cria gráficos interativos para visualização de dados
    históricos de servidores NTP.
    """
    
    def __init__(self, parent, width: int = 800, height: int = 400):
        """
        Inicializa o componente de gráfico.
        
        Args:
            parent: Widget pai
            width: Largura do gráfico
            height: Altura do gráfico
        """
        self.parent = parent
        self.width = width
        self.height = height
        
        # Configuração da figura matplotlib
        self.figure = Figure(figsize=(width/100, height/100), dpi=100)
        self.figure.patch.set_facecolor('#f0f0f0')
        
        # Canvas para integração com tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        
        # Dados do gráfico
        self.metrics_data = []
        self.current_metric = 'response_time'
        
        self._setup_chart()
    
    def _setup_chart(self):
        """Configura o gráfico inicial."""
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#ffffff')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_title('Métricas NTP', fontsize=14, fontweight='bold')
        
        # Configurações de estilo
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#cccccc')
        self.ax.spines['bottom'].set_color('#cccccc')
        
        self.figure.tight_layout(pad=3.0)
    
    def update_data(self, metrics: List[NTPMetrics]):
        """
        Atualiza os dados do gráfico.
        
        Args:
            metrics: Lista de métricas para exibir
        """
        self.metrics_data = metrics
        self.refresh_chart()
    
    def set_metric_type(self, metric_type: str):
        """
        Define o tipo de métrica a ser exibida.
        
        Args:
            metric_type: Tipo de métrica ('response_time', 'offset', 'delay')
        """
        self.current_metric = metric_type
        self.refresh_chart()
    
    def refresh_chart(self):
        """Atualiza a visualização do gráfico."""
        self.ax.clear()
        self._setup_chart()
        
        if not self.metrics_data:
            self.ax.text(0.5, 0.5, 'Nenhum dado disponível', 
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=12, color='#666666')
            self.canvas.draw()
            return
        
        # Agrupa métricas por servidor
        servers_data = {}
        for metric in self.metrics_data:
            if metric.server not in servers_data:
                servers_data[metric.server] = []
            servers_data[metric.server].append(metric)
        
        # Cores para diferentes servidores
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # Plota dados de cada servidor
        for i, (server, server_metrics) in enumerate(servers_data.items()):
            if not server_metrics:
                continue
            
            # Ordena por timestamp
            server_metrics.sort(key=lambda m: m.timestamp)
            
            # Extrai dados para plotagem
            timestamps = [m.timestamp for m in server_metrics]
            values = []
            
            for metric in server_metrics:
                if self.current_metric == 'response_time':
                    values.append(metric.response_time)
                elif self.current_metric == 'offset':
                    values.append(abs(metric.offset))
                elif self.current_metric == 'delay':
                    values.append(metric.delay)
                else:
                    values.append(metric.response_time)
            
            # Plota linha do servidor
            color = colors[i % len(colors)]
            self.ax.plot(timestamps, values, 
                        label=server, color=color, linewidth=2, marker='o', markersize=4)
        
        # Configurações do gráfico
        metric_labels = {
            'response_time': 'Tempo de Resposta (s)',
            'offset': 'Offset Absoluto (s)',
            'delay': 'Delay (s)'
        }
        
        self.ax.set_ylabel(metric_labels.get(self.current_metric, 'Valor'))
        self.ax.set_xlabel('Timestamp')
        self.ax.set_title(f'Histórico - {metric_labels.get(self.current_metric, "Métricas")}')
        
        # Formata eixo X para timestamps
        self.figure.autofmt_xdate()
        
        # Adiciona legenda se houver múltiplos servidores
        if len(servers_data) > 1:
            self.ax.legend(loc='upper right', framealpha=0.9)
        
        self.canvas.draw()
    
    def pack(self, **kwargs):
        """Empacota o widget."""
        self.canvas_widget.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Posiciona o widget em grid."""
        self.canvas_widget.grid(**kwargs)


class StatusIndicator:
    """
    Componente para indicação visual de status.
    
    Exibe status de servidores com cores e ícones.
    """
    
    def __init__(self, parent):
        """
        Inicializa o indicador de status.
        
        Args:
            parent: Widget pai
        """
        self.parent = parent
        self.frame = ttk.Frame(parent)
        
        # Elementos visuais
        self.status_label = ttk.Label(self.frame, text="Status", font=('Arial', 12, 'bold'))
        self.status_label.pack(pady=5)
        
        self.indicators_frame = ttk.Frame(self.frame)
        self.indicators_frame.pack(fill='both', expand=True)
        
        self.indicators = {}
    
    def update_status(self, servers_status: Dict[str, Dict]):
        """
        Atualiza os indicadores de status.
        
        Args:
            servers_status: Dicionário com status dos servidores
        """
        # Remove indicadores antigos
        for widget in self.indicators_frame.winfo_children():
            widget.destroy()
        self.indicators.clear()
        
        # Cria novos indicadores
        for server, status in servers_status.items():
            self._create_server_indicator(server, status)
    
    def _create_server_indicator(self, server: str, status: Dict):
        """
        Cria indicador para um servidor específico.
        
        Args:
            server: Nome do servidor
            status: Status do servidor
        """
        # Frame do indicador
        indicator_frame = ttk.Frame(self.indicators_frame)
        indicator_frame.pack(fill='x', padx=5, pady=2)
        
        # Determina cor do status
        is_available = status.get('is_available', False)
        is_healthy = status.get('is_healthy', False)
        
        if is_available and is_healthy:
            status_color = '#4CAF50'  # Verde
            status_text = '●'
            status_desc = 'Saudável'
        elif is_available:
            status_color = '#FF9800'  # Laranja
            status_text = '●'
            status_desc = 'Disponível'
        else:
            status_color = '#F44336'  # Vermelho
            status_text = '●'
            status_desc = 'Indisponível'
        
        # Indicador visual
        status_indicator = tk.Label(indicator_frame, text=status_text, 
                                  fg=status_color, font=('Arial', 16))
        status_indicator.pack(side='left', padx=(0, 5))
        
        # Nome do servidor
        server_label = ttk.Label(indicator_frame, text=server, font=('Arial', 10, 'bold'))
        server_label.pack(side='left', padx=(0, 10))
        
        # Status descritivo
        desc_label = ttk.Label(indicator_frame, text=status_desc, font=('Arial', 9))
        desc_label.pack(side='left')
        
        # Métricas adicionais
        if 'response_time' in status:
            metrics_text = f"RT: {status['response_time']:.3f}s"
            if 'offset' in status:
                metrics_text += f" | Offset: {status['offset']:.3f}s"
            
            metrics_label = ttk.Label(indicator_frame, text=metrics_text, 
                                    font=('Arial', 8), foreground='#666666')
            metrics_label.pack(side='right')
        
        self.indicators[server] = {
            'frame': indicator_frame,
            'indicator': status_indicator,
            'server_label': server_label,
            'desc_label': desc_label
        }
    
    def pack(self, **kwargs):
        """Empacota o widget."""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Posiciona o widget em grid."""
        self.frame.grid(**kwargs)


class ServerTable:
    """
    Componente para exibição tabular de servidores.
    
    Mostra informações detalhadas dos servidores em formato de tabela.
    """
    
    def __init__(self, parent):
        """
        Inicializa a tabela de servidores.
        
        Args:
            parent: Widget pai
        """
        self.parent = parent
        
        # Frame principal
        self.frame = ttk.Frame(parent)
        
        # Título
        self.title_label = ttk.Label(self.frame, text="Servidores NTP", 
                                   font=('Arial', 12, 'bold'))
        self.title_label.pack(pady=(0, 10))
        
        # Configuração da tabela
        self.columns = ('servidor', 'status', 'resposta', 'offset', 'delay', 'stratum')
        self.tree = ttk.Treeview(self.frame, columns=self.columns, show='headings', height=10)
        
        # Configuração das colunas
        column_configs = {
            'servidor': {'text': 'Servidor', 'width': 150, 'anchor': 'w'},
            'status': {'text': 'Status', 'width': 100, 'anchor': 'center'},
            'resposta': {'text': 'Resposta (s)', 'width': 100, 'anchor': 'center'},
            'offset': {'text': 'Offset (s)', 'width': 100, 'anchor': 'center'},
            'delay': {'text': 'Delay (s)', 'width': 100, 'anchor': 'center'},
            'stratum': {'text': 'Stratum', 'width': 80, 'anchor': 'center'}
        }
        
        for col, config in column_configs.items():
            self.tree.heading(col, text=config['text'])
            self.tree.column(col, width=config['width'], anchor=config['anchor'])
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Tags para colorir linhas
        self.tree.tag_configure('healthy', background='#E8F5E8')
        self.tree.tag_configure('warning', background='#FFF3E0')
        self.tree.tag_configure('error', background='#FFEBEE')
    
    def update_data(self, metrics: List[NTPMetrics]):
        """
        Atualiza os dados da tabela.
        
        Args:
            metrics: Lista de métricas dos servidores
        """
        # Limpa dados existentes
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adiciona novos dados
        for metric in metrics:
            # Determina status e tag
            if metric.is_available:
                if metric.is_healthy():
                    status = "✅ Saudável"
                    tag = 'healthy'
                else:
                    status = "⚠️ Disponível"
                    tag = 'warning'
            else:
                status = "❌ Indisponível"
                tag = 'error'
            
            # Formata valores
            response_time = f"{metric.response_time:.3f}" if metric.is_available else "N/A"
            offset = f"{metric.offset:.3f}" if metric.is_available else "N/A"
            delay = f"{metric.delay:.3f}" if metric.is_available else "N/A"
            stratum = str(metric.stratum) if metric.is_available and metric.stratum > 0 else "N/A"
            
            # Insere linha na tabela
            self.tree.insert('', 'end', values=(
                metric.server,
                status,
                response_time,
                offset,
                delay,
                stratum
            ), tags=(tag,))
    
    def pack(self, **kwargs):
        """Empacota o widget."""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Posiciona o widget em grid."""
        self.frame.grid(**kwargs)