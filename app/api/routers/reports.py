"""
Router para Geração de Relatórios
Endpoints para criar e gerenciar relatórios em PDF
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
import logging
import sys
import os
import uuid
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.api.models.requests import ReportRequest
from app.api.models.responses import ReportResponse
from app.services.database_service import DatabaseService
from app.services.report_service import ReportService
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

# Criar router
router = APIRouter()

# Dependências
def get_database_service():
    """Obter instância do serviço de banco de dados"""
    return DatabaseService()

def get_report_service():
    """Obter instância do serviço de relatórios"""
    return ReportService()

@router.post("/", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_report(
    report_request: ReportRequest,
    background_tasks: BackgroundTasks,
    report_service: ReportService = Depends(get_report_service),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Criar novo relatório em PDF
    
    - **title**: Título do relatório
    - **report_type**: Tipo de relatório (summary, detailed, performance)
    - **period_start**: Data de início do período
    - **period_end**: Data de fim do período
    - **server_ids**: IDs dos servidores (opcional - todos se não especificado)
    - **include_charts**: Incluir gráficos no relatório
    """
    try:
        logger.info(f"Criando relatório: {report_request.title}")
        
        # Gerar ID único para o relatório
        report_id = str(uuid.uuid4())
        
        # Validar servidores se especificados
        if report_request.server_ids:
            for server_id in report_request.server_ids:
                server = db_service.get_server_by_id(server_id)
                if not server:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Servidor {server_id} não encontrado"
                    )
        
        # Criar entrada no banco de dados
        report_data = {
            'id': report_id,
            'title': report_request.title,
            'type': report_request.report_type,
            'period_start': report_request.period_start,
            'period_end': report_request.period_end,
            'server_ids': report_request.server_ids,
            'include_charts': report_request.include_charts,
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        db_service.create_report_entry(report_data)
        
        # Adicionar tarefa em background para gerar o relatório
        background_tasks.add_task(
            generate_report_background,
            report_id,
            report_request,
            report_service,
            db_service
        )
        
        logger.info(f"Relatório {report_id} adicionado à fila de geração")
        
        return ReportResponse(
            id=report_id,
            title=report_request.title,
            type=report_request.report_type,
            period_start=report_request.period_start,
            period_end=report_request.period_end,
            generated_at=datetime.now(),
            file_path="",  # Será preenchido quando o relatório for gerado
            file_size=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar relatório: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

async def generate_report_background(
    report_id: str,
    report_request: ReportRequest,
    report_service: ReportService,
    db_service: DatabaseService
):
    """
    Função para gerar relatório em background
    """
    try:
        logger.info(f"Iniciando geração do relatório {report_id}")
        
        # Atualizar status para 'generating'
        db_service.update_report_status(report_id, 'generating')
        
        # Gerar relatório
        file_path = await report_service.generate_report(
            report_id=report_id,
            title=report_request.title,
            report_type=report_request.report_type,
            period_start=report_request.period_start,
            period_end=report_request.period_end,
            server_ids=report_request.server_ids,
            include_charts=report_request.include_charts
        )
        
        # Obter tamanho do arquivo
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # Atualizar entrada no banco de dados
        db_service.update_report_completion(
            report_id=report_id,
            file_path=file_path,
            file_size=file_size,
            status='completed'
        )
        
        logger.info(f"Relatório {report_id} gerado com sucesso: {file_path}")
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório {report_id}: {e}")
        # Atualizar status para 'failed'
        db_service.update_report_status(report_id, 'failed', str(e))

@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    limit: int = 50,
    offset: int = 0,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Listar relatórios gerados
    
    - **limit**: Limite de registros retornados
    - **offset**: Número de registros para pular
    """
    try:
        logger.info(f"Listando relatórios - limit: {limit}, offset: {offset}")
        
        # Buscar relatórios
        reports = db_service.get_reports(limit=limit, offset=offset)
        
        # Converter para modelo de resposta
        report_responses = []
        for report in reports:
            report_responses.append(ReportResponse(
                id=report.id,
                title=report.title,
                type=report.type,
                period_start=report.period_start,
                period_end=report.period_end,
                generated_at=report.created_at,
                file_path=report.file_path or "",
                file_size=report.file_size or 0
            ))
        
        logger.info(f"Retornando {len(report_responses)} relatórios")
        return report_responses
        
    except Exception as e:
        logger.error(f"Erro ao listar relatórios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Obter detalhes de um relatório específico
    
    - **report_id**: ID único do relatório
    """
    try:
        logger.info(f"Buscando relatório {report_id}")
        
        # Buscar relatório
        report = db_service.get_report_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        return ReportResponse(
            id=report.id,
            title=report.title,
            type=report.type,
            period_start=report.period_start,
            period_end=report.period_end,
            generated_at=report.created_at,
            file_path=report.file_path or "",
            file_size=report.file_size or 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar relatório {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Fazer download do arquivo PDF do relatório
    
    - **report_id**: ID único do relatório
    """
    try:
        logger.info(f"Download do relatório {report_id}")
        
        # Buscar relatório
        report = db_service.get_report_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        # Verificar se arquivo existe
        if not report.file_path or not os.path.exists(report.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arquivo do relatório não encontrado"
            )
        
        # Verificar se relatório foi gerado com sucesso
        if report.status != 'completed':
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Relatório ainda não está pronto (status: {report.status})"
            )
        
        # Retornar arquivo
        filename = f"relatorio_{report.title.replace(' ', '_')}_{report_id[:8]}.pdf"
        
        return FileResponse(
            path=report.file_path,
            filename=filename,
            media_type='application/pdf'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no download do relatório {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Remover relatório e seu arquivo
    
    - **report_id**: ID único do relatório
    """
    try:
        logger.info(f"Removendo relatório {report_id}")
        
        # Buscar relatório
        report = db_service.get_report_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        # Remover arquivo se existir
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
                logger.info(f"Arquivo {report.file_path} removido")
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo {report.file_path}: {e}")
        
        # Remover entrada do banco de dados
        success = db_service.delete_report(report_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao remover relatório do banco de dados"
            )
        
        logger.info(f"Relatório {report_id} removido com sucesso")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover relatório {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )