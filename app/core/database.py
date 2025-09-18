"""
Gerenciador de banco de dados para o NTP Monitor
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData, text

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """
    Classe base para todos os modelos SQLAlchemy
    """
    metadata = MetaData()


class DatabaseManager:
    """
    Gerenciador de conexões e sessões do banco de dados
    """
    
    def __init__(self, database_url: str, echo: bool = False):
        """
        Inicializa o gerenciador de banco de dados
        
        Args:
            database_url: URL de conexão com o banco
            echo: Se deve fazer log das queries SQL
        """
        self.database_url = database_url
        self.echo = echo
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
    
    async def initialize(self):
        """
        Inicializa o banco de dados e cria as tabelas
        """
        if self._initialized:
            return
        
        try:
            # Cria o engine
            self.engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                future=True
            )
            
            # Cria o factory de sessões
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Cria as tabelas
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("Banco de dados inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    async def close(self):
        """
        Fecha as conexões do banco de dados
        """
        if self.engine:
            await self.engine.dispose()
            logger.info("Conexões do banco de dados fechadas")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager para obter uma sessão do banco de dados
        
        Yields:
            AsyncSession: Sessão do banco de dados
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute_raw_sql(self, sql: str, params: dict = None) -> any:
        """
        Executa SQL bruto
        
        Args:
            sql: Query SQL para executar
            params: Parâmetros da query
            
        Returns:
            Resultado da query
        """
        async with self.get_session() as session:
            result = await session.execute(text(sql), params or {})
            return result
    
    async def health_check(self) -> bool:
        """
        Verifica se o banco de dados está funcionando
        
        Returns:
            True se o banco está funcionando, False caso contrário
        """
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Health check do banco falhou: {e}")
            return False