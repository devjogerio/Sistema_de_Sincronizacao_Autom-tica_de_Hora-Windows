"""
Serviço para operações de banco de dados.
Centraliza todas as operações de persistência de dados.
"""

import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import contextmanager

from ..models.ntp_metrics import NTPMetrics
from ..utils.logger import get_logger

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Serviço para operações de banco de dados.
    
    Gerencia a persistência de métricas NTP e
    fornece métodos para consulta de dados históricos.
    """
    
    def __init__(self, db_path: str = "data/ntp_monitor.db"):
        """
        Inicializa o serviço de banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path
        self.logger = get_logger(__name__)
        self._connection_pool = None
    
    def _initialize_database(self):
        """Inicializa o banco de dados e cria tabelas necessárias."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Tabela para métricas NTP
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ntp_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        server TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        response_time REAL NOT NULL,
                        offset REAL NOT NULL,
                        delay REAL NOT NULL,
                        precision REAL NOT NULL,
                        stratum INTEGER NOT NULL,
                        is_available BOOLEAN NOT NULL,
                        error_message TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Índices para melhor performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_server_timestamp 
                    ON ntp_metrics(server, timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON ntp_metrics(timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON ntp_metrics(created_at)
                ''')
                
                conn.commit()
                logger.info("Banco de dados inicializado com sucesso")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    def initialize(self):
        """
        Inicializa o banco de dados e cria as tabelas necessárias.
        
        Returns:
            bool: True se inicialização foi bem-sucedida
        """
        try:
            self.logger.info("Inicializando banco de dados...")
            
            # Cria diretório de dados se não existir
            data_dir = Path(self.db_path).parent
            data_dir.mkdir(exist_ok=True)
            
            # Conecta ao banco e cria tabelas
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Cria tabela de métricas NTP
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ntp_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        server_address TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        is_available BOOLEAN NOT NULL,
                        response_time REAL,
                        offset REAL,
                        delay REAL,
                        stratum INTEGER,
                        precision INTEGER,
                        root_delay REAL,
                        root_dispersion REAL,
                        error_message TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Cria índices para melhor performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_server_timestamp 
                    ON ntp_metrics(server_address, timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON ntp_metrics(timestamp)
                ''')
                
                conn.commit()
                
            self.logger.info("Banco de dados inicializado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar banco de dados: {e}")
            return False

    @contextmanager
    def _get_connection(self):
        """
        Context manager para conexões com o banco de dados.
        
        Yields:
            sqlite3.Connection: Conexão com o banco
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Erro na conexão com banco de dados: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def store_metrics(self, metrics: List[NTPMetrics]) -> bool:
        """
        Armazena uma lista de métricas no banco de dados.
        
        Args:
            metrics: Lista de métricas para armazenar
            
        Returns:
            bool: True se armazenou com sucesso, False caso contrário
        """
        if not metrics:
            logger.warning("Nenhuma métrica fornecida para armazenamento")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepara dados para inserção
                data_to_insert = []
                for metric in metrics:
                    data_to_insert.append((
                        metric.server,
                        metric.timestamp.isoformat(),
                        metric.response_time,
                        metric.offset,
                        metric.delay,
                        metric.precision,
                        metric.stratum,
                        metric.is_available,
                        metric.error_message
                    ))
                
                # Inserção em lote
                cursor.executemany('''
                    INSERT INTO ntp_metrics 
                    (server, timestamp, response_time, offset, delay, precision, 
                     stratum, is_available, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data_to_insert)
                
                conn.commit()
                logger.debug(f"Armazenadas {len(metrics)} métricas no banco de dados")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao armazenar métricas: {e}")
            return False
    
    def get_latest_metrics(self) -> List[NTPMetrics]:
        """
        Obtém as métricas mais recentes de cada servidor.
        
        Returns:
            List[NTPMetrics]: Lista com métricas mais recentes
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Busca métricas mais recentes por servidor
                cursor.execute('''
                    SELECT m1.* FROM ntp_metrics m1
                    INNER JOIN (
                        SELECT server, MAX(timestamp) as max_timestamp
                        FROM ntp_metrics
                        GROUP BY server
                    ) m2 ON m1.server = m2.server AND m1.timestamp = m2.max_timestamp
                    ORDER BY m1.server
                ''')
                
                rows = cursor.fetchall()
                return [self._row_to_metric(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Erro ao obter métricas mais recentes: {e}")
            return []
    
    def get_historical_metrics(self, hours: int = 24) -> List[NTPMetrics]:
        """
        Obtém métricas históricas de um período específico.
        
        Args:
            hours: Número de horas de histórico
            
        Returns:
            List[NTPMetrics]: Lista com métricas históricas
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM ntp_metrics
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (cutoff_time.isoformat(),))
                
                rows = cursor.fetchall()
                return [self._row_to_metric(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Erro ao obter métricas históricas: {e}")
            return []
    
    def get_server_metrics(self, server: str, hours: int = 24) -> List[NTPMetrics]:
        """
        Obtém métricas de um servidor específico.
        
        Args:
            server: Endereço do servidor
            hours: Número de horas de histórico
            
        Returns:
            List[NTPMetrics]: Lista com métricas do servidor
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM ntp_metrics
                    WHERE server = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (server, cutoff_time.isoformat()))
                
                rows = cursor.fetchall()
                return [self._row_to_metric(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Erro ao obter métricas do servidor {server}: {e}")
            return []
    
    def get_server_statistics(self, server: str, hours: int = 24) -> Dict:
        """
        Calcula estatísticas de um servidor específico.
        
        Args:
            server: Endereço do servidor
            hours: Período em horas para análise
            
        Returns:
            Dict: Estatísticas do servidor
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Estatísticas básicas
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN is_available = 1 THEN 1 ELSE 0 END) as available_checks,
                        AVG(CASE WHEN is_available = 1 THEN response_time END) as avg_response_time,
                        MIN(CASE WHEN is_available = 1 THEN response_time END) as min_response_time,
                        MAX(CASE WHEN is_available = 1 THEN response_time END) as max_response_time,
                        AVG(CASE WHEN is_available = 1 THEN ABS(offset) END) as avg_offset,
                        MIN(CASE WHEN is_available = 1 THEN ABS(offset) END) as min_offset,
                        MAX(CASE WHEN is_available = 1 THEN ABS(offset) END) as max_offset
                    FROM ntp_metrics
                    WHERE server = ? AND timestamp >= ?
                ''', (server, cutoff_time.isoformat()))
                
                row = cursor.fetchone()
                
                if not row or row['total_checks'] == 0:
                    return {
                        'server': server,
                        'period_hours': hours,
                        'total_checks': 0,
                        'availability_percentage': 0.0,
                        'avg_response_time': 0.0,
                        'min_response_time': 0.0,
                        'max_response_time': 0.0,
                        'avg_offset': 0.0,
                        'min_offset': 0.0,
                        'max_offset': 0.0
                    }
                
                availability_percentage = (row['available_checks'] / row['total_checks']) * 100
                
                return {
                    'server': server,
                    'period_hours': hours,
                    'total_checks': row['total_checks'],
                    'available_checks': row['available_checks'],
                    'availability_percentage': availability_percentage,
                    'avg_response_time': row['avg_response_time'] or 0.0,
                    'min_response_time': row['min_response_time'] or 0.0,
                    'max_response_time': row['max_response_time'] or 0.0,
                    'avg_offset': row['avg_offset'] or 0.0,
                    'min_offset': row['min_offset'] or 0.0,
                    'max_offset': row['max_offset'] or 0.0
                }
                
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas do servidor {server}: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """
        Remove dados antigos do banco de dados.
        
        Args:
            days: Número de dias para manter os dados
            
        Returns:
            bool: True se limpou com sucesso, False caso contrário
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM ntp_metrics
                    WHERE timestamp < ?
                ''', (cutoff_time.isoformat(),))
                
                deleted_rows = cursor.rowcount
                conn.commit()
                
                logger.info(f"Removidos {deleted_rows} registros antigos do banco de dados")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao limpar dados antigos: {e}")
            return False
    
    def close(self):
        """
        Fecha conexões e limpa recursos do banco de dados.
        """
        try:
            # Fecha pool de conexões se existir
            if hasattr(self, '_connection_pool'):
                self._connection_pool.close()
            
            self.logger.info("Conexões do banco de dados fechadas")
            
        except Exception as e:
            self.logger.error(f"Erro ao fechar conexões do banco: {e}")

    def get_status(self) -> Dict:
        """
        Obtém status do banco de dados.
        
        Returns:
            Dict: Status do banco de dados
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Conta total de registros
                cursor.execute('SELECT COUNT(*) as total FROM ntp_metrics')
                total_records = cursor.fetchone()['total']
                
                # Conta registros das últimas 24 horas
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                cursor.execute('''
                    SELECT COUNT(*) as recent FROM ntp_metrics
                    WHERE timestamp >= ?
                ''', (cutoff_time.isoformat(),))
                recent_records = cursor.fetchone()['recent']
                
                # Tamanho do arquivo
                file_size = self.db_file.stat().st_size if self.db_file.exists() else 0
                
                return {
                    'database_file': str(self.db_file),
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'total_records': total_records,
                    'recent_records_24h': recent_records,
                    'status': 'healthy'
                }
                
        except Exception as e:
            logger.error(f"Erro ao obter status do banco de dados: {e}")
            return {
                'database_file': str(self.db_file),
                'status': 'error',
                'error': str(e)
            }
    
    def _row_to_metric(self, row) -> NTPMetrics:
        """
        Converte uma linha do banco de dados em objeto NTPMetrics.
        
        Args:
            row: Linha do banco de dados
            
        Returns:
            NTPMetrics: Objeto com métricas
        """
        return NTPMetrics(
            server=row['server'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            response_time=row['response_time'],
            offset=row['offset'],
            delay=row['delay'],
            precision=row['precision'],
            stratum=row['stratum'],
            is_available=bool(row['is_available']),
            error_message=row['error_message']
        )