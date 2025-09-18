@echo off
echo ========================================
echo  Instalador do Servico de Sincronizacao
echo ========================================
echo.

REM Verifica se esta executando como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Privilegios administrativos detectados.
) else (
    echo ERRO: Este script deve ser executado como administrador.
    echo Clique com o botao direito e selecione "Executar como administrador"
    pause
    exit /b 1
)

echo Instalando dependencias Python...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo Instalando servico Windows...
python windows_service.py install
if %errorLevel% neq 0 (
    echo ERRO: Falha ao instalar servico.
    pause
    exit /b 1
)

echo.
echo Iniciando servico...
python windows_service.py start
if %errorLevel% neq 0 (
    echo AVISO: Falha ao iniciar servico automaticamente.
    echo Voce pode iniciar manualmente com: net start WindowsTimeSyncService
)

echo.
echo ========================================
echo  Instalacao concluida com sucesso!
echo ========================================
echo.
echo O servico foi instalado e configurado para iniciar automaticamente.
echo Nome do servico: WindowsTimeSyncService
echo.
echo Comandos uteis:
echo   net start WindowsTimeSyncService    - Iniciar servico
echo   net stop WindowsTimeSyncService     - Parar servico
echo   python windows_service.py uninstall - Desinstalar servico
echo.
pause