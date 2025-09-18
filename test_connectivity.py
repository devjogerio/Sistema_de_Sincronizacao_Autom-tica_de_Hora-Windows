"""
Script de teste para verificar conectividade NTP sem privilégios administrativos.
"""

from config import Config
from logger_config import setup_logging, get_logger
from ntp_client import NTPClient

def test_ntp_connectivity():
    """Testa conectividade e funcionalidades NTP."""
    
    # Inicializa logging
    setup_logging()
    logger = get_logger()
    
    print("=== TESTE DE CONECTIVIDADE NTP ===")
    print(f"Servidor NTP: {Config.NTP_SERVER}")
    print(f"Timeout: {Config.NTP_TIMEOUT}s")
    print(f"Tolerância: {Config.TIME_TOLERANCE_SECONDS}s")
    print()
    
    # Cria cliente NTP
    ntp_client = NTPClient()
    
    # Testa conectividade
    print("1. Testando conectividade...")
    connectivity = ntp_client.test_connectivity()
    print(f"   Resultado: {'✓ OK' if connectivity else '✗ FALHA'}")
    
    if not connectivity:
        print("   ERRO: Não foi possível conectar ao servidor NTP")
        return False
    
    # Obtém hora da rede
    print("\n2. Obtendo hora da rede...")
    network_time = ntp_client.get_network_time()
    if network_time:
        print(f"   Hora da rede: {network_time}")
    else:
        print("   ERRO: Não foi possível obter hora da rede")
        return False
    
    # Obtém hora do sistema
    print("\n3. Obtendo hora do sistema...")
    system_time = ntp_client.get_system_time()
    print(f"   Hora do sistema: {system_time}")
    
    # Calcula diferença
    print("\n4. Calculando diferença...")
    difference = ntp_client.calculate_time_difference(network_time, system_time)
    print(f"   Diferença: {difference:.2f} segundos")
    
    # Verifica se precisa sincronizar
    print("\n5. Verificando necessidade de sincronização...")
    needs_sync, _, _ = ntp_client.needs_synchronization()
    print(f"   Precisa sincronizar: {'Sim' if needs_sync else 'Não'}")
    
    print("\n=== RESULTADO DO TESTE ===")
    if abs(difference) <= Config.TIME_TOLERANCE_SECONDS:
        print("✓ Sistema está sincronizado!")
    else:
        print(f"⚠ Sistema fora de sincronização ({difference:.2f}s)")
        print("  Execute como administrador para sincronizar")
    
    print(f"\nConectividade NTP: {'✓ OK' if connectivity else '✗ FALHA'}")
    print("==========================")
    
    return True

if __name__ == "__main__":
    try:
        test_ntp_connectivity()
    except Exception as e:
        print(f"Erro durante teste: {e}")