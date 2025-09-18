"""
Dashboard centralizado para monitoramento NTP com gráficos e indicadores de desempenho.
Implementa visualizações em tempo real e históricas das métricas coletadas.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
import time
import logging

from config_manager import ConfigManager
from ntp_monitor import NTPMonitor

logger = logging.getLogger(__name__)

class MetricsChart:
    """Classe para criar gráficos de métricas."""
    
    def __init__(self, parent_frame, title: str, width: int = 400, height: int = 300):
        """
        Inicializa o gráfico de métricas.
        
        Args:
            parent_frame: Frame pai para o gráfico
            title: Título do gráfico
            width: Largura do gráfico
            height: Altura do gráfico
        """
        self.parent_frame = parent_frame
        self.title = title
        
        # Cria figura matplotlib
        self.figure = Figure(figsize=(width/100, height/100), dpi=100)
        self.figure.patch.set_facecolor('#2b2b2b')
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.set_title(title, color='white', fontsize=12, fontweight='bold')
        
        # Canvas para integração com tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, parent_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurações de estilo
        self._setup_style()
    
    def _setup_style(self):
        """Configura estilo do gráfico."""
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.grid(True, alpha=0.3, color='gray')
    
    def update_line_chart(self, data: Dict[str, List], x_label: str = "Tempo", y_label: str = "Valor"):
        """
        Atualiza gráfico de linhas.
        
        Args:
            data: Dicionário com dados {servidor: [valores]}
            x_label: Rótulo do eixo X
            y_label: Rótulo do eixo Y
        """
        try:
            self.ax.clear()
            self._setup_style()
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            for i, (server, values) in enumerate(data.items()):
                if values:
                    color = colors[i % len(colors)]
                    self.ax.plot(values, label=server, color=color, linewidth=2, marker='o', markersize=4)
            
            self.ax.set_xlabel(x_label, color='white')
            self.ax.set_ylabel(y_label, color='white')
            self.ax.set_title(self.title, color='white', fontsize=12, fontweight='bold')
            
            if data:
                self.ax.legend(loc='upper right', facecolor='#2b2b2b', edgecolor='white', labelcolor='white')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar gráfico de linhas: {e}")
    
    def update_bar_chart(self, data: Dict[str, float], y_label: str = "Valor"):
        """
        Atualiza gráfico de barras.
        
        Args:
            data: Dicionário com dados {servidor: valor}
            y_label: Rótulo do eixo Y
        """
        try:
            self.ax.clear()
            self._setup_style()
            
            if not data:
                return
            
            servers = list(data.keys())
            values = list(data.values())
            
            # Cores baseadas nos valores (verde para bom, vermelho para ruim)
            colors = []
            for value in values:
                if value >= 95:  # Disponibilidade alta
                    colors.append('#2ca02c')  # Verde
                elif value >= 80:
                    colors.append('#ff7f0e')  # Laranja
                else:
                    colors.append('#d62728')  # Vermelho
            
            bars = self.ax.bar(servers, values, color=colors, alpha=0.8)
            
            # Adiciona valores nas barras
            for bar, value in zip(bars, values):
                height = bar.get_height()
                self.ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                           f'{value:.1f}%', ha='center', va='bottom', color='white', fontweight='bold')
            
            self.ax.set_ylabel(y_label, color='white')
            self.ax.set_title(self.title, color='white', fontsize=12, fontweight='bold')
            
            # Rotaciona labels do eixo X se necessário
            if len(servers) > 3:
                plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar gráfico de barras: {e}")

class StatusIndicator(ctk.CTkFrame):
    """Indicador de status visual."""
    
    def __init__(self, parent, title: str, **kwargs):
        """
        Inicializa indicador de status.
        
        Args:
            parent: Widget pai
            title: Título do indicador
        """
        super().__init__(parent, **kwargs)
        
        self.title = title
        
        # Label do título
        self.title_label = ctk.CTkLabel(
            self, 
            text=title, 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        # Label do valor
        self.value_label = ctk.CTkLabel(
            self, 
            text="--", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.value_label.pack(pady=5)
        
        # Label da unidade
        self.unit_label = ctk.CTkLabel(
            self, 
            text="", 
            font=ctk.CTkFont(size=12)
        )
        self.unit_label.pack(pady=(0, 10))
    
    def update_value(self, value: float, unit: str = "", status: str = "normal"):
        """
        Atualiza valor do indicador.
        
        Args:
            value: Valor a ser exibido
            unit: Unidade do valor
            status: Status (normal, warning, error)
        """
        try:
            # Formata valor baseado no tipo
            if isinstance(value, float):
                if value < 1:
                    formatted_value = f"{value:.3f}"
                elif value < 10:
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = f"{value:.1f}"
            else:
                formatted_value = str(value)
            
            self.value_label.configure(text=formatted_value)
            self.unit_label.configure(text=unit)
            
            # Define cor baseada no status
            if status == "error":
                color = "#d62728"  # Vermelho
            elif status == "warning":
                color = "#ff7f0e"  # Laranja
            else:
                color = "#2ca02c"  # Verde
            
            self.value_label.configure(text_color=color)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar indicador {self.title}: {e}")
            self.value_label.configure(text="Erro")

class NTPDashboard(ctk.CTkToplevel):
    """Dashboard principal de monitoramento NTP."""
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        Inicializa o dashboard.
        
        Args:
            config_manager: Gerenciador de configurações
        """
        super().__init__()
        
        self.config_manager = config_manager or ConfigManager()
        self.ntp_monitor = NTPMonitor(self.config_manager)
        
        self.title("Dashboard NTP - Monitoramento em Tempo Real")
        self.geometry("1400x900")
        
        # Variáveis de controle
        self.monitoring_active = False
        self.update_thread = None
        self._stop_event = threading.Event()
        
        # Dados para gráficos
        self.metrics_history = {}
        self.max_history_points = 50
        
        # Configura interface
        self._setup_ui()
        
        # Inicia monitoramento automático
        self.start_monitoring()
        
        # Configura fechamento da janela
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("Dashboard NTP inicializado")
    
    def _setup_ui(self):
        """Configura a interface do dashboard."""
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Dashboard de Monitoramento NTP", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Frame de controles
        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Botões de controle
        self.start_button = ctk.CTkButton(
            controls_frame, 
            text="Iniciar Monitoramento", 
            command=self.start_monitoring,
            width=150
        )
        self.start_button.pack(side="left", padx=10, pady=10)
        
        self.stop_button = ctk.CTkButton(
            controls_frame, 
            text="Parar Monitoramento", 
            command=self.stop_monitoring,
            width=150
        )
        self.stop_button.pack(side="left", padx=10, pady=10)
        
        self.refresh_button = ctk.CTkButton(
            controls_frame, 
            text="Atualizar Agora", 
            command=self.manual_refresh,
            width=150
        )
        self.refresh_button.pack(side="left", padx=10, pady=10)
        
        # Status do monitoramento
        self.status_label = ctk.CTkLabel(
            controls_frame, 
            text="Status: Parado", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.status_label.pack(side="right", padx=10, pady=10)
        
        # Frame de indicadores
        indicators_frame = ctk.CTkFrame(main_frame)
        indicators_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Indicadores de status
        self.total_servers_indicator = StatusIndicator(
            indicators_frame, 
            "Total de Servidores",
            width=180,
            height=120
        )
        self.total_servers_indicator.pack(side="left", padx=10, pady=10)
        
        self.active_servers_indicator = StatusIndicator(
            indicators_frame, 
            "Servidores Ativos",
            width=180,
            height=120
        )
        self.active_servers_indicator.pack(side="left", padx=10, pady=10)
        
        self.avg_response_indicator = StatusIndicator(
            indicators_frame, 
            "Tempo Médio",
            width=180,
            height=120
        )
        self.avg_response_indicator.pack(side="left", padx=10, pady=10)
        
        self.avg_offset_indicator = StatusIndicator(
            indicators_frame, 
            "Offset Médio",
            width=180,
            height=120
        )
        self.avg_offset_indicator.pack(side="left", padx=10, pady=10)
        
        self.availability_indicator = StatusIndicator(
            indicators_frame, 
            "Disponibilidade",
            width=180,
            height=120
        )
        self.availability_indicator.pack(side="left", padx=10, pady=10)
        
        # Frame de gráficos
        charts_frame = ctk.CTkFrame(main_frame)
        charts_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Primeira linha de gráficos
        top_charts_frame = ctk.CTkFrame(charts_frame)
        top_charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Gráfico de tempo de resposta
        response_chart_frame = ctk.CTkFrame(top_charts_frame)
        response_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.response_time_chart = MetricsChart(
            response_chart_frame, 
            "Tempo de Resposta (ms)",
            width=450,
            height=250
        )
        
        # Gráfico de offset
        offset_chart_frame = ctk.CTkFrame(top_charts_frame)
        offset_chart_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.offset_chart = MetricsChart(
            offset_chart_frame, 
            "Offset NTP (ms)",
            width=450,
            height=250
        )
        
        # Segunda linha de gráficos
        bottom_charts_frame = ctk.CTkFrame(charts_frame)
        bottom_charts_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Gráfico de disponibilidade
        availability_chart_frame = ctk.CTkFrame(bottom_charts_frame)
        availability_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.availability_chart = MetricsChart(
            availability_chart_frame, 
            "Disponibilidade por Servidor (%)",
            width=450,
            height=250
        )
        
        # Gráfico de stratum
        stratum_chart_frame = ctk.CTkFrame(bottom_charts_frame)
        stratum_chart_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.stratum_chart = MetricsChart(
            stratum_chart_frame, 
            "Stratum dos Servidores",
            width=450,
            height=250
        )
    
    def start_monitoring(self):
        """Inicia o monitoramento automático."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self._stop_event.clear()
            
            self.update_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.update_thread.start()
            
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.status_label.configure(text="Status: Monitorando", text_color="green")
            
            logger.info("Monitoramento iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento automático."""
        if self.monitoring_active:
            self.monitoring_active = False
            self._stop_event.set()
            
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=2)
            
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.status_label.configure(text="Status: Parado", text_color="red")
            
            logger.info("Monitoramento parado")
    
    def manual_refresh(self):
        """Atualiza dados manualmente."""
        threading.Thread(target=self._update_dashboard, daemon=True).start()
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento."""
        while self.monitoring_active and not self._stop_event.is_set():
            try:
                self._update_dashboard()
                
                # Aguarda próxima atualização
                interval = self.config_manager.ui.refresh_interval
                if self._stop_event.wait(timeout=interval):
                    break
                    
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(5)  # Aguarda antes de tentar novamente
    
    def _update_dashboard(self):
        """Atualiza todos os dados do dashboard."""
        try:
            # Coleta métricas de todos os servidores
            results = self.ntp_monitor.check_all_servers()
            
            if not results:
                return
            
            # Atualiza histórico de métricas
            self._update_metrics_history(results)
            
            # Atualiza indicadores
            self._update_indicators(results)
            
            # Atualiza gráficos
            self._update_charts()
            
            logger.debug("Dashboard atualizado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar dashboard: {e}")
    
    def _update_metrics_history(self, results: List[Dict]):
        """
        Atualiza histórico de métricas.
        
        Args:
            results: Lista de resultados dos servidores
        """
        current_time = datetime.now()
        
        for result in results:
            server_name = result['server_name']
            
            if server_name not in self.metrics_history:
                self.metrics_history[server_name] = {
                    'timestamps': [],
                    'response_times': [],
                    'offsets': [],
                    'availability': [],
                    'stratum': []
                }
            
            history = self.metrics_history[server_name]
            
            # Adiciona novos dados
            history['timestamps'].append(current_time)
            history['response_times'].append(result.get('response_time', 0) * 1000 if result.get('response_time') else 0)
            history['offsets'].append(abs(result.get('offset', 0)) * 1000 if result.get('offset') else 0)
            history['availability'].append(100 if result.get('success') else 0)
            history['stratum'].append(result.get('stratum', 0) if result.get('stratum') else 0)
            
            # Limita tamanho do histórico
            for key in history:
                if len(history[key]) > self.max_history_points:
                    history[key] = history[key][-self.max_history_points:]
    
    def _update_indicators(self, results: List[Dict]):
        """
        Atualiza indicadores de status.
        
        Args:
            results: Lista de resultados dos servidores
        """
        try:
            total_servers = len(results)
            active_servers = sum(1 for r in results if r.get('success'))
            
            # Calcula métricas agregadas
            successful_results = [r for r in results if r.get('success')]
            
            if successful_results:
                avg_response = sum(r.get('response_time', 0) for r in successful_results) / len(successful_results)
                avg_offset = sum(abs(r.get('offset', 0)) for r in successful_results) / len(successful_results)
                availability = (active_servers / total_servers) * 100
            else:
                avg_response = 0
                avg_offset = 0
                availability = 0
            
            # Atualiza indicadores
            self.total_servers_indicator.update_value(total_servers, "servidores")
            
            status = "normal" if active_servers > 0 else "error"
            self.active_servers_indicator.update_value(active_servers, "ativos", status)
            
            status = "normal" if avg_response < 1 else "warning" if avg_response < 5 else "error"
            self.avg_response_indicator.update_value(avg_response * 1000, "ms", status)
            
            status = "normal" if avg_offset < 0.1 else "warning" if avg_offset < 1 else "error"
            self.avg_offset_indicator.update_value(avg_offset * 1000, "ms", status)
            
            status = "normal" if availability >= 95 else "warning" if availability >= 80 else "error"
            self.availability_indicator.update_value(availability, "%", status)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar indicadores: {e}")
    
    def _update_charts(self):
        """Atualiza todos os gráficos."""
        try:
            if not self.metrics_history:
                return
            
            # Prepara dados para gráficos de linha
            response_data = {}
            offset_data = {}
            stratum_data = {}
            
            for server, history in self.metrics_history.items():
                if history['response_times']:
                    response_data[server] = history['response_times'][-20:]  # Últimos 20 pontos
                    offset_data[server] = history['offsets'][-20:]
                    stratum_data[server] = history['stratum'][-20:]
            
            # Atualiza gráficos de linha
            self.response_time_chart.update_line_chart(response_data, "Tempo", "ms")
            self.offset_chart.update_line_chart(offset_data, "Tempo", "ms")
            self.stratum_chart.update_line_chart(stratum_data, "Tempo", "Stratum")
            
            # Prepara dados para gráfico de disponibilidade (barras)
            availability_data = {}
            for server, history in self.metrics_history.items():
                if history['availability']:
                    # Calcula disponibilidade média dos últimos pontos
                    recent_availability = history['availability'][-10:]  # Últimos 10 pontos
                    avg_availability = sum(recent_availability) / len(recent_availability)
                    availability_data[server] = avg_availability
            
            # Atualiza gráfico de barras
            self.availability_chart.update_bar_chart(availability_data, "Disponibilidade (%)")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar gráficos: {e}")
    
    def on_closing(self):
        """Manipula fechamento da janela."""
        self.stop_monitoring()
        self.destroy()

def main():
    """Função principal para teste do dashboard."""
    # Configura logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configura tema
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Cria aplicação principal (oculta)
    root = ctk.CTk()
    root.withdraw()  # Oculta janela principal
    
    # Cria dashboard
    dashboard = NTPDashboard()
    
    # Inicia loop principal
    root.mainloop()

if __name__ == "__main__":
    main()