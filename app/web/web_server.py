"""
Web Server Module
Servidor web para servir a interface estática do NTP Monitor
"""

import os
import mimetypes
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebServer:
    """
    Servidor web para interface estática
    """
    
    def __init__(self, static_dir: str = None):
        """
        Inicializa o servidor web
        
        Args:
            static_dir: Diretório dos arquivos estáticos
        """
        self.app = FastAPI(
            title="NTP Monitor Web Interface",
            description="Interface web para monitoramento de servidores NTP",
            version="3.0.0"
        )
        
        # Define diretório estático
        if static_dir is None:
            current_dir = Path(__file__).parent
            static_dir = current_dir / "static"
        
        self.static_dir = Path(static_dir)
        
        # Configura CORS
        self.setup_cors()
        
        # Configura rotas
        self.setup_routes()
        
        logger.info(f"Servidor web inicializado com diretório estático: {self.static_dir}")
    
    def setup_cors(self):
        """
        Configura CORS para permitir acesso da interface web
        """
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Em produção, especificar domínios
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """
        Configura rotas do servidor web
        """
        
        @self.app.get("/", response_class=HTMLResponse)
        async def serve_index():
            """
            Serve a página principal
            """
            return await self.serve_file("index.html")
        
        @self.app.get("/health")
        async def health_check():
            """
            Endpoint de health check
            """
            return {
                "status": "healthy",
                "service": "web_interface",
                "static_dir": str(self.static_dir)
            }
        
        @self.app.get("/{file_path:path}")
        async def serve_static_file(file_path: str):
            """
            Serve arquivos estáticos
            
            Args:
                file_path: Caminho do arquivo
            """
            return await self.serve_file(file_path)
    
    async def serve_file(self, file_path: str):
        """
        Serve um arquivo estático
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            FileResponse: Resposta com o arquivo
        """
        # Remove barras iniciais e normaliza o caminho
        file_path = file_path.lstrip('/')
        
        # Se não especificado, serve index.html
        if not file_path or file_path == '/':
            file_path = 'index.html'
        
        # Constrói caminho completo
        full_path = self.static_dir / file_path
        
        # Verifica se o arquivo existe
        if not full_path.exists() or not full_path.is_file():
            # Se for uma rota SPA, serve index.html
            if not file_path.startswith(('css/', 'js/', 'images/', 'fonts/')):
                full_path = self.static_dir / 'index.html'
                if not full_path.exists():
                    raise HTTPException(status_code=404, detail="Arquivo não encontrado")
            else:
                raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Verifica se o arquivo está dentro do diretório permitido
        try:
            full_path.resolve().relative_to(self.static_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        # Determina o tipo MIME
        mime_type, _ = mimetypes.guess_type(str(full_path))
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        # Configura headers de cache baseado no tipo de arquivo
        headers = self.get_cache_headers(file_path, mime_type)
        
        return FileResponse(
            path=str(full_path),
            media_type=mime_type,
            headers=headers
        )
    
    def get_cache_headers(self, file_path: str, mime_type: str) -> dict:
        """
        Obtém headers de cache apropriados para o arquivo
        
        Args:
            file_path: Caminho do arquivo
            mime_type: Tipo MIME do arquivo
            
        Returns:
            dict: Headers de cache
        """
        headers = {}
        
        # Arquivos estáticos com cache longo
        if any(file_path.endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf']):
            headers['Cache-Control'] = 'public, max-age=31536000'  # 1 ano
        # HTML com cache curto
        elif file_path.endswith('.html'):
            headers['Cache-Control'] = 'public, max-age=300'  # 5 minutos
        # Outros arquivos com cache médio
        else:
            headers['Cache-Control'] = 'public, max-age=3600'  # 1 hora
        
        # Headers de segurança
        if mime_type.startswith('text/html'):
            headers.update({
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'strict-origin-when-cross-origin'
            })
        
        return headers
    
    def mount_api(self, api_app: FastAPI, path: str = "/api"):
        """
        Monta a API no servidor web
        
        Args:
            api_app: Aplicação FastAPI da API
            path: Caminho base para a API
        """
        self.app.mount(path, api_app)
        logger.info(f"API montada em {path}")
    
    def get_app(self) -> FastAPI:
        """
        Obtém a aplicação FastAPI
        
        Returns:
            FastAPI: Aplicação configurada
        """
        return self.app


def create_web_server(static_dir: str = None, api_app: FastAPI = None) -> WebServer:
    """
    Cria e configura o servidor web
    
    Args:
        static_dir: Diretório dos arquivos estáticos
        api_app: Aplicação FastAPI da API (opcional)
        
    Returns:
        WebServer: Servidor web configurado
    """
    web_server = WebServer(static_dir)
    
    # Monta a API se fornecida
    if api_app:
        web_server.mount_api(api_app)
    
    return web_server


if __name__ == "__main__":
    import uvicorn
    from pathlib import Path
    
    # Cria servidor web
    current_dir = Path(__file__).parent
    static_dir = current_dir / "static"
    
    web_server = create_web_server(str(static_dir))
    app = web_server.get_app()
    
    # Inicia servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        access_log=True
    )