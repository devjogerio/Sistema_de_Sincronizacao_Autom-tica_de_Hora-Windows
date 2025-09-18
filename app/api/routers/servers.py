"""
Router para Gerenciamento de Servidores NTP
Endpoints para CRUD e operações com servidores
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
import logging
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.api.models.requests import ServerCreateRequest, ServerUpdateRequest
from app.api.models.responses import ServerResponse, ErrorResponse
from app.services.database_service import DatabaseService
from app.services.ntp_service import NTPService
from app.models.server_config import ServerConfig
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

# Criar router
router = APIRouter()

# Dependências
def get_database_service():
    """Obter instância do serviço de banco de dados"""
    return DatabaseService()

def get_ntp_service():
    """Obter instância do serviço NTP"""
    return NTPService()

@router.get("/", response_model=List[ServerResponse])
async def list_servers(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    active_only: bool = Query(False, description="Apenas servidores ativos"),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Listar servidores NTP configurados
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Limite máximo de registros retornados
    - **active_only**: Filtrar apenas servidores ativos
    """
    try:
        logger.info(f"Listando servidores - skip: {skip}, limit: {limit}, active_only: {active_only}")
        
        # Buscar servidores no banco de dados
        servers = db_service.get_servers(skip=skip, limit=limit, active_only=active_only)
        
        # Converter para modelo de resposta
        server_responses = []
        for server in servers:
            server_responses.append(ServerResponse(
                id=server.id,
                name=server.name,
                host=server.host,
                port=server.port,
                status=server.status or "offline",
                last_check=server.last_check,
                response_time=server.response_time,
                offset=server.offset,
                delay=server.delay,
                created_at=server.created_at,
                updated_at=server.updated_at
            ))
        
        logger.info(f"Retornando {len(server_responses)} servidores")
        return server_responses
        
    except Exception as e:
        logger.error(f"Erro ao listar servidores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Obter detalhes de um servidor específico
    
    - **server_id**: ID único do servidor
    """
    try:
        logger.info(f"Buscando servidor ID: {server_id}")
        
        server = db_service.get_server_by_id(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servidor não encontrado"
            )
        
        return ServerResponse(
            id=server.id,
            name=server.name,
            host=server.host,
            port=server.port,
            status=server.status or "offline",
            last_check=server.last_check,
            response_time=server.response_time,
            offset=server.offset,
            delay=server.delay,
            created_at=server.created_at,
            updated_at=server.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar servidor {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: ServerCreateRequest,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Criar novo servidor NTP
    
    - **name**: Nome identificador do servidor
    - **host**: Endereço IP ou hostname do servidor
    - **port**: Porta do serviço NTP (padrão: 123)
    - **description**: Descrição opcional do servidor
    """
    try:
        logger.info(f"Criando servidor: {server_data.name} ({server_data.host})")
        
        # Verificar se já existe servidor com mesmo nome ou host
        existing = db_service.get_server_by_name_or_host(server_data.name, server_data.host)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe servidor com este nome ou host"
            )
        
        # Criar configuração do servidor
        server_config = ServerConfig(
            name=server_data.name,
            host=server_data.host,
            port=server_data.port,
            description=server_data.description
        )
        
        # Salvar no banco de dados
        server_id = db_service.create_server(server_config)
        
        # Buscar servidor criado
        created_server = db_service.get_server_by_id(server_id)
        
        logger.info(f"Servidor criado com sucesso - ID: {server_id}")
        
        return ServerResponse(
            id=created_server.id,
            name=created_server.name,
            host=created_server.host,
            port=created_server.port,
            status="offline",
            last_check=None,
            response_time=None,
            offset=None,
            delay=None,
            created_at=created_server.created_at,
            updated_at=created_server.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar servidor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    server_data: ServerUpdateRequest,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Atualizar servidor existente
    
    - **server_id**: ID do servidor a ser atualizado
    - Campos opcionais: name, host, port, description, is_active
    """
    try:
        logger.info(f"Atualizando servidor ID: {server_id}")
        
        # Verificar se servidor existe
        existing_server = db_service.get_server_by_id(server_id)
        if not existing_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servidor não encontrado"
            )
        
        # Atualizar servidor
        updated = db_service.update_server(server_id, server_data.dict(exclude_unset=True))
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha ao atualizar servidor"
            )
        
        # Buscar servidor atualizado
        updated_server = db_service.get_server_by_id(server_id)
        
        logger.info(f"Servidor {server_id} atualizado com sucesso")
        
        return ServerResponse(
            id=updated_server.id,
            name=updated_server.name,
            host=updated_server.host,
            port=updated_server.port,
            status=updated_server.status or "offline",
            last_check=updated_server.last_check,
            response_time=updated_server.response_time,
            offset=updated_server.offset,
            delay=updated_server.delay,
            created_at=updated_server.created_at,
            updated_at=updated_server.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar servidor {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Remover servidor
    
    - **server_id**: ID do servidor a ser removido
    """
    try:
        logger.info(f"Removendo servidor ID: {server_id}")
        
        # Verificar se servidor existe
        existing_server = db_service.get_server_by_id(server_id)
        if not existing_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servidor não encontrado"
            )
        
        # Remover servidor
        deleted = db_service.delete_server(server_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha ao remover servidor"
            )
        
        logger.info(f"Servidor {server_id} removido com sucesso")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover servidor {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/{server_id}/test", response_model=ServerResponse)
async def test_server(
    server_id: int,
    db_service: DatabaseService = Depends(get_database_service),
    ntp_service: NTPService = Depends(get_ntp_service)
):
    """
    Testar conectividade com servidor NTP
    
    - **server_id**: ID do servidor a ser testado
    """
    try:
        logger.info(f"Testando servidor ID: {server_id}")
        
        # Buscar servidor
        server = db_service.get_server_by_id(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servidor não encontrado"
            )
        
        # Testar conectividade
        result = ntp_service.check_server(server.host, server.port)
        
        # Atualizar status no banco
        update_data = {
            'status': 'healthy' if result.success else 'error',
            'last_check': result.timestamp,
            'response_time': result.response_time,
            'offset': result.offset,
            'delay': result.delay
        }
        db_service.update_server(server_id, update_data)
        
        # Buscar servidor atualizado
        updated_server = db_service.get_server_by_id(server_id)
        
        logger.info(f"Teste do servidor {server_id} concluído - Status: {result.success}")
        
        return ServerResponse(
            id=updated_server.id,
            name=updated_server.name,
            host=updated_server.host,
            port=updated_server.port,
            status=updated_server.status,
            last_check=updated_server.last_check,
            response_time=updated_server.response_time,
            offset=updated_server.offset,
            delay=updated_server.delay,
            created_at=updated_server.created_at,
            updated_at=updated_server.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao testar servidor {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )