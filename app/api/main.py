"""
API REST Principal do Sistema NTP Monitor
Fornece endpoints para monitoramento e controle de servidores NTP
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import logging
from typing import List, Optional
import os
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.api.routers import servers, metrics, monitoring, reports
from app.api.models.responses import HealthResponse
from app.services.database_service import DatabaseService
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

# Configuração de segurança
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento do ciclo de vida da aplicação"""
    logger.info("Iniciando API NTP Monitor...")
    
    # Inicializar serviços
    try:
        db_service = DatabaseService()
        db_service.initialize()
        logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        raise
    
    yield
    
    logger.info("Encerrando API NTP Monitor...")



def create_api_app(
    db_manager=None,
    ntp_controller=None,
    monitoring_service=None,
    alert_service=None,
    pool_service=None
) -> FastAPI:
    """
    Cria e configura a aplicação FastAPI
    
    Args:
        db_manager: Gerenciador de banco de dados
        ntp_controller: Controlador NTP
        monitoring_service: Serviço de monitoramento
        alert_service: Serviço de alertas
        pool_service: Serviço de pools
        
    Returns:
        FastAPI: Aplicação configurada
    """
    
    # Criar aplicação FastAPI
    app = FastAPI(
        title="NTP Monitor API",
        description="API REST para monitoramento e controle de servidores NTP",
        version="3.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, especificar domínios específicos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Incluir routers
    app.include_router(servers.router, prefix="/api/v1/servers", tags=["Servidores"])
    app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Métricas"])
    app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoramento"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["Relatórios"])
    
    @app.get("/api", response_model=HealthResponse)
    async def api_root():
        """Endpoint raiz da API"""
        return HealthResponse(
            status="healthy",
            message="NTP Monitor API está funcionando",
            version="3.0.0"
        )
    
    @app.get("/api/health", response_model=HealthResponse)
    async def health_check():
        """Verificação de saúde da API"""
        try:
            # Verificar conexão com banco de dados se disponível
            if db_manager:
                db_healthy = await db_manager.health_check()
                if not db_healthy:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Banco de dados indisponível"
                    )
            
            return HealthResponse(
                status="healthy",
                message="Todos os serviços estão funcionando",
                version="3.0.0"
            )
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Serviço indisponível: {str(e)}"
            )
    
    return app


# Aplicação padrão para desenvolvimento
app = create_api_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )