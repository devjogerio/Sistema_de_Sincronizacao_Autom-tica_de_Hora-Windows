"""
Router para Controle de Monitoramento
Endpoints para gerenciar o sistema de monitoramento
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import logging
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.api.models.requests import MonitoringConfigRequest, AlertConfigRequest
from app.api.models.responses import MonitoringStatusResponse, AlertResponse
from app.services.database_service import DatabaseService
from app.controllers.ntp_controller import NTPController
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

# Criar router
router = APIRouter()

# Instância global do controlador (será inicializada quando necessário)
_ntp_controller = None

# Dependências
def get_database_service():
    """Obter instância do serviço de banco de dados"""
    return DatabaseService()

def get_ntp_controller():
    """Obter instância do controlador NTP"""
    global _ntp_controller
    if _ntp_controller is None:
        _ntp_controller = NTPController()
    return _ntp_controller

@router.get("/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status(
    ntp_controller: NTPController = Depends(get_ntp_controller),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Obter status atual do sistema de monitoramento
    
    Retorna informações sobre:
    - Se o monitoramento está ativo
    - Intervalo de verificação configurado
    - Número de servidores monitorados
    - Última verificação realizada
    """
    try:
        logger.info("Consultando status do monitoramento")
        
        # Obter status do controlador
        is_active = ntp_controller.is_monitoring_active()
        config = ntp_controller.get_monitoring_config()
        
        # Contar servidores ativos
        servers_count = db_service.count_active_servers()
        
        # Obter última verificação
        last_check = db_service.get_last_monitoring_check()
        
        # Calcular próxima verificação
        next_check = None
        if is_active and last_check and config:
            from datetime import timedelta
            next_check = last_check + timedelta(seconds=config.update_interval)
        
        return MonitoringStatusResponse(
            is_active=is_active,
            interval_seconds=config.update_interval if config else 60,
            servers_count=servers_count,
            last_check=last_check,
            next_check=next_check
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter status do monitoramento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/start", response_model=MonitoringStatusResponse)
async def start_monitoring(
    ntp_controller: NTPController = Depends(get_ntp_controller)
):
    """
    Iniciar o sistema de monitoramento
    
    Ativa o monitoramento automático de todos os servidores configurados
    """
    try:
        logger.info("Iniciando monitoramento")
        
        # Verificar se já está ativo
        if ntp_controller.is_monitoring_active():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Monitoramento já está ativo"
            )
        
        # Iniciar monitoramento
        success = ntp_controller.start_monitoring()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao iniciar monitoramento"
            )
        
        # Retornar status atualizado
        return await get_monitoring_status(ntp_controller)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao iniciar monitoramento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/stop", response_model=MonitoringStatusResponse)
async def stop_monitoring(
    ntp_controller: NTPController = Depends(get_ntp_controller)
):
    """
    Parar o sistema de monitoramento
    
    Desativa o monitoramento automático
    """
    try:
        logger.info("Parando monitoramento")
        
        # Verificar se está ativo
        if not ntp_controller.is_monitoring_active():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Monitoramento já está inativo"
            )
        
        # Parar monitoramento
        success = ntp_controller.stop_monitoring()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao parar monitoramento"
            )
        
        # Retornar status atualizado
        return await get_monitoring_status(ntp_controller)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao parar monitoramento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.put("/config", response_model=MonitoringStatusResponse)
async def update_monitoring_config(
    config: MonitoringConfigRequest,
    ntp_controller: NTPController = Depends(get_ntp_controller)
):
    """
    Atualizar configuração do monitoramento
    
    - **interval_seconds**: Intervalo entre verificações em segundos
    - **timeout_seconds**: Timeout para cada verificação
    - **retry_attempts**: Número de tentativas em caso de falha
    - **alert_threshold**: Limite para disparar alertas
    """
    try:
        logger.info(f"Atualizando configuração do monitoramento: {config.dict()}")
        
        # Atualizar configuração
        success = ntp_controller.update_monitoring_config(config.dict())
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao atualizar configuração"
            )
        
        # Se monitoramento estiver ativo, reiniciar com nova configuração
        if ntp_controller.is_monitoring_active():
            ntp_controller.restart_monitoring()
        
        # Retornar status atualizado
        return await get_monitoring_status(ntp_controller)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/check", response_model=dict)
async def manual_check(
    ntp_controller: NTPController = Depends(get_ntp_controller)
):
    """
    Executar verificação manual de todos os servidores
    
    Força uma verificação imediata independente do monitoramento automático
    """
    try:
        logger.info("Executando verificação manual")
        
        # Executar verificação
        results = ntp_controller.perform_manual_check()
        
        # Contar resultados
        total_servers = len(results)
        successful_checks = sum(1 for r in results if r.get('success', False))
        failed_checks = total_servers - successful_checks
        
        return {
            "message": "Verificação manual concluída",
            "total_servers": total_servers,
            "successful_checks": successful_checks,
            "failed_checks": failed_checks,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Erro na verificação manual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    active_only: bool = False,
    limit: int = 100,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Obter lista de alertas
    
    - **active_only**: Apenas alertas não resolvidos
    - **limit**: Limite de registros retornados
    """
    try:
        logger.info(f"Consultando alertas - active_only: {active_only}, limit: {limit}")
        
        # Buscar alertas
        alerts = db_service.get_alerts(active_only=active_only, limit=limit)
        
        # Converter para modelo de resposta
        alert_responses = []
        for alert in alerts:
            alert_responses.append(AlertResponse(
                id=alert.id,
                server_id=alert.server_id,
                server_name=alert.server_name,
                alert_type=alert.alert_type,
                message=alert.message,
                severity=alert.severity,
                created_at=alert.created_at,
                resolved_at=alert.resolved_at,
                is_resolved=alert.is_resolved
            ))
        
        logger.info(f"Retornando {len(alert_responses)} alertas")
        return alert_responses
        
    except Exception as e:
        logger.error(f"Erro ao consultar alertas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Marcar alerta como resolvido
    
    - **alert_id**: ID do alerta a ser resolvido
    """
    try:
        logger.info(f"Resolvendo alerta ID: {alert_id}")
        
        # Resolver alerta
        success = db_service.resolve_alert(alert_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alerta não encontrado"
            )
        
        return {"message": "Alerta resolvido com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao resolver alerta {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )