"""
Utilitários de formatação para a aplicação NTP Monitor.
Contém funções para formatar dados para exibição.
"""

from datetime import datetime, timedelta
from typing import Union, Optional


def format_time(seconds: Union[int, float], precision: int = 3) -> str:
    """
    Formata tempo em segundos para exibição legível.
    
    Args:
        seconds: Tempo em segundos
        precision: Número de casas decimais
        
    Returns:
        String formatada (ex: "1.234s", "0.001s")
    """
    if seconds is None:
        return "N/A"
    
    try:
        seconds_val = float(seconds)
    except (ValueError, TypeError):
        return "N/A"
    
    if seconds_val < 0.001:
        return f"{seconds_val * 1000:.{precision}f}ms"
    elif seconds_val < 1.0:
        return f"{seconds_val * 1000:.{precision-1}f}ms"
    else:
        return f"{seconds_val:.{precision}f}s"


def format_offset(offset: Union[int, float], precision: int = 3) -> str:
    """
    Formata offset de tempo para exibição.
    
    Args:
        offset: Offset em segundos
        precision: Número de casas decimais
        
    Returns:
        String formatada com sinal (ex: "+0.123s", "-0.456s")
    """
    if offset is None:
        return "N/A"
    
    try:
        offset_val = float(offset)
    except (ValueError, TypeError):
        return "N/A"
    
    sign = "+" if offset_val >= 0 else ""
    
    if abs(offset_val) < 0.001:
        return f"{sign}{offset_val * 1000:.{precision}f}ms"
    elif abs(offset_val) < 1.0:
        return f"{sign}{offset_val * 1000:.{precision-1}f}ms"
    else:
        return f"{sign}{offset_val:.{precision}f}s"


def format_percentage(value: Union[int, float], precision: int = 1) -> str:
    """
    Formata valor como porcentagem.
    
    Args:
        value: Valor (0-100)
        precision: Número de casas decimais
        
    Returns:
        String formatada (ex: "95.5%")
    """
    if value is None:
        return "N/A"
    
    try:
        value_val = float(value)
    except (ValueError, TypeError):
        return "N/A"
    
    return f"{value_val:.{precision}f}%"


def format_bytes(bytes_val: Union[int, float]) -> str:
    """
    Formata tamanho em bytes para exibição legível.
    
    Args:
        bytes_val: Tamanho em bytes
        
    Returns:
        String formatada (ex: "1.5 KB", "2.3 MB")
    """
    if bytes_val is None:
        return "N/A"
    
    try:
        size = float(bytes_val)
    except (ValueError, TypeError):
        return "N/A"
    
    if size < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: Union[int, float]) -> str:
    """
    Formata duração em segundos para exibição legível.
    
    Args:
        seconds: Duração em segundos
        
    Returns:
        String formatada (ex: "2h 30m 15s", "45m 30s")
    """
    if seconds is None:
        return "N/A"
    
    try:
        total_seconds = int(float(seconds))
    except (ValueError, TypeError):
        return "N/A"
    
    if total_seconds < 0:
        return "0s"
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    parts = []
    
    if hours > 0:
        parts.append(f"{hours}h")
    
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def format_timestamp(timestamp: datetime, format_type: str = 'full') -> str:
    """
    Formata timestamp para exibição.
    
    Args:
        timestamp: Objeto datetime
        format_type: Tipo de formato ('full', 'date', 'time', 'short')
        
    Returns:
        String formatada
    """
    if timestamp is None:
        return "N/A"
    
    if not isinstance(timestamp, datetime):
        return "N/A"
    
    formats = {
        'full': '%Y-%m-%d %H:%M:%S',
        'date': '%Y-%m-%d',
        'time': '%H:%M:%S',
        'short': '%d/%m %H:%M',
        'iso': '%Y-%m-%dT%H:%M:%S'
    }
    
    format_str = formats.get(format_type, formats['full'])
    
    try:
        return timestamp.strftime(format_str)
    except (ValueError, AttributeError):
        return "N/A"


def format_relative_time(timestamp: datetime) -> str:
    """
    Formata timestamp como tempo relativo (ex: "há 5 minutos").
    
    Args:
        timestamp: Objeto datetime
        
    Returns:
        String formatada
    """
    if timestamp is None:
        return "N/A"
    
    if not isinstance(timestamp, datetime):
        return "N/A"
    
    try:
        now = datetime.now()
        diff = now - timestamp
        
        if diff.total_seconds() < 0:
            return "no futuro"
        
        seconds = int(diff.total_seconds())
        
        if seconds < 60:
            return f"há {seconds}s"
        
        minutes = seconds // 60
        if minutes < 60:
            return f"há {minutes}m"
        
        hours = minutes // 60
        if hours < 24:
            return f"há {hours}h"
        
        days = hours // 24
        if days < 30:
            return f"há {days}d"
        
        months = days // 30
        if months < 12:
            return f"há {months} mês(es)"
        
        years = months // 12
        return f"há {years} ano(s)"
        
    except (ValueError, AttributeError):
        return "N/A"


def format_server_status(is_available: bool, is_healthy: bool = None) -> str:
    """
    Formata status do servidor para exibição.
    
    Args:
        is_available: Se o servidor está disponível
        is_healthy: Se o servidor está saudável (opcional)
        
    Returns:
        String formatada com emoji e texto
    """
    if not is_available:
        return "🔴 Indisponível"
    
    if is_healthy is None:
        return "🟡 Disponível"
    
    if is_healthy:
        return "🟢 Saudável"
    else:
        return "🟡 Com problemas"


def format_priority(priority: int) -> str:
    """
    Formata prioridade do servidor.
    
    Args:
        priority: Valor da prioridade (1-10)
        
    Returns:
        String formatada
    """
    if priority is None:
        return "N/A"
    
    try:
        priority_val = int(priority)
    except (ValueError, TypeError):
        return "N/A"
    
    if priority_val <= 3:
        return f"🔴 Alta ({priority_val})"
    elif priority_val <= 6:
        return f"🟡 Média ({priority_val})"
    else:
        return f"🟢 Baixa ({priority_val})"


def format_stratum(stratum: int) -> str:
    """
    Formata stratum NTP para exibição.
    
    Args:
        stratum: Valor do stratum
        
    Returns:
        String formatada com descrição
    """
    if stratum is None:
        return "N/A"
    
    try:
        stratum_val = int(stratum)
    except (ValueError, TypeError):
        return "N/A"
    
    descriptions = {
        0: "Não especificado",
        1: "Referência primária",
        2: "Referência secundária",
        3: "Referência secundária",
        4: "Referência secundária"
    }
    
    if stratum_val in descriptions:
        return f"{stratum_val} ({descriptions[stratum_val]})"
    elif 2 <= stratum_val <= 15:
        return f"{stratum_val} (Referência secundária)"
    elif stratum_val == 16:
        return f"{stratum_val} (Não sincronizado)"
    else:
        return f"{stratum_val} (Inválido)"


def format_number(number: Union[int, float], precision: int = 2, 
                 thousands_sep: str = '.', decimal_sep: str = ',') -> str:
    """
    Formata número com separadores localizados.
    
    Args:
        number: Número a formatar
        precision: Casas decimais
        thousands_sep: Separador de milhares
        decimal_sep: Separador decimal
        
    Returns:
        String formatada
    """
    if number is None:
        return "N/A"
    
    try:
        num_val = float(number)
    except (ValueError, TypeError):
        return "N/A"
    
    # Formata com precisão especificada
    formatted = f"{num_val:.{precision}f}"
    
    # Separa parte inteira e decimal
    if '.' in formatted:
        integer_part, decimal_part = formatted.split('.')
    else:
        integer_part = formatted
        decimal_part = ""
    
    # Adiciona separador de milhares
    if len(integer_part) > 3:
        # Inverte, adiciona separadores e inverte novamente
        reversed_int = integer_part[::-1]
        separated = thousands_sep.join([reversed_int[i:i+3] for i in range(0, len(reversed_int), 3)])
        integer_part = separated[::-1]
    
    # Reconstrói o número
    if decimal_part and precision > 0:
        return f"{integer_part}{decimal_sep}{decimal_part}"
    else:
        return integer_part


def format_table_cell(value, max_width: int = 20, align: str = 'left') -> str:
    """
    Formata valor para exibição em célula de tabela.
    
    Args:
        value: Valor a formatar
        max_width: Largura máxima da célula
        align: Alinhamento ('left', 'right', 'center')
        
    Returns:
        String formatada e alinhada
    """
    if value is None:
        text = "N/A"
    else:
        text = str(value)
    
    # Trunca se necessário
    if len(text) > max_width:
        text = text[:max_width-3] + "..."
    
    # Aplica alinhamento
    if align == 'right':
        return text.rjust(max_width)
    elif align == 'center':
        return text.center(max_width)
    else:  # left
        return text.ljust(max_width)


def format_config_value(value, value_type: str = 'auto') -> str:
    """
    Formata valor de configuração para exibição.
    
    Args:
        value: Valor a formatar
        value_type: Tipo do valor ('auto', 'bool', 'time', 'size')
        
    Returns:
        String formatada
    """
    if value is None:
        return "Não definido"
    
    if value_type == 'bool':
        return "Sim" if value else "Não"
    
    elif value_type == 'time':
        return format_duration(value)
    
    elif value_type == 'size':
        return format_bytes(value)
    
    else:  # auto
        if isinstance(value, bool):
            return "Sim" if value else "Não"
        elif isinstance(value, (int, float)):
            return format_number(value)
        else:
            return str(value)