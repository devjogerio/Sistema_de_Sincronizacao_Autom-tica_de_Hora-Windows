"""
Utilitários de validação para a aplicação NTP Monitor.
Contém funções para validar dados de entrada.
"""

import re
import socket
import ipaddress
from typing import Union, Tuple, Optional
from urllib.parse import urlparse


def validate_ntp_server(server: str) -> Tuple[bool, str]:
    """
    Valida endereço de servidor NTP.
    
    Args:
        server: Endereço do servidor (IP ou hostname)
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    if not server or not isinstance(server, str):
        return False, "Endereço do servidor não pode estar vazio"
    
    server = server.strip()
    
    if not server:
        return False, "Endereço do servidor não pode estar vazio"
    
    # Verifica se é um IP válido
    try:
        ipaddress.ip_address(server)
        return True, ""
    except ValueError:
        pass
    
    # Verifica se é um hostname válido
    if _is_valid_hostname(server):
        return True, ""
    
    return False, "Endereço do servidor inválido (deve ser IP ou hostname válido)"


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Valida endereço de email.
    
    Args:
        email: Endereço de email
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    if not email or not isinstance(email, str):
        return False, "Email não pode estar vazio"
    
    email = email.strip()
    
    if not email:
        return False, "Email não pode estar vazio"
    
    # Regex básico para validação de email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Formato de email inválido"
    
    # Verifica comprimento
    if len(email) > 254:
        return False, "Email muito longo (máximo 254 caracteres)"
    
    # Verifica partes local e domínio
    local, domain = email.rsplit('@', 1)
    
    if len(local) > 64:
        return False, "Parte local do email muito longa (máximo 64 caracteres)"
    
    if len(domain) > 253:
        return False, "Domínio do email muito longo (máximo 253 caracteres)"
    
    return True, ""


def validate_port(port: Union[int, str]) -> Tuple[bool, str]:
    """
    Valida número de porta.
    
    Args:
        port: Número da porta
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    try:
        port_num = int(port)
    except (ValueError, TypeError):
        return False, "Porta deve ser um número inteiro"
    
    if port_num < 1 or port_num > 65535:
        return False, "Porta deve estar entre 1 e 65535"
    
    return True, ""


def validate_timeout(timeout: Union[int, float, str]) -> Tuple[bool, str]:
    """
    Valida valor de timeout.
    
    Args:
        timeout: Valor do timeout em segundos
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    try:
        timeout_val = float(timeout)
    except (ValueError, TypeError):
        return False, "Timeout deve ser um número"
    
    if timeout_val <= 0:
        return False, "Timeout deve ser maior que zero"
    
    if timeout_val > 300:  # 5 minutos
        return False, "Timeout muito alto (máximo 300 segundos)"
    
    return True, ""


def validate_interval(interval: Union[int, str]) -> Tuple[bool, str]:
    """
    Valida intervalo de monitoramento.
    
    Args:
        interval: Intervalo em segundos
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    try:
        interval_val = int(interval)
    except (ValueError, TypeError):
        return False, "Intervalo deve ser um número inteiro"
    
    if interval_val < 10:
        return False, "Intervalo mínimo é 10 segundos"
    
    if interval_val > 86400:  # 24 horas
        return False, "Intervalo máximo é 86400 segundos (24 horas)"
    
    return True, ""


def validate_threshold(threshold: Union[int, float, str], 
                      min_val: float = 0.0, 
                      max_val: float = float('inf')) -> Tuple[bool, str]:
    """
    Valida valor de threshold/limite.
    
    Args:
        threshold: Valor do threshold
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    try:
        threshold_val = float(threshold)
    except (ValueError, TypeError):
        return False, "Threshold deve ser um número"
    
    if threshold_val < min_val:
        return False, f"Threshold deve ser maior ou igual a {min_val}"
    
    if threshold_val > max_val:
        return False, f"Threshold deve ser menor ou igual a {max_val}"
    
    return True, ""


def validate_file_path(file_path: str, must_exist: bool = False) -> Tuple[bool, str]:
    """
    Valida caminho de arquivo.
    
    Args:
        file_path: Caminho do arquivo
        must_exist: Se True, verifica se o arquivo existe
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    if not file_path or not isinstance(file_path, str):
        return False, "Caminho do arquivo não pode estar vazio"
    
    file_path = file_path.strip()
    
    if not file_path:
        return False, "Caminho do arquivo não pode estar vazio"
    
    # Verifica caracteres inválidos (Windows)
    invalid_chars = '<>:"|?*'
    if any(char in file_path for char in invalid_chars):
        return False, f"Caminho contém caracteres inválidos: {invalid_chars}"
    
    if must_exist:
        import os
        if not os.path.exists(file_path):
            return False, "Arquivo não encontrado"
        
        if not os.path.isfile(file_path):
            return False, "Caminho não aponta para um arquivo"
    
    return True, ""


def validate_directory_path(dir_path: str, must_exist: bool = False) -> Tuple[bool, str]:
    """
    Valida caminho de diretório.
    
    Args:
        dir_path: Caminho do diretório
        must_exist: Se True, verifica se o diretório existe
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    if not dir_path or not isinstance(dir_path, str):
        return False, "Caminho do diretório não pode estar vazio"
    
    dir_path = dir_path.strip()
    
    if not dir_path:
        return False, "Caminho do diretório não pode estar vazio"
    
    # Verifica caracteres inválidos (Windows)
    invalid_chars = '<>:"|?*'
    if any(char in dir_path for char in invalid_chars):
        return False, f"Caminho contém caracteres inválidos: {invalid_chars}"
    
    if must_exist:
        import os
        if not os.path.exists(dir_path):
            return False, "Diretório não encontrado"
        
        if not os.path.isdir(dir_path):
            return False, "Caminho não aponta para um diretório"
    
    return True, ""


def validate_smtp_config(host: str, port: Union[int, str], 
                        username: str = None, password: str = None) -> Tuple[bool, str]:
    """
    Valida configuração SMTP.
    
    Args:
        host: Servidor SMTP
        port: Porta SMTP
        username: Nome de usuário (opcional)
        password: Senha (opcional)
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    # Valida host
    if not host or not isinstance(host, str):
        return False, "Host SMTP não pode estar vazio"
    
    host = host.strip()
    if not host:
        return False, "Host SMTP não pode estar vazio"
    
    # Valida porta
    port_valid, port_msg = validate_port(port)
    if not port_valid:
        return False, f"Porta SMTP inválida: {port_msg}"
    
    # Valida credenciais se fornecidas
    if username is not None:
        if not isinstance(username, str) or not username.strip():
            return False, "Nome de usuário SMTP inválido"
    
    if password is not None:
        if not isinstance(password, str):
            return False, "Senha SMTP inválida"
    
    return True, ""


def _is_valid_hostname(hostname: str) -> bool:
    """
    Verifica se é um hostname válido.
    
    Args:
        hostname: Nome do host
        
    Returns:
        True se válido, False caso contrário
    """
    if len(hostname) > 253:
        return False
    
    if hostname[-1] == ".":
        hostname = hostname[:-1]
    
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    
    return all(allowed.match(x) for x in hostname.split("."))


def validate_json_config(config_data: dict) -> Tuple[bool, str]:
    """
    Valida estrutura de configuração JSON.
    
    Args:
        config_data: Dados de configuração
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    if not isinstance(config_data, dict):
        return False, "Configuração deve ser um objeto JSON válido"
    
    # Verifica seções obrigatórias
    required_sections = ['servers', 'monitoring']
    
    for section in required_sections:
        if section not in config_data:
            return False, f"Seção obrigatória '{section}' não encontrada"
    
    # Valida seção de servidores
    servers = config_data.get('servers', [])
    if not isinstance(servers, list):
        return False, "Seção 'servers' deve ser uma lista"
    
    if not servers:
        return False, "Pelo menos um servidor NTP deve ser configurado"
    
    for i, server in enumerate(servers):
        if not isinstance(server, dict):
            return False, f"Servidor {i+1} deve ser um objeto"
        
        if 'address' not in server:
            return False, f"Servidor {i+1} deve ter campo 'address'"
        
        # Valida endereço do servidor
        server_valid, server_msg = validate_ntp_server(server['address'])
        if not server_valid:
            return False, f"Servidor {i+1}: {server_msg}"
    
    return True, ""