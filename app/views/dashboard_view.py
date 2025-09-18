"""
View principal do dashboard NTP Monitor.
Interface gráfica principal da aplicação usando CustomTkinter.
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import logging
from datetime import datetime
from typing import List, Dict, Optional, Callable

from .components import MetricsChart, StatusIndicator, ServerTable
from ..models.ntp_metrics import NTPMetrics

logger = logging.getLogger(__name__)

# Configuração do tema CustomTkinter
ctk.set_appearance_mode("system")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green


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
        """Configura a interface gráfica usando CustomTkinter."""
        self.root = ctk.CTk()
        self.root.title(self.title)
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Cria variáveis de controle após criar root
        self.monitoring_status = ctk.StringVar(value="Parado")
        self.last_update = ctk.StringVar(value="Nunca")
        self.selected_metric = ctk.StringVar(value="response_time")
        
        # Layout principal
        self._create_main_layout()
        
        # Menu
        self._create_menu()
        
        # Barra de status
        self._create_status_bar()
        
        # Configurações da janela
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        logger.info("Interface gráfica configurada")
    def _create_main_layout(self):
        """Cria o layout principal da interface usando CustomTkinter."""
        # Frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(main_frame, text="NTP Monitor Dashboard", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(10, 20))
        
        # Frame de controles
        self._create_controls_frame(main_frame)
        
        # Tabview para abas (substitui Notebook)
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill='both', expand=True, pady=(10, 0))
        
        # Aba de visão geral
        self._create_overview_tab()
        
        # Aba de gráficos
        self._create_charts_tab()
        
        # Aba de detalhes
        self._create_details_tab()
    
    def _create_controls_frame(self, parent):
        """
        Cria frame com controles principais usando CustomTkinter.
        
        Args:
            parent: Widget pai
        """
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.pack(fill='x', pady=(0, 10), padx=10)
        
        # Frame interno para organização
        inner_frame = ctk.CTkFrame(controls_frame)
        inner_frame.pack(fill='x', padx=10, pady=10)
        
        # Frame esquerdo - botões de ação
        left_frame = ctk.CTkFrame(inner_frame)
        left_frame.pack(side='left', fill='x', expand=True)
        
        # Botões de controle
        self.start_button = ctk.CTkButton(left_frame, text="▶ Iniciar Monitoramento",
                                         command=self._on_start_monitoring,
                                         fg_color="green", hover_color="darkgreen")
        self.start_button.pack(side='left', padx=(10, 10), pady=10)
        
        self.stop_button = ctk.CTkButton(left_frame, text="⏹ Parar Monitoramento",
                                        command=self._on_stop_monitoring,
                                        state='disabled',
                                        fg_color="red", hover_color="darkred")
        self.stop_button.pack(side='left', padx=(0, 10), pady=10)
        
        self.refresh_button = ctk.CTkButton(left_frame, text="🔄 Atualizar",
                                           command=self._on_refresh_data)
        self.refresh_button.pack(side='left', padx=(0, 10), pady=10)
        
        # Frame direito - informações de status
        right_frame = ctk.CTkFrame(inner_frame)
        right_frame.pack(side='right', padx=10, pady=10)
        
        # Status do monitoramento
        ctk.CTkLabel(right_frame, text="Status:").pack(side='left', padx=(10, 5), pady=10)
        status_label = ctk.CTkLabel(right_frame, textvariable=self.monitoring_status,
                                   font=ctk.CTkFont(weight="bold"))
        status_label.pack(side='left', padx=(0, 20), pady=10)
        
        # Última atualização
        ctk.CTkLabel(right_frame, text="Última atualização:").pack(side='left', padx=(0, 5), pady=10)
        update_label = ctk.CTkLabel(right_frame, textvariable=self.last_update)
        update_label.pack(side='left', padx=(0, 10), pady=10)
    
    def _create_overview_tab(self):
        """Cria aba de visão geral usando CustomTkinter."""
        # Adiciona aba ao tabview
        self.tabview.add("📊 Visão Geral")
        overview_frame = self.tabview.tab("📊 Visão Geral")
        
        # Frame superior - indicadores de status
        status_frame = ctk.CTkFrame(overview_frame)
        status_frame.pack(fill='x', padx=10, pady=10)
        
        status_title = ctk.CTkLabel(status_frame, text="Status dos Servidores",
                                   font=ctk.CTkFont(size=14, weight="bold"))
        status_title.pack(pady=(10, 5))
        
        self.status_indicator = StatusIndicator(status_frame)
        self.status_indicator.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Frame inferior - resumo estatístico
        stats_frame = ctk.CTkFrame(overview_frame)
        stats_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        stats_title = ctk.CTkLabel(stats_frame, text="Estatísticas Gerais",
                                  font=ctk.CTkFont(size=14, weight="bold"))
        stats_title.pack(pady=(10, 5))
        
        self._create_stats_display(stats_frame)
    
    def _create_charts_tab(self):
        """Cria aba de gráficos usando CustomTkinter."""
        # Adiciona aba ao tabview
        self.tabview.add("📈 Gráficos")
        charts_frame = self.tabview.tab("📈 Gráficos")
        
        # Controles do gráfico
        controls_frame = ctk.CTkFrame(charts_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)
        
        ctk.CTkLabel(controls_frame, text="Métrica:").pack(side='left', padx=(10, 5), pady=10)
        
        metric_combo = ctk.CTkComboBox(controls_frame, variable=self.selected_metric,
                                      values=['response_time', 'offset', 'delay'],
                                      state='readonly', width=150,
                                      command=self._on_metric_changed)
        metric_combo.pack(side='left', padx=(0, 10), pady=10)
        
        # Gráfico
        chart_frame = ctk.CTkFrame(charts_frame)
        chart_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        chart_title = ctk.CTkLabel(chart_frame, text="Histórico de Métricas",
                                  font=ctk.CTkFont(size=14, weight="bold"))
        chart_title.pack(pady=(10, 5))
        
        self.metrics_chart = MetricsChart(chart_frame, width=800, height=400)
        self.metrics_chart.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    
    def _create_details_tab(self):
        """Cria aba de detalhes usando CustomTkinter."""
        # Adiciona aba ao tabview
        self.tabview.add("📋 Detalhes")
        details_frame = self.tabview.tab("📋 Detalhes")
        
        # Tabela de servidores
        table_frame = ctk.CTkFrame(details_frame)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        table_title = ctk.CTkLabel(table_frame, text="Detalhes dos Servidores",
                                  font=ctk.CTkFont(size=14, weight="bold"))
        table_title.pack(pady=(10, 5))
        
        self.server_table = ServerTable(table_frame)
        self.server_table.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    
    def _create_stats_display(self, parent):
        """
        Cria display de estatísticas usando CustomTkinter.
        
        Args:
            parent: Widget pai
        """
        # Grid de estatísticas
        stats_grid = ctk.CTkFrame(parent)
        stats_grid.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Configuração do grid
        for i in range(3):
            stats_grid.columnconfigure(i, weight=1)
        
        # Variáveis para estatísticas
        self.stats_vars = {
            'total_servers': ctk.StringVar(value="0"),
            'available_servers': ctk.StringVar(value="0"),
            'healthy_servers': ctk.StringVar(value="0"),
            'avg_response_time': ctk.StringVar(value="0.000s"),
            'avg_offset': ctk.StringVar(value="0.000s"),
            'availability_percentage': ctk.StringVar(value="0.0%")
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
    
    def _create_stat_card(self, parent, title: str, variable: ctk.StringVar, 
                         row: int, col: int, color: str):
        """
        Cria card de estatística usando CustomTkinter.
        
        Args:
            parent: Widget pai
            title: Título da estatística
            variable: Variável com o valor
            row: Linha no grid
            col: Coluna no grid
            color: Cor do card
        """
        # Frame do card
        card_frame = ctk.CTkFrame(parent)
        card_frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Título
        title_label = ctk.CTkLabel(card_frame, text=title,
                                  font=ctk.CTkFont(size=12, weight="bold"))
        title_label.pack(pady=(10, 5))
        
        # Valor
        value_label = ctk.CTkLabel(card_frame, textvariable=variable,
                                  font=ctk.CTkFont(size=16, weight="bold"),
                                  text_color=color)
        value_label.pack(pady=(0, 10))
    
    def _create_menu(self):
        """Cria menu da aplicação usando CustomTkinter (removido - não suportado)."""
        # CustomTkinter não suporta menus nativos
        # Funcionalidades de menu podem ser implementadas com botões se necessário
        pass
    
    def _create_status_bar(self):
        """Cria barra de status usando CustomTkinter."""
        status_frame = ctk.CTkFrame(self.root)
        status_frame.pack(side='bottom', fill='x', padx=5, pady=5)
        
        # Status da aplicação
        self.status_text = ctk.StringVar(value="Pronto")
        status_label = ctk.CTkLabel(status_frame, textvariable=self.status_text,
                                   font=ctk.CTkFont(size=10))
        status_label.pack(side='left', padx=10, pady=5)
    
    def set_callback(self, event: str, callback: Callable):
        """
        Define callback para evento.
        
        Args:
            event: Nome do evento
            callback: Função callback
        """
        if event in self.callbacks:
            self.callbacks[event] = callback
            logger.debug(f"Callback definido para evento: {event}")
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
            self.start_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
            self.status_text.set("Monitoramento ativo")
        else:
            self.monitoring_status.set("🔴 Inativo")
            self.start_button.configure(state='normal')
            self.stop_button.configure(state='disabled')
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
    
    def _on_metric_changed(self, value):
        """Handler para mudança de métrica no gráfico (CustomTkinter)."""
        if self.metrics_chart:
            self.metrics_chart.set_metric_type(value)
    
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