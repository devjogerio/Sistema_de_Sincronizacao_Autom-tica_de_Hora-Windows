"""
Modelos de Requisição da API
Define as estruturas de dados aceitas pelos endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class ServerCreateRequest(BaseModel):
    """Requisição para criar servidor NTP"""
    name: str = Field(..., min_length=1, max_length=100, description="Nome do servidor")
    host: str = Field(..., min_length=1, max_length=255, description="Endereço do servidor")
    port: int = Field(default=123, ge=1, le=65535, description="Porta do servidor")
    description: Optional[str] = Field(None, max_length=500, description="Descrição opcional")
    
    @validator('name')
    def validate_name(cls, v):
        """Validar nome do servidor"""
        if not v.strip():
            raise ValueError('Nome não pode estar vazio')
        return v.strip()
    
    @validator('host')
    def validate_host(cls, v):
        """Validar formato do host"""
        # Regex básica para IP ou hostname
        ip_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        
        if not (re.match(ip_pattern, v) or re.match(hostname_pattern, v)):
            raise ValueError('Formato de host inválido')
        return v

class ServerUpdateRequest(BaseModel):
    """Requisição para atualizar servidor NTP"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Nome não pode estar vazio')
        return v.strip() if v else v
    
    @validator('host')
    def validate_host(cls, v):
        if v is not None:
            ip_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
            hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            
            if not (re.match(ip_pattern, v) or re.match(hostname_pattern, v)):
                raise ValueError('Formato de host inválido')
        return v

class MonitoringConfigRequest(BaseModel):
    """Configuração do monitoramento"""
    interval_seconds: int = Field(..., ge=10, le=3600, description="Intervalo em segundos")
    timeout_seconds: int = Field(default=5, ge=1, le=30, description="Timeout em segundos")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="Tentativas de retry")
    alert_threshold: float = Field(default=1.0, ge=0.1, le=10.0, description="Limite para alertas")

class AlertConfigRequest(BaseModel):
    """Configuração de alertas"""
    server_id: Optional[int] = None
    alert_type: str = Field(..., description="Tipo de alerta")
    threshold_value: float = Field(..., description="Valor limite")
    enabled: bool = Field(default=True, description="Alerta ativo")
    cooldown_minutes: int = Field(default=5, ge=1, le=1440, description="Cooldown em minutos")

class ReportRequest(BaseModel):
    """Requisição para gerar relatório"""
    title: str = Field(..., min_length=1, max_length=200, description="Título do relatório")
    report_type: str = Field(..., description="Tipo de relatório")
    period_start: datetime = Field(..., description="Data de início")
    period_end: datetime = Field(..., description="Data de fim")
    server_ids: Optional[List[int]] = Field(None, description="IDs dos servidores")
    include_charts: bool = Field(default=True, description="Incluir gráficos")
    
    @validator('period_end')
    def validate_period(cls, v, values):
        """Validar período do relatório"""
        if 'period_start' in values and v <= values['period_start']:
            raise ValueError('Data de fim deve ser posterior à data de início')
        return v

class MetricsQueryRequest(BaseModel):
    """Consulta de métricas"""
    server_ids: Optional[List[int]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metric_types: Optional[List[str]] = None
    aggregation: str = Field(default="avg", description="Tipo de agregação")
    interval: str = Field(default="1h", description="Intervalo de agregação")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        """Validar datas da consulta"""
        if 'start_date' in values and values['start_date'] and v and v <= values['start_date']:
            raise ValueError('Data de fim deve ser posterior à data de início')
        return v