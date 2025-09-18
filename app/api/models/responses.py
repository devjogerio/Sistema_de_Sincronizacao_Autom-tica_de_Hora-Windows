"""
Modelos de Resposta da API
Define as estruturas de dados retornadas pelos endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class StatusEnum(str, Enum):
    """Enum para status do sistema"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    OFFLINE = "offline"

class HealthResponse(BaseModel):
    """Resposta de verificação de saúde"""
    status: StatusEnum
    message: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ServerResponse(BaseModel):
    """Resposta com dados de servidor NTP"""
    id: int
    name: str
    host: str
    port: int = 123
    status: StatusEnum
    last_check: Optional[datetime] = None
    response_time: Optional[float] = None
    offset: Optional[float] = None
    delay: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class MetricResponse(BaseModel):
    """Resposta com métricas de servidor"""
    server_id: int
    server_name: str
    timestamp: datetime
    response_time: float
    offset: float
    delay: float
    jitter: Optional[float] = None
    status: StatusEnum

class MonitoringStatusResponse(BaseModel):
    """Status do monitoramento"""
    is_active: bool
    interval_seconds: int
    servers_count: int
    last_check: Optional[datetime] = None
    next_check: Optional[datetime] = None

class AlertResponse(BaseModel):
    """Resposta de alerta"""
    id: int
    server_id: int
    server_name: str
    alert_type: str
    message: str
    severity: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    is_resolved: bool = False

class StatisticsResponse(BaseModel):
    """Estatísticas avançadas"""
    server_id: int
    server_name: str
    period_start: datetime
    period_end: datetime
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    avg_offset: float
    std_offset: float
    uptime_percentage: float
    total_checks: int
    failed_checks: int

class ReportResponse(BaseModel):
    """Resposta de relatório"""
    id: str
    title: str
    type: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    file_path: str
    file_size: int

class ErrorResponse(BaseModel):
    """Resposta de erro padronizada"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class PaginatedResponse(BaseModel):
    """Resposta paginada genérica"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool