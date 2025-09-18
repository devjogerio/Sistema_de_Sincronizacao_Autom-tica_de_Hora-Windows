"""
Módulo de monitoramento NTP avançado com suporte a múltiplos servidores.
Implementa coleta de métricas, armazenamento de dados e análise de performance.
"""

import time
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

from ntp_client import NTPClient
from config_manager import ConfigManager, ServerConfig

logger = logging.getLogger(__name__)

@dataclass
class NTPMetrics:
    """Classe para armazenar métricas de um servidor NTP."""
    server: str
    timestamp: datetime
    response_time: float
    offset: float
    delay: float
    precision: float
    stratum: int
    is_available: bool
    error_message: Optional[str] = None

class NTPMonitor:
    """Monitor avançado para múltiplos servidores NTP."""
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        Inicializa o monitor NTP.
        
        Args:
            config_manager: Gerenciador de configurações
        """
        self.config_manager = config_manager or ConfigManager()
        self.ntp_client = NTPClient()
        self.db_path = "ntp_metrics.db"
        self.running = False
        self.monitor_thread = None
        self._lock = threading.Lock()
        
        # Inicializa banco de dados
        self._init_database()
        
        logger.info("NTP Monitor inicializado")
        
    def _init_database(self):
        """Inicializa o banco de dados SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela de métricas dos servidores
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS server_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        server_address TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        offset REAL,
                        delay REAL,
                        stratum INTEGER,
                        precision INTEGER,
                        root_delay REAL,
                        root_dispersion REAL,
                        response_time REAL,
                        success BOOLEAN NOT NULL,
                        error_message TEXT
                    )
                ''')
                
                # Criar índices separadamente
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_server_timestamp 
                    ON server_metrics(server_address, timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON server_metrics(timestamp)
                ''')
                
                # Tabela de estatísticas agregadas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS server_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        server_address TEXT NOT NULL,
                        date DATE NOT NULL,
                        total_checks INTEGER DEFAULT 0,
                        successful_checks INTEGER DEFAULT 0,
                        avg_offset REAL,
                        avg_delay REAL,
                        avg_response_time REAL,
                        min_response_time REAL,
                        max_response_time REAL,
                        availability_percent REAL,
                        last_updated DATETIME,
                        UNIQUE(server_address, date)
                    )
                ''')
                
                conn.commit()
                logger.info("Banco de dados inicializado")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    def check_server(self, server: str, timeout: int = 5) -> NTPMetrics:
        """
        Verifica um servidor NTP específico e coleta métricas.
        
        Args:
            server: Endereço do servidor NTP
            timeout: Timeout para conexão
            
        Returns:
            NTPMetrics: Métricas coletadas do servidor
        """
        start_time = time.time()
        
        try:
            ntp_client = NTPClient(server=server, timeout=timeout)
            
            # Obtém hora do servidor
            network_time = ntp_client.get_network_time()
            response_time = time.time() - start_time
            
            if network_time is None:
                return NTPMetrics(
                    server=server,
                    timestamp=datetime.now(timezone.utc),
                    response_time=response_time,
                    offset=0.0,
                    delay=0.0,
                    precision=0.0,
                    stratum=0,
                    is_available=False,
                    error_message="Falha ao obter hora do servidor"
                )
            
            # Calcula métricas
            system_time = ntp_client.get_system_time()
            offset = ntp_client.calculate_time_difference(network_time, system_time)
            
            # Simula outras métricas (em implementação real, obteria do protocolo NTP)
            delay = response_time * 1000  # Converte para ms
            precision = 0.001  # Precisão estimada
            stratum = 2  # Stratum típico para servidores públicos
            
            return NTPMetrics(
                server=server,
                timestamp=datetime.now(timezone.utc),
                response_time=response_time,
                offset=offset,
                delay=delay,
                precision=precision,
                stratum=stratum,
                is_available=True
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Erro ao verificar servidor {server}: {e}")
            
            return NTPMetrics(
                server=server,
                timestamp=datetime.now(timezone.utc),
                response_time=response_time,
                offset=0.0,
                delay=0.0,
                precision=0.0,
                stratum=0,
                is_available=False,
                error_message=str(e)
            )
    
    def check_all_servers(self) -> List[Dict]:
        """
        Verifica todos os servidores habilitados simultaneamente.
        
        Returns:
            List[Dict]: Lista com métricas de todos os servidores
        """
        enabled_servers = self.config_manager.get_enabled_servers()
        if not enabled_servers:
            logger.warning("Nenhum servidor habilitado para verificação")
            return []
        
        results = []
        max_workers = min(len(enabled_servers), self.config_manager.monitoring.max_concurrent_checks)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submete tarefas para verificação paralela
            future_to_server = {
                executor.submit(self.check_server, server.address, server.timeout): server 
                for server in enabled_servers
            }
            
            # Coleta resultados conforme completam
            for future in as_completed(future_to_server):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    server = future_to_server[future]
                    logger.error(f"Erro na verificação paralela do servidor {server.name}: {e}")
                    
                    # Adiciona resultado de erro
                    results.append({
                        'server_name': server.name,
                        'server_address': server.address,
                        'timestamp': datetime.now(),
                        'success': False,
                        'error_message': f"Erro na execução paralela: {str(e)}"
                    })
        
        logger.info(f"Verificação completa: {len(results)} servidores processados")
        return results
    
    def store_metrics(self, results: List[Dict]):
        """
        Armazena métricas no banco de dados.
        
        Args:
            results: Lista de resultados dos servidores
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for result in results:
                    # Insere métricas individuais
                    cursor.execute('''
                        INSERT INTO server_metrics (
                            server_address, timestamp, offset, delay,
                            stratum, precision, root_delay, root_dispersion,
                            response_time, success, error_message
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        result.get('server_address'),
                        result.get('timestamp'),
                        result.get('offset'),
                        result.get('delay'),
                        result.get('stratum'),
                        result.get('precision'),
                        result.get('root_delay'),
                        result.get('root_dispersion'),
                        result.get('response_time'),
                        result.get('success', False),
                        result.get('error_message')
                    ))
                
                conn.commit()
                
                # Atualiza estatísticas agregadas
                self._update_daily_stats(results)
                
                logger.debug(f"Métricas armazenadas: {len(results)} registros")
                
        except Exception as e:
            logger.error(f"Erro ao armazenar métricas: {e}")
            raise
    
    def _update_daily_stats(self, results: List[Dict]):
        """
        Atualiza estatísticas diárias agregadas.
        
        Args:
            results: Lista de resultados dos servidores
        """
        try:
            today = datetime.now().date()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for result in results:
                    server_address = result.get('server_address')
                    
                    # Busca estatísticas existentes do dia
                    cursor.execute('''
                        SELECT total_checks, successful_checks, avg_offset, avg_delay,
                               avg_response_time, min_response_time, max_response_time
                        FROM server_stats 
                        WHERE server_address = ? AND date = ?
                    ''', (server_address, today))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Atualiza estatísticas existentes
                        total_checks = existing[0] + 1
                        successful_checks = existing[1] + (1 if result.get('success') else 0)
                        
                        if result.get('success'):
                            # Recalcula médias ponderadas
                            old_avg_offset = existing[2] or 0
                            old_avg_delay = existing[3] or 0
                            old_avg_response = existing[4] or 0
                            old_min_response = existing[5] or float('inf')
                            old_max_response = existing[6] or 0
                            
                            new_offset = abs(result.get('offset', 0))
                            new_delay = result.get('delay', 0)
                            new_response = result.get('response_time', 0)
                            
                            # Média ponderada
                            weight = successful_checks - 1
                            avg_offset = (old_avg_offset * weight + new_offset) / successful_checks
                            avg_delay = (old_avg_delay * weight + new_delay) / successful_checks
                            avg_response = (old_avg_response * weight + new_response) / successful_checks
                            
                            min_response = min(old_min_response, new_response)
                            max_response = max(old_max_response, new_response)
                        else:
                            avg_offset = existing[2]
                            avg_delay = existing[3]
                            avg_response = existing[4]
                            min_response = existing[5]
                            max_response = existing[6]
                        
                        availability = (successful_checks / total_checks) * 100
                        
                        cursor.execute('''
                            UPDATE server_stats SET
                                total_checks = ?, successful_checks = ?, avg_offset = ?,
                                avg_delay = ?, avg_response_time = ?, min_response_time = ?,
                                max_response_time = ?, availability_percent = ?, last_updated = ?
                            WHERE server_address = ? AND date = ?
                        ''', (
                            total_checks, successful_checks, avg_offset, avg_delay,
                            avg_response, min_response, max_response, availability,
                            datetime.now(), server_address, today
                        ))
                    
                    else:
                        # Cria nova entrada
                        if result.get('success'):
                            avg_offset = abs(result.get('offset', 0))
                            avg_delay = result.get('delay', 0)
                            avg_response = result.get('response_time', 0)
                            min_response = avg_response
                            max_response = avg_response
                            successful_checks = 1
                            availability = 100.0
                        else:
                            avg_offset = None
                            avg_delay = None
                            avg_response = None
                            min_response = None
                            max_response = None
                            successful_checks = 0
                            availability = 0.0
                        
                        cursor.execute('''
                            INSERT INTO server_stats (
                                server_address, date, total_checks, successful_checks,
                                avg_offset, avg_delay, avg_response_time, min_response_time,
                                max_response_time, availability_percent, last_updated
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            server_address, today, 1, successful_checks, avg_offset,
                            avg_delay, avg_response, min_response, max_response,
                            availability, datetime.now()
                        ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas diárias: {e}")
    
    def get_server_metrics(self, server_address: str, hours: int = 24) -> List[Dict]:
        """
        Obtém métricas de um servidor específico.
        
        Args:
            server_address: Endereço do servidor
            hours: Número de horas de histórico
            
        Returns:
            List[Dict]: Lista de métricas do servidor
        """
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM server_metrics 
                    WHERE server_address = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (server_address, since))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
                
        except Exception as e:
            logger.error(f"Erro ao obter métricas do servidor {server_address}: {e}")
            return []
    
    def get_server_stats(self, server_address: str, days: int = 7) -> List[Dict]:
        """
        Obtém estatísticas agregadas de um servidor.
        
        Args:
            server_address: Endereço do servidor
            days: Número de dias de histórico
            
        Returns:
            List[Dict]: Lista de estatísticas diárias
        """
        try:
            since = datetime.now().date() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM server_stats 
                    WHERE server_address = ? AND date >= ?
                    ORDER BY date DESC
                ''', (server_address, since))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
                
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do servidor {server_address}: {e}")
            return []
    
    def get_all_servers_summary(self) -> Dict[str, Dict]:
        """
        Obtém resumo de todos os servidores.
        
        Returns:
            Dict[str, Dict]: Resumo por servidor
        """
        try:
            today = datetime.now().date()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT server_address, total_checks, successful_checks,
                           avg_offset, avg_delay, avg_response_time,
                           availability_percent, last_updated
                    FROM server_stats 
                    WHERE date = ?
                ''', (today,))
                
                summary = {}
                for row in cursor.fetchall():
                    server_address = row[0]
                    summary[server_address] = {
                        'total_checks': row[1],
                        'successful_checks': row[2],
                        'avg_offset': row[3],
                        'avg_delay': row[4],
                        'avg_response_time': row[5],
                        'availability_percent': row[6],
                        'last_updated': row[7]
                    }
                
                return summary
                
        except Exception as e:
            logger.error(f"Erro ao obter resumo dos servidores: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = None):
        """
        Remove dados antigos do banco.
        
        Args:
            days: Dias de retenção (usa configuração se não especificado)
        """
        try:
            if days is None:
                days = self.config_manager.monitoring.history_retention_days
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove métricas antigas
                cursor.execute('''
                    DELETE FROM server_metrics WHERE timestamp < ?
                ''', (cutoff_date,))
                
                metrics_deleted = cursor.rowcount
                
                # Remove estatísticas antigas
                cursor.execute('''
                    DELETE FROM server_stats WHERE date < ?
                ''', (cutoff_date.date(),))
                
                stats_deleted = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Limpeza concluída: {metrics_deleted} métricas e {stats_deleted} estatísticas removidas")
                
        except Exception as e:
            logger.error(f"Erro na limpeza de dados antigos: {e}")
    
    def get_performance_report(self, days: int = 7) -> Dict:
        """
        Gera relatório de performance dos últimos dias.
        
        Args:
            days: Número de dias para o relatório
            
        Returns:
            Dict: Relatório de performance
        """
        try:
            since_date = datetime.now().date() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estatísticas gerais
                cursor.execute('''
                    SELECT 
                        COUNT(DISTINCT server_address) as total_servers,
                        AVG(availability_percent) as avg_availability,
                        AVG(avg_response_time) as avg_response_time,
                        AVG(avg_offset) as avg_offset,
                        MIN(min_response_time) as best_response_time,
                        MAX(max_response_time) as worst_response_time
                    FROM server_stats 
                    WHERE date >= ?
                ''', (since_date,))
                
                general_stats = cursor.fetchone()
                
                # Top servidores por disponibilidade
                cursor.execute('''
                    SELECT server_address, AVG(availability_percent) as avg_availability
                    FROM server_stats 
                    WHERE date >= ?
                    GROUP BY server_address
                    ORDER BY avg_availability DESC
                    LIMIT 5
                ''', (since_date,))
                
                top_availability = cursor.fetchall()
                
                # Servidores com melhor tempo de resposta
                cursor.execute('''
                    SELECT server_address, AVG(avg_response_time) as avg_response
                    FROM server_stats 
                    WHERE date >= ? AND avg_response_time IS NOT NULL
                    GROUP BY server_address
                    ORDER BY avg_response ASC
                    LIMIT 5
                ''', (since_date,))
                
                best_response = cursor.fetchall()
                
                # Servidores com menor offset
                cursor.execute('''
                    SELECT server_address, AVG(avg_offset) as avg_offset
                    FROM server_stats 
                    WHERE date >= ? AND avg_offset IS NOT NULL
                    GROUP BY server_address
                    ORDER BY avg_offset ASC
                    LIMIT 5
                ''', (since_date,))
                
                best_offset = cursor.fetchall()
                
                report = {
                    'period_days': days,
                    'generated_at': datetime.now().isoformat(),
                    'general_stats': {
                        'total_servers': general_stats[0] or 0,
                        'avg_availability': round(general_stats[1] or 0, 2),
                        'avg_response_time': round((general_stats[2] or 0) * 1000, 2),  # ms
                        'avg_offset': round((general_stats[3] or 0) * 1000, 2),  # ms
                        'best_response_time': round((general_stats[4] or 0) * 1000, 2),  # ms
                        'worst_response_time': round((general_stats[5] or 0) * 1000, 2)  # ms
                    },
                    'top_servers': {
                        'availability': [
                            {'server': row[0], 'availability': round(row[1], 2)}
                            for row in top_availability
                        ],
                        'response_time': [
                            {'server': row[0], 'response_time': round(row[1] * 1000, 2)}
                            for row in best_response
                        ],
                        'offset': [
                            {'server': row[0], 'offset': round(row[1] * 1000, 2)}
                            for row in best_offset
                        ]
                    }
                }
                
                return report
                
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de performance: {e}")
            return {}
    
    def get_availability_stats(self, server_address: str, hours: int = 24) -> Dict[str, float]:
        """
        Calcula estatísticas de disponibilidade de um servidor.
        
        Args:
            server_address: Endereço do servidor
            hours: Período para análise
            
        Returns:
            Dict[str, float]: Estatísticas de disponibilidade
        """
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de verificações
                cursor.execute('''
                    SELECT COUNT(*) FROM server_metrics 
                    WHERE server_address = ? AND timestamp >= ?
                ''', (server_address, since))
                total_checks = cursor.fetchone()[0]
                
                # Verificações bem-sucedidas
                cursor.execute('''
                    SELECT COUNT(*) FROM server_metrics 
                    WHERE server_address = ? AND success = 1 
                    AND timestamp >= ?
                ''', (server_address, since))
                successful_checks = cursor.fetchone()[0]
                
                # Tempo médio de resposta
                cursor.execute('''
                    SELECT AVG(response_time) FROM server_metrics 
                    WHERE server_address = ? AND success = 1 
                    AND timestamp >= ?
                ''', (server_address, since))
                avg_response_time = cursor.fetchone()[0] or 0.0
                
                # Offset médio
                cursor.execute('''
                    SELECT AVG(ABS(offset)) FROM server_metrics 
                    WHERE server_address = ? AND success = 1 
                    AND timestamp >= ?
                ''', (server_address, since))
                avg_offset = cursor.fetchone()[0] or 0.0
                
                availability = (successful_checks / total_checks * 100) if total_checks > 0 else 0.0
                
                return {
                    'availability_percent': availability,
                    'total_checks': total_checks,
                    'successful_checks': successful_checks,
                    'avg_response_time': avg_response_time,
                    'avg_offset': avg_offset
                }
                
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas para {server_address}: {e}")
            return {
                'availability_percent': 0.0,
                'total_checks': 0,
                'successful_checks': 0,
                'avg_response_time': 0.0,
                'avg_offset': 0.0
            }
    
    def start_monitoring(self, interval: int = None):
        """
        Inicia monitoramento contínuo.
        
        Args:
            interval: Intervalo em segundos (usa configuração se não especificado)
        """
        if self.running:
            logger.warning("Monitoramento já está em execução")
            return
        
        if interval is None:
            interval = self.config_manager.monitoring.update_interval
        
        self.running = True
        
        def monitoring_loop():
            while self.running:
                try:
                    # Verifica todos os servidores
                    results = self.check_all_servers()
                    
                    if results:
                        # Armazena métricas
                        self.store_metrics(results)
                    
                    # Aguarda próxima verificação
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Erro no loop de monitoramento: {e}")
                    time.sleep(10)  # Aguarda antes de tentar novamente
        
        self.monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Monitoramento iniciado com intervalo de {interval} segundos")
    
    def stop_monitoring(self):
        """Para o monitoramento contínuo."""
        if not self.running:
            logger.warning("Monitoramento não está em execução")
            return
        
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info("Monitoramento parado")
    
    def get_best_server(self) -> Optional[str]:
        """
        Identifica o melhor servidor baseado em métricas de performance.
        
        Returns:
            Optional[str]: Endereço do melhor servidor ou None
        """
        try:
            results = self.check_all_servers()
            
            if not results:
                return None
            
            # Filtra apenas servidores disponíveis
            available_servers = [
                result for result in results
                if result.get('success', False)
            ]
            
            if not available_servers:
                logger.warning("Nenhum servidor NTP disponível")
                return None
            
            # Critério: menor offset + menor tempo de resposta
            best_server = min(
                available_servers,
                key=lambda s: abs(s.get('offset', float('inf'))) + s.get('response_time', float('inf'))
            )
            
            return best_server.get('server_address')
            
        except Exception as e:
            logger.error(f"Erro ao identificar melhor servidor: {e}")
            return None