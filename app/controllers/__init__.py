"""
Controladores da aplicação NTP Monitor.
Contém a lógica de controle e coordenação entre modelos e views.
"""

from .ntp_controller import NTPController
from .dashboard_controller import DashboardController

__all__ = [
    'NTPController',
    'DashboardController'
]