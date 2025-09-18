"""
View principal do dashboard NTP Monitor.
Interface gráfica principal da aplicação.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from datetime import datetime
from typing import List, Dict, Optional, Callable

from .components import MetricsChart, StatusIndicator, ServerTable
from ..models.ntp_metrics import NTPMetrics

logger = logging.getLogger(__name__)


class DashboardView:
    """
    View principal do dashboard NTP Monitor.
    
    Interface gráfica que exibe métricas, status e
    controles para o sistema de monitoramento NTP.
    """
    
    def __init__(self, title: str = "NTP Monitor Dashboard"):
        """
        Inicializa a view do dashboard.
        
        Args:
            title: Título da janela
        """
        self.title = title
        self.root = None
        self.is_running = False
        
        # Callbacks para interação com controlador
        self.callbacks = {
            'start_monitoring': None,
            'stop_monitoring': None,
            'refresh_data': None,
            'export_data': None
        }
        
        # Componentes da interface
        self.metrics_chart = None
        self.status_indicator = None
        self.server_table = None
        
        # Variáveis de controle (serão criadas no setup_ui)
        self.monitoring_status = None
        self.last_update = None
        self.selected_metric = None
        
        # Dados atuais
        self.current_metrics = []
        
        logger.info("Dashboard view inicializada")
    
    def setup_ui(self):
        """Configura a interface gráfica."""
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Cria variáveis de controle após criar root
        self.monitoring_status = tk.StringVar(value="Parado")
        self.last_update = tk.StringVar(value="Nunca")
        self.selected_metric = tk.StringVar(value="response_time")
        
        # Configuração de estilo
        self._setup_styles()
        
        # Layout principal
        self._create_main_layout()
        
        # Menu
        self._create_menu()
        
        # Barra de status
        self._create_status_bar()
        
        # Configurações da janela
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        logger.info("Interface gráfica configurada")
    
    def _setup_styles(self):
        """Configura estilos da interface."""
        style = ttk.Style()
        
        # Tema moderno
        try:
            style.theme_use('clam')
        except:
            pass  # Usa tema padrão se 'clam' não estiver disponível
        
        # Cores personalizadas
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 10))
        
        # Botões
        style.configure('Action.TButton', font=('Arial', 10, 'bold'))
        style.map('Action.TButton',
                 background=[('active', '#4CAF50')])
    
    def _create_main_layout(self):
        """Cria o layout principal da interface."""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Título
        title_label = ttk.Label(main_frame, text="NTP Monitor Dashboard", 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Frame de controles
        self._create_controls_frame(main_frame)
        
        # Notebook para abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True, pady=(10, 0))
        
        # Aba de visão geral
        self._create_overview_tab()
        
        # Aba de gráficos
        self._create_charts_tab()
        
        # Aba de detalhes
        self._create_details_tab()
    
    def _create_controls_frame(self, parent):
        """
        Cria frame com controles principais.
        
        Args:
            parent: Widget pai
        """
        controls_frame = ttk.LabelFrame(parent, text="Controles", padding=10)
        controls_frame.pack(fill='x', pady=(0, 10))
        
        # Frame esquerdo - botões de ação
        left_frame = ttk.Frame(controls_frame)
        left_frame.pack(side='left', fill='x', expand=True)
        
        # Botões de controle
        self.start_button = ttk.Button(left_frame, text="▶ Iniciar Monitoramento",
                                      command=self._on_start_monitoring,
                                      style='Action.TButton')
        self.start_button.pack(side='left', padx=(0, 10))
        
        self.stop_button = ttk.Button(left_frame, text="⏹ Parar Monitoramento",
                                     command=self._on_stop_monitoring,
                                     state='disabled')
        self.stop_button.pack(side='left', padx=(0, 10))
        
        self.refresh_button = ttk.Button(left_frame, text="🔄 Atualizar",
                                        command=self._on_refresh_data)
        self.refresh_button.pack(side='left', padx=(0, 10))
        
        # Frame direito - informações de status
        right_frame = ttk.Frame(controls_frame)
        right_frame.pack(side='right')
        
        # Status do monitoramento
        ttk.Label(right_frame, text="Status:").pack(side='left', padx=(0, 5))
        status_label = ttk.Label(right_frame, textvariable=self.monitoring_status,
                                style='Status.TLabel')
        status_label.pack(side='left', padx=(0, 20))
        
        # Última atualização
        ttk.Label(right_frame, text="Última atualização:").pack(side='left', padx=(0, 5))
        update_label = ttk.Label(right_frame, textvariable=self.last_update,
                                style='Status.TLabel')
        update_label.pack(side='left')
    
    def _create_overview_tab(self):
        """Cria aba de visão geral."""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="📊 Visão Geral")
        
        # Frame superior - indicadores de status
        status_frame = ttk.LabelFrame(overview_frame, text="Status dos Servidores", padding=10)
        status_frame.pack(fill='x', padx=10, pady=10)
        
        self.status_indicator = StatusIndicator(status_frame)
        self.status_indicator.pack(fill='both', expand=True)
        
        # Frame inferior - resumo estatístico
        stats_frame = ttk.LabelFrame(overview_frame, text="Estatísticas Gerais", padding=10)
        stats_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self._create_stats_display(stats_frame)
    
    def _create_charts_tab(self):
        """Cria aba de gráficos."""
        charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(charts_frame, text="📈 Gráficos")
        
        # Controles do gráfico
        controls_frame = ttk.Frame(charts_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(controls_frame, text="Métrica:").pack(side='left', padx=(0, 5))
        
        metric_combo = ttk.Combobox(controls_frame, textvariable=self.selected_metric,
                                   values=['response_time', 'offset', 'delay'],
                                   state='readonly', width=15)
        metric_combo.pack(side='left', padx=(0, 10))
        metric_combo.bind('<<ComboboxSelected>>', self._on_metric_changed)
        
        # Gráfico
        chart_frame = ttk.LabelFrame(charts_frame, text="Histórico de Métricas", padding=10)
        chart_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.metrics_chart = MetricsChart(chart_frame, width=800, height=400)
        self.metrics_chart.pack(fill='both', expand=True)
    
    def _create_details_tab(self):
        """Cria aba de detalhes."""
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="📋 Detalhes")
        
        # Tabela de servidores
        table_frame = ttk.LabelFrame(details_frame, text="Detalhes dos Servidores", padding=10)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.server_table = ServerTable(table_frame)
        self.server_table.pack(fill='both', expand=True)
    
    def _create_stats_display(self, parent):
        """
        Cria display de estatísticas.
        
        Args:
            parent: Widget pai
        """
        # Grid de estatísticas
        stats_grid = ttk.Frame(parent)
        stats_grid.pack(fill='both', expand=True)
        
        # Configuração do grid
        for i in range(3):
            stats_grid.columnconfigure(i, weight=1)
        
        # Variáveis para estatísticas
        self.stats_vars = {
            'total_servers': tk.StringVar(value="0"),
            'available_servers': tk.StringVar(value="0"),
            'healthy_servers': tk.StringVar(value="0"),
            'avg_response_time': tk.StringVar(value="0.000s"),
            'avg_offset': tk.StringVar(value="0.000s"),
            'availability_percentage': tk.StringVar(value="0.0%")
        }
        
        # Cards de estatísticas
        self._create_stat_card(stats_grid, "Total de Servidores", 
                              self.stats_vars['total_servers'], 0, 0, '#2196F3')
        self._create_stat_card(stats_grid, "Servidores Disponíveis", 
                              self.stats_vars['available_servers'], 0, 1, '#4CAF50')
        self._create_stat_card(stats_grid, "Servidores Saudáveis", 
                              self.stats_vars['healthy_servers'], 0, 2, '#8BC34A')
        
        self._create_stat_card(stats_grid, "Tempo Médio de Resposta", 
                              self.stats_vars['avg_response_time'], 1, 0, '#FF9800')
        self._create_stat_card(stats_grid, "Offset Médio", 
                              self.stats_vars['avg_offset'], 1, 1, '#9C27B0')
        self._create_stat_card(stats_grid, "Taxa de Disponibilidade", 
                              self.stats_vars['availability_percentage'], 1, 2, '#00BCD4')
    
    def _create_stat_card(self, parent, title: str, variable: tk.StringVar, 
                         row: int, col: int, color: str):
        """
        Cria card de estatística.
        
        Args:
            parent: Widget pai
            title: Título da estatística
            variable: Variável com o valor
            row: Linha no grid
            col: Coluna no grid
            color: Cor do card
        """
        card_frame = tk.Frame(parent, bg=color, relief='raised', bd=2)
        card_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        
        # Título
        title_label = tk.Label(card_frame, text=title, bg=color, fg='white',
                              font=('Arial', 10, 'bold'))
        title_label.pack(pady=(10, 5))
        
        # Valor
        value_label = tk.Label(card_frame, textvariable=variable, bg=color, fg='white',
                              font=('Arial', 16, 'bold'))
        value_label.pack(pady=(0, 10))
    
    def _create_menu(self):
        """Cria menu da aplicação."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Exportar Dados", command=self._on_export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self._on_closing)
        
        # Menu Visualizar
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualizar", menu=view_menu)
        view_menu.add_command(label="Atualizar", command=self._on_refresh_data)
        view_menu.add_separator()
        view_menu.add_command(label="Limpar Dados", command=self._on_clear_data)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self._show_about)
    
    def _create_status_bar(self):
        """Cria barra de status."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side='bottom', fill='x')
        
        # Separador
        ttk.Separator(self.status_bar, orient='horizontal').pack(fill='x')
        
        # Status frame
        status_frame = ttk.Frame(self.status_bar)
        status_frame.pack(fill='x', padx=5, pady=2)
        
        # Informações de status
        self.status_text = tk.StringVar(value="Pronto")
        status_label = ttk.Label(status_frame, textvariable=self.status_text)
        status_label.pack(side='left')
        
        # Timestamp
        self.timestamp_text = tk.StringVar(value="")
        timestamp_label = ttk.Label(status_frame, textvariable=self.timestamp_text)
        timestamp_label.pack(side='right')
    
    def set_callback(self, event: str, callback: Callable):
        """
        Define callback para eventos da interface.
        
        Args:
            event: Nome do evento
            callback: Função callback
        """
        if event in self.callbacks:
            self.callbacks[event] = callback
        else:
            logger.warning(f"Evento desconhecido: {event}")
    
    def update_metrics(self, metrics: List[NTPMetrics]):
        """
        Atualiza métricas na interface.
        
        Args:
            metrics: Lista de métricas
        """
        self.current_metrics = metrics
        
        # Atualiza componentes
        if self.metrics_chart:
            self.metrics_chart.update_data(metrics)
        
        if self.server_table:
            self.server_table.update_data(metrics)
        
        # Atualiza indicadores de status
        if self.status_indicator:
            servers_status = {}
            for metric in metrics:
                servers_status[metric.server] = {
                    'is_available': metric.is_available,
                    'is_healthy': metric.is_healthy(),
                    'response_time': metric.response_time,
                    'offset': metric.offset
                }
            self.status_indicator.update_status(servers_status)
        
        # Atualiza estatísticas
        self._update_statistics(metrics)
        
        # Atualiza timestamp
        self.last_update.set(datetime.now().strftime("%H:%M:%S"))
        self.timestamp_text.set(f"Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _update_statistics(self, metrics: List[NTPMetrics]):
        """
        Atualiza estatísticas na interface.
        
        Args:
            metrics: Lista de métricas
        """
        if not metrics:
            return
        
        total_servers = len(metrics)
        available_servers = sum(1 for m in metrics if m.is_available)
        healthy_servers = sum(1 for m in metrics if m.is_available and m.is_healthy())
        
        # Calcula médias apenas para servidores disponíveis
        available_metrics = [m for m in metrics if m.is_available]
        
        avg_response_time = 0.0
        avg_offset = 0.0
        
        if available_metrics:
            avg_response_time = sum(m.response_time for m in available_metrics) / len(available_metrics)
            avg_offset = sum(abs(m.offset) for m in available_metrics) / len(available_metrics)
        
        availability_percentage = (available_servers / total_servers) * 100 if total_servers > 0 else 0.0
        
        # Atualiza variáveis
        self.stats_vars['total_servers'].set(str(total_servers))
        self.stats_vars['available_servers'].set(str(available_servers))
        self.stats_vars['healthy_servers'].set(str(healthy_servers))
        self.stats_vars['avg_response_time'].set(f"{avg_response_time:.3f}s")
        self.stats_vars['avg_offset'].set(f"{avg_offset:.3f}s")
        self.stats_vars['availability_percentage'].set(f"{availability_percentage:.1f}%")
    
    def set_monitoring_status(self, is_monitoring: bool):
        """
        Atualiza status do monitoramento.
        
        Args:
            is_monitoring: True se está monitorando, False caso contrário
        """
        if is_monitoring:
            self.monitoring_status.set("🟢 Ativo")
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.status_text.set("Monitoramento ativo")
        else:
            self.monitoring_status.set("🔴 Parado")
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.status_text.set("Monitoramento parado")
    
    def show_message(self, title: str, message: str, msg_type: str = 'info'):
        """
        Exibe mensagem para o usuário.
        
        Args:
            title: Título da mensagem
            message: Conteúdo da mensagem
            msg_type: Tipo da mensagem ('info', 'warning', 'error')
        """
        if msg_type == 'error':
            messagebox.showerror(title, message)
        elif msg_type == 'warning':
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)
    
    def run(self):
        """Inicia a interface gráfica."""
        if not self.root:
            self.setup_ui()
        
        self.is_running = True
        logger.info("Iniciando interface gráfica")
        self.root.mainloop()
    
    def close(self):
        """Fecha a interface gráfica."""
        if self.root:
            self.root.quit()
            self.root.destroy()
        self.is_running = False
        logger.info("Interface gráfica fechada")
    
    # Event handlers
    def _on_start_monitoring(self):
        """Handler para iniciar monitoramento."""
        if self.callbacks['start_monitoring']:
            self.callbacks['start_monitoring']()
    
    def _on_stop_monitoring(self):
        """Handler para parar monitoramento."""
        if self.callbacks['stop_monitoring']:
            self.callbacks['stop_monitoring']()
    
    def _on_refresh_data(self):
        """Handler para atualizar dados."""
        if self.callbacks['refresh_data']:
            self.callbacks['refresh_data']()
    
    def _on_export_data(self):
        """Handler para exportar dados."""
        if self.callbacks['export_data']:
            self.callbacks['export_data']()
    
    def _on_metric_changed(self, event):
        """Handler para mudança de métrica no gráfico."""
        if self.metrics_chart:
            self.metrics_chart.set_metric_type(self.selected_metric.get())
    
    def _on_clear_data(self):
        """Handler para limpar dados."""
        self.current_metrics = []
        if self.metrics_chart:
            self.metrics_chart.update_data([])
        if self.server_table:
            self.server_table.update_data([])
        if self.status_indicator:
            self.status_indicator.update_status({})
    
    def _show_about(self):
        """Exibe diálogo sobre a aplicação."""
        about_text = """
NTP Monitor Dashboard v1.0

Sistema de monitoramento de servidores NTP
com interface gráfica moderna e intuitiva.

Desenvolvido com arquitetura MVC para
máxima modularidade e manutenibilidade.

© 2024 - NTP Monitor
        """
        messagebox.showinfo("Sobre", about_text.strip())
    
    def _on_closing(self):
        """Handler para fechamento da janela."""
        if messagebox.askokcancel("Sair", "Deseja realmente sair da aplicação?"):
            self.close()