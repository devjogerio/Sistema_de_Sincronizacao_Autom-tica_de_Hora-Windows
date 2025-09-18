"""
Interface gráfica desktop para monitoramento NTP em tempo real.
Implementa dashboard com customTkinter, gráficos e indicadores de performance.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
from matplotlib.figure import Figure
import pandas as pd
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from ntp_monitor import NTPMonitor, NTPMetrics
from email_notifier import EmailNotifier, EmailConfig

logger = logging.getLogger(__name__)

# Configuração do tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ServerStatusFrame(ctk.CTkFrame):
    """Frame para exibir status de um servidor NTP."""
    
    def __init__(self, parent, server_name: str):
        super().__init__(parent)
        self.server_name = server_name
        
        # Configuração do grid
        self.grid_columnconfigure(1, weight=1)
        
        # Widgets
        self.status_indicator = ctk.CTkLabel(
            self, text="●", font=ctk.CTkFont(size=20), text_color="gray"
        )
        self.status_indicator.grid(row=0, column=0, padx=5, pady=5)
        
        self.server_label = ctk.CTkLabel(
            self, text=server_name, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.server_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        self.response_time_label = ctk.CTkLabel(self, text="Tempo: --")
        self.response_time_label.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        self.offset_label = ctk.CTkLabel(self, text="Offset: --")
        self.offset_label.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        
        self.last_check_label = ctk.CTkLabel(self, text="Última verificação: --")
        self.last_check_label.grid(row=3, column=1, padx=5, pady=2, sticky="w")
    
    def update_status(self, metrics: NTPMetrics):
        """Atualiza o status do servidor."""
        if metrics.is_available:
            self.status_indicator.configure(text_color="green")
            self.response_time_label.configure(text=f"Tempo: {metrics.response_time:.3f}s")
            self.offset_label.configure(text=f"Offset: {metrics.offset:.3f}s")
        else:
            self.status_indicator.configure(text_color="red")
            self.response_time_label.configure(text="Tempo: Indisponível")
            self.offset_label.configure(text=f"Erro: {metrics.error_message or 'Desconhecido'}")
        
        self.last_check_label.configure(
            text=f"Última verificação: {metrics.timestamp.strftime('%H:%M:%S')}"
        )

class MetricsGraphFrame(ctk.CTkFrame):
    """Frame para exibir gráficos de métricas."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configuração do matplotlib para tema escuro
        plt.style.use('dark_background')
        
        # Figura do matplotlib
        self.figure = Figure(figsize=(12, 6), facecolor='#2b2b2b')
        self.canvas = FigureCanvasTkinter(self.figure, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Subplots
        self.ax1 = self.figure.add_subplot(221)  # Response time
        self.ax2 = self.figure.add_subplot(222)  # Offset
        self.ax3 = self.figure.add_subplot(223)  # Availability
        self.ax4 = self.figure.add_subplot(224)  # Server comparison
        
        self.figure.tight_layout(pad=3.0)
        
        # Dados para gráficos
        self.history_data = {}
    
    def update_graphs(self, ntp_monitor: NTPMonitor):
        """Atualiza todos os gráficos com dados recentes."""
        try:
            # Limpa gráficos
            for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
                ax.clear()
            
            # Coleta dados históricos
            servers = ntp_monitor.servers
            current_time = datetime.now()
            
            # Gráfico 1: Tempo de resposta
            self.ax1.set_title("Tempo de Resposta (últimas 24h)", color='white')
            self.ax1.set_xlabel("Tempo", color='white')
            self.ax1.set_ylabel("Segundos", color='white')
            
            for server in servers:
                history = ntp_monitor.get_server_history(server, hours=24)
                if history:
                    times = [h.timestamp for h in history if h.is_available]
                    response_times = [h.response_time for h in history if h.is_available]
                    
                    if times and response_times:
                        self.ax1.plot(times, response_times, label=server, marker='o', markersize=2)
            
            self.ax1.legend()
            self.ax1.tick_params(colors='white')
            
            # Gráfico 2: Offset de tempo
            self.ax2.set_title("Offset de Tempo (últimas 24h)", color='white')
            self.ax2.set_xlabel("Tempo", color='white')
            self.ax2.set_ylabel("Segundos", color='white')
            
            for server in servers:
                history = ntp_monitor.get_server_history(server, hours=24)
                if history:
                    times = [h.timestamp for h in history if h.is_available]
                    offsets = [abs(h.offset) for h in history if h.is_available]
                    
                    if times and offsets:
                        self.ax2.plot(times, offsets, label=server, marker='o', markersize=2)
            
            self.ax2.legend()
            self.ax2.tick_params(colors='white')
            
            # Gráfico 3: Disponibilidade por servidor
            self.ax3.set_title("Disponibilidade (últimas 24h)", color='white')
            self.ax3.set_ylabel("Porcentagem", color='white')
            
            server_names = []
            availability_percentages = []
            
            for server in servers:
                stats = ntp_monitor.get_availability_stats(server, hours=24)
                server_names.append(server.split('.')[0])  # Nome curto
                availability_percentages.append(stats['availability_percent'])
            
            if server_names and availability_percentages:
                bars = self.ax3.bar(server_names, availability_percentages)
                
                # Colorir barras baseado na disponibilidade
                for bar, percentage in zip(bars, availability_percentages):
                    if percentage >= 95:
                        bar.set_color('green')
                    elif percentage >= 80:
                        bar.set_color('orange')
                    else:
                        bar.set_color('red')
            
            self.ax3.set_ylim(0, 100)
            self.ax3.tick_params(colors='white')
            
            # Gráfico 4: Comparação atual de servidores
            self.ax4.set_title("Status Atual dos Servidores", color='white')
            
            current_metrics = ntp_monitor.metrics_cache
            if current_metrics:
                available_servers = [s for s, m in current_metrics.items() if m.is_available]
                unavailable_servers = [s for s, m in current_metrics.items() if not m.is_available]
                
                sizes = [len(available_servers), len(unavailable_servers)]
                labels = ['Disponíveis', 'Indisponíveis']
                colors = ['green', 'red']
                
                if sum(sizes) > 0:
                    self.ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                               textprops={'color': 'white'})
            
            # Atualiza canvas
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar gráficos: {e}")

class SettingsWindow(ctk.CTkToplevel):
    """Janela de configurações."""
    
    def __init__(self, parent, ntp_monitor: NTPMonitor, email_notifier: Optional[EmailNotifier] = None):
        super().__init__(parent)
        
        self.ntp_monitor = ntp_monitor
        self.email_notifier = email_notifier
        
        self.title("Configurações")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Centraliza janela
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Cria widgets da janela de configurações."""
        # Notebook para abas
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Aba de servidores NTP
        servers_frame = ctk.CTkFrame(notebook)
        notebook.add(servers_frame, text="Servidores NTP")
        
        ctk.CTkLabel(servers_frame, text="Servidores NTP:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        self.servers_text = ctk.CTkTextbox(servers_frame, height=200)
        self.servers_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Preenche com servidores atuais
        current_servers = "\n".join(self.ntp_monitor.servers)
        self.servers_text.insert("1.0", current_servers)
        
        # Aba de email
        email_frame = ctk.CTkFrame(notebook)
        notebook.add(email_frame, text="Notificações Email")
        
        # Campos de email
        ctk.CTkLabel(email_frame, text="Servidor SMTP:").pack(pady=5)
        self.smtp_server_entry = ctk.CTkEntry(email_frame, width=300)
        self.smtp_server_entry.pack(pady=5)
        
        ctk.CTkLabel(email_frame, text="Porta SMTP:").pack(pady=5)
        self.smtp_port_entry = ctk.CTkEntry(email_frame, width=300)
        self.smtp_port_entry.pack(pady=5)
        
        ctk.CTkLabel(email_frame, text="Usuário:").pack(pady=5)
        self.email_user_entry = ctk.CTkEntry(email_frame, width=300)
        self.email_user_entry.pack(pady=5)
        
        ctk.CTkLabel(email_frame, text="Senha:").pack(pady=5)
        self.email_pass_entry = ctk.CTkEntry(email_frame, width=300, show="*")
        self.email_pass_entry.pack(pady=5)
        
        ctk.CTkLabel(email_frame, text="Destinatários (separados por vírgula):").pack(pady=5)
        self.recipients_entry = ctk.CTkEntry(email_frame, width=300)
        self.recipients_entry.pack(pady=5)
        
        # Botões
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(buttons_frame, text="Salvar", 
                     command=self.save_settings).pack(side="right", padx=5)
        ctk.CTkButton(buttons_frame, text="Cancelar", 
                     command=self.destroy).pack(side="right", padx=5)
    
    def save_settings(self):
        """Salva as configurações."""
        try:
            # Atualiza servidores NTP
            servers_text = self.servers_text.get("1.0", "end-1c")
            new_servers = [s.strip() for s in servers_text.split("\n") if s.strip()]
            
            if new_servers:
                self.ntp_monitor.servers = new_servers
                logger.info(f"Servidores NTP atualizados: {new_servers}")
            
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            self.destroy()
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")

class NTPMonitorGUI:
    """Interface gráfica principal para monitoramento NTP."""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("NTP Monitor - Sistema de Monitoramento")
        self.root.geometry("1200x800")
        
        # Componentes
        self.ntp_monitor = NTPMonitor()
        self.email_notifier = None
        self.monitoring_active = False
        self.update_thread = None
        
        # Interface
        self.create_widgets()
        self.setup_monitoring()
        
        # Inicia monitoramento
        self.start_monitoring()
    
    def create_widgets(self):
        """Cria todos os widgets da interface."""
        # Frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Barra superior
        top_frame = ctk.CTkFrame(main_frame)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        # Título
        title_label = ctk.CTkLabel(
            top_frame, 
            text="🕐 NTP Monitor Dashboard", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        # Botões de controle
        controls_frame = ctk.CTkFrame(top_frame)
        controls_frame.pack(side="right", padx=10, pady=10)
        
        self.start_stop_button = ctk.CTkButton(
            controls_frame, 
            text="Parar Monitoramento",
            command=self.toggle_monitoring,
            width=150
        )
        self.start_stop_button.pack(side="left", padx=5)
        
        ctk.CTkButton(
            controls_frame,
            text="Configurações",
            command=self.open_settings,
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            controls_frame,
            text="Atualizar",
            command=self.manual_update,
            width=100
        ).pack(side="left", padx=5)
        
        # Status geral
        self.status_label = ctk.CTkLabel(
            top_frame,
            text="Status: Iniciando...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="right", padx=10)
        
        # Notebook para abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Aba de status dos servidores
        self.servers_frame = ctk.CTkScrollableFrame(self.notebook)
        self.notebook.add(self.servers_frame, text="Status dos Servidores")
        
        # Aba de gráficos
        self.graphs_frame = MetricsGraphFrame(self.notebook)
        self.notebook.add(self.graphs_frame, text="Gráficos e Métricas")
        
        # Aba de logs
        logs_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(logs_frame, text="Logs e Alertas")
        
        self.logs_text = ctk.CTkTextbox(logs_frame, height=400)
        self.logs_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frames de status dos servidores
        self.server_frames = {}
        self.create_server_frames()
    
    def create_server_frames(self):
        """Cria frames para cada servidor."""
        for server in self.ntp_monitor.servers:
            frame = ServerStatusFrame(self.servers_frame, server)
            frame.pack(fill="x", padx=10, pady=5)
            self.server_frames[server] = frame
    
    def setup_monitoring(self):
        """Configura o sistema de monitoramento."""
        # Inicia monitoramento em thread separada
        self.ntp_monitor.start_monitoring(interval=30)  # Verifica a cada 30 segundos
    
    def start_monitoring(self):
        """Inicia o loop de atualização da interface."""
        self.monitoring_active = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
    
    def stop_monitoring(self):
        """Para o monitoramento."""
        self.monitoring_active = False
        self.ntp_monitor.stop_monitoring()
    
    def toggle_monitoring(self):
        """Alterna entre iniciar e parar monitoramento."""
        if self.monitoring_active:
            self.stop_monitoring()
            self.start_stop_button.configure(text="Iniciar Monitoramento")
            self.status_label.configure(text="Status: Parado")
        else:
            self.setup_monitoring()
            self.start_monitoring()
            self.start_stop_button.configure(text="Parar Monitoramento")
            self.status_label.configure(text="Status: Monitorando...")
    
    def update_loop(self):
        """Loop principal de atualização da interface."""
        while self.monitoring_active:
            try:
                self.update_interface()
                time.sleep(5)  # Atualiza interface a cada 5 segundos
            except Exception as e:
                logger.error(f"Erro no loop de atualização: {e}")
                time.sleep(5)
    
    def update_interface(self):
        """Atualiza todos os elementos da interface."""
        try:
            # Atualiza status dos servidores
            current_metrics = self.ntp_monitor.metrics_cache
            
            if current_metrics:
                for server, metrics in current_metrics.items():
                    if server in self.server_frames:
                        self.server_frames[server].update_status(metrics)
                
                # Atualiza status geral
                available_count = sum(1 for m in current_metrics.values() if m.is_available)
                total_count = len(current_metrics)
                
                self.root.after(0, lambda: self.status_label.configure(
                    text=f"Status: {available_count}/{total_count} servidores disponíveis"
                ))
                
                # Atualiza gráficos (menos frequente)
                if hasattr(self, '_last_graph_update'):
                    if time.time() - self._last_graph_update > 60:  # Atualiza gráficos a cada minuto
                        self.root.after(0, lambda: self.graphs_frame.update_graphs(self.ntp_monitor))
                        self._last_graph_update = time.time()
                else:
                    self.root.after(0, lambda: self.graphs_frame.update_graphs(self.ntp_monitor))
                    self._last_graph_update = time.time()
                
                # Log de status
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_message = f"[{timestamp}] Verificação concluída: {available_count}/{total_count} servidores disponíveis\n"
                
                self.root.after(0, lambda: self.logs_text.insert("end", log_message))
                self.root.after(0, lambda: self.logs_text.see("end"))
            
        except Exception as e:
            logger.error(f"Erro ao atualizar interface: {e}")
    
    def manual_update(self):
        """Força atualização manual."""
        def update_task():
            self.ntp_monitor.check_all_servers()
            self.update_interface()
        
        threading.Thread(target=update_task, daemon=True).start()
    
    def open_settings(self):
        """Abre janela de configurações."""
        SettingsWindow(self.root, self.ntp_monitor, self.email_notifier)
    
    def run(self):
        """Executa a aplicação."""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Erro na execução da GUI: {e}")
    
    def on_closing(self):
        """Manipula o fechamento da aplicação."""
        self.stop_monitoring()
        self.root.destroy()

def main():
    """Função principal para executar a GUI."""
    try:
        # Configura logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Cria e executa aplicação
        app = NTPMonitorGUI()
        app.run()
        
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {e}")
        messagebox.showerror("Erro", f"Erro ao iniciar aplicação: {e}")

if __name__ == "__main__":
    main()