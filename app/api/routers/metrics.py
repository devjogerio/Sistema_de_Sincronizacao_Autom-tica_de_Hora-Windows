"""
Router para Métricas e Estatísticas
Endpoints para consulta de dados históricos e análises
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.api.models.requests import MetricsQueryRequest
from app.api.models.responses import MetricResponse, StatisticsResponse
from app.services.database_service import DatabaseService
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

# Criar router
router = APIRouter()

# Dependências
def get_database_service():
    """Obter instância do serviço de banco de dados"""
    return DatabaseService()

@router.get("/", response_model=List[MetricResponse])
async def get_metrics(
    server_ids: Optional[List[int]] = Query(None, description="IDs dos servidores"),
    start_date: Optional[datetime] = Query(None, description="Data de início"),
    end_date: Optional[datetime] = Query(None, description="Data de fim"),
    limit: int = Query(1000, ge=1, le=10000, description="Limite de registros"),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Obter métricas históricas dos servidores
    
    - **server_ids**: Lista de IDs dos servidores (opcional)
    - **start_date**: Data de início do período (opcional)
    - **end_date**: Data de fim do período (opcional)
    - **limit**: Limite máximo de registros
    """
    try:
        logger.info(f"Consultando métricas - servidores: {server_ids}, período: {start_date} a {end_date}")
        
        # Definir período padrão se não especificado (últimas 24 horas)
        if not start_date:
            start_date = datetime.now() - timedelta(hours=24)
        if not end_date:
            end_date = datetime.now()
        
        # Validar período
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data de fim deve ser posterior à data de início"
            )
        
        # Buscar métricas no banco de dados
        metrics = db_service.get_metrics(
            server_ids=server_ids,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        # Converter para modelo de resposta
        metric_responses = []
        for metric in metrics:
            metric_responses.append(MetricResponse(
                server_id=metric.server_id,
                server_name=metric.server_name,
                timestamp=metric.timestamp,
                response_time=metric.response_time,
                offset=metric.offset,
                delay=metric.delay,
                jitter=metric.jitter,
                status=metric.status or "unknown"
            ))
        
        logger.info(f"Retornando {len(metric_responses)} métricas")
        return metric_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar métricas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/statistics", response_model=List[StatisticsResponse])
async def get_statistics(
    server_ids: Optional[List[int]] = Query(None, description="IDs dos servidores"),
    period_hours: int = Query(24, ge=1, le=8760, description="Período em horas"),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Obter estatísticas agregadas dos servidores
    
    - **server_ids**: Lista de IDs dos servidores (opcional)
    - **period_hours**: Período para análise em horas (padrão: 24h)
    """
    try:
        logger.info(f"Calculando estatísticas - servidores: {server_ids}, período: {period_hours}h")
        
        # Definir período
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=period_hours)
        
        # Buscar estatísticas
        statistics = db_service.get_server_statistics(
            server_ids=server_ids,
            start_date=start_date,
            end_date=end_date
        )
        
        # Converter para modelo de resposta
        stats_responses = []
        for stat in statistics:
            stats_responses.append(StatisticsResponse(
                server_id=stat.server_id,
                server_name=stat.server_name,
                period_start=start_date,
                period_end=end_date,
                avg_response_time=stat.avg_response_time,
                min_response_time=stat.min_response_time,
                max_response_time=stat.max_response_time,
                avg_offset=stat.avg_offset,
                std_offset=stat.std_offset,
                uptime_percentage=stat.uptime_percentage,
                total_checks=stat.total_checks,
                failed_checks=stat.failed_checks
            ))
        
        logger.info(f"Retornando estatísticas de {len(stats_responses)} servidores")
        return stats_responses
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/server/{server_id}/latest", response_model=MetricResponse)
async def get_latest_metric(
    server_id: int,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Obter última métrica de um servidor específico
    
    - **server_id**: ID do servidor
    """
    try:
        logger.info(f"Buscando última métrica do servidor {server_id}")
        
        # Buscar última métrica
        metric = db_service.get_latest_metric(server_id)
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma métrica encontrada para este servidor"
            )
        
        return MetricResponse(
            server_id=metric.server_id,
            server_name=metric.server_name,
            timestamp=metric.timestamp,
            response_time=metric.response_time,
            offset=metric.offset,
            delay=metric.delay,
            jitter=metric.jitter,
            status=metric.status or "unknown"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar última métrica do servidor {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/server/{server_id}/trend", response_model=List[MetricResponse])
async def get_server_trend(
    server_id: int,
    hours: int = Query(24, ge=1, le=168, description="Período em horas"),
    interval_minutes: int = Query(60, ge=5, le=1440, description="Intervalo em minutos"),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Obter tendência de métricas de um servidor
    
    - **server_id**: ID do servidor
    - **hours**: Período para análise em horas
    - **interval_minutes**: Intervalo de agregação em minutos
    """
    try:
        logger.info(f"Calculando tendência do servidor {server_id} - {hours}h com intervalo {interval_minutes}min")
        
        # Definir período
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)
        
        # Buscar tendência
        trend_data = db_service.get_server_trend(
            server_id=server_id,
            start_date=start_date,
            end_date=end_date,
            interval_minutes=interval_minutes
        )
        
        # Converter para modelo de resposta
        trend_responses = []
        for data_point in trend_data:
            trend_responses.append(MetricResponse(
                server_id=data_point.server_id,
                server_name=data_point.server_name,
                timestamp=data_point.timestamp,
                response_time=data_point.avg_response_time,
                offset=data_point.avg_offset,
                delay=data_point.avg_delay,
                jitter=data_point.jitter,
                status="healthy" if data_point.success_rate > 0.8 else "warning"
            ))
        
        logger.info(f"Retornando {len(trend_responses)} pontos de tendência")
        return trend_responses
        
    except Exception as e:
        logger.error(f"Erro ao calcular tendência do servidor {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/query", response_model=List[MetricResponse])
async def query_metrics(
    query: MetricsQueryRequest,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Consulta avançada de métricas com filtros personalizados
    
    - **server_ids**: Lista de IDs dos servidores
    - **start_date**: Data de início
    - **end_date**: Data de fim
    - **metric_types**: Tipos de métricas a incluir
    - **aggregation**: Tipo de agregação (avg, min, max, sum)
    - **interval**: Intervalo de agregação (1m, 5m, 1h, 1d)
    """
    try:
        logger.info(f"Executando consulta avançada de métricas")
        
        # Validar período se especificado
        if query.start_date and query.end_date and query.end_date <= query.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data de fim deve ser posterior à data de início"
            )
        
        # Executar consulta personalizada
        metrics = db_service.query_metrics_advanced(
            server_ids=query.server_ids,
            start_date=query.start_date,
            end_date=query.end_date,
            metric_types=query.metric_types,
            aggregation=query.aggregation,
            interval=query.interval
        )
        
        # Converter para modelo de resposta
        metric_responses = []
        for metric in metrics:
            metric_responses.append(MetricResponse(
                server_id=metric.server_id,
                server_name=metric.server_name,
                timestamp=metric.timestamp,
                response_time=metric.response_time,
                offset=metric.offset,
                delay=metric.delay,
                jitter=metric.jitter,
                status=metric.status or "unknown"
            ))
        
        logger.info(f"Consulta retornou {len(metric_responses)} métricas")
        return metric_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na consulta avançada de métricas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )