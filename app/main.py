"""
NTP Monitor - Sistema de Monitoramento de Servidores NTP
Aplicação principal que integra todos os componentes do sistema
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

# Importações locais
from app.core.config import get_settings
from app.core.database import DatabaseManager
from app.api.main import create_api_app
from app.controllers.ntp_controller import NTPController

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NTPMonitorApp:
    """
    Aplicação principal do NTP Monitor
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = None
        self.ntp_controller = None
        self.api_app = None
        self.app = None
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self):
        """
        Inicializa todos os componentes da aplicação
        """
        try:
            # Inicializa banco de dados
            self.db_manager = DatabaseManager(self.settings.database_url)
            await self.db_manager.initialize()
            logger.info("Banco de dados inicializado")
            
            # Inicializa controlador NTP
            self.ntp_controller = NTPController()
            logger.info("Controlador NTP inicializado")
            
            # Cria aplicação API
            self.api_app = create_api_app()
            logger.info("API REST criada")
            
            self.app = self.api_app
            logger.info("Interface web configurada")
            
            logger.info("NTP Monitor inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar aplicação: {e}")
            raise
    
    async def start_background_tasks(self):
        """
        Inicia tarefas em background
        """
        try:
            # Inicia monitoramento NTP se habilitado
            if hasattr(self.settings, 'auto_monitoring_enabled') and self.settings.auto_monitoring_enabled:
                if self.ntp_controller:
                    self.ntp_controller.start_monitoring()
                    logger.info("Monitoramento NTP iniciado")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar tarefas em background: {e}")
            raise
    
    async def shutdown(self):
        """
        Finaliza a aplicação graciosamente
        """
        try:
            logger.info("Iniciando shutdown da aplicação...")
            
            # Para monitoramento NTP
            if self.ntp_controller:
                self.ntp_controller.stop_monitoring()
                logger.info("Monitoramento NTP parado")
            
            # Fecha conexões do banco
            if self.db_manager:
                await self.db_manager.close()
                logger.info("Conexões do banco fechadas")
            
            logger.info("Shutdown concluído")
            
        except Exception as e:
            logger.error(f"Erro durante shutdown: {e}")
    
    def setup_signal_handlers(self):
        """
        Configura handlers para sinais do sistema
        """
        def signal_handler(signum, frame):
            logger.info(f"Sinal {signum} recebido, iniciando shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """
        Executa a aplicação
        """
        try:
            # Configura handlers de sinal
            self.setup_signal_handlers()
            
            # Inicializa componentes
            await self.initialize()
            
            # Inicia tarefas em background
            await self.start_background_tasks()
            
            # Configura servidor
            config = uvicorn.Config(
                app=self.app,
                host=self.settings.host,
                port=self.settings.port,
                log_level=self.settings.log_level.lower(),
                access_log=True
            )
            
            server = uvicorn.Server(config)
            
            # Inicia servidor em background
            server_task = asyncio.create_task(server.serve())
            
            logger.info(f"Servidor iniciado em http://{self.settings.host}:{self.settings.port}")
            logger.info(f"Interface web disponível em: http://{self.settings.host}:{self.settings.port}")
            logger.info(f"API REST disponível em: http://{self.settings.host}:{self.settings.port}/api")
            logger.info("Pressione Ctrl+C para parar")
            
            # Aguarda sinal de shutdown
            await self._shutdown_event.wait()
            
            # Para o servidor
            server.should_exit = True
            await server_task
            
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
            raise
        finally:
            await self.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação FastAPI
    """
    # Startup
    logger.info("Aplicação iniciando...")
    yield
    # Shutdown
    logger.info("Aplicação finalizando...")


async def main():
    """
    Função principal
    """
    app = NTPMonitorApp()
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)