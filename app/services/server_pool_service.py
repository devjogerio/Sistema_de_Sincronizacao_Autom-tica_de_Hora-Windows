"""
Serviço de Pool de Servidores NTP
Responsável por gerenciar múltiplos servidores com balanceamento de carga e failover
"""

import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import statistics

from app.services.database_service import DatabaseService
from app.services.ntp_service import NTPService
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

class ServerStatus(Enum):
    """Status dos servidores no pool"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    MAINTENANCE = "maintenance"

class LoadBalanceMethod(Enum):
    """Métodos de balanceamento de carga"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    RANDOM = "random"

class ServerPoolService:
    """Serviço de gerenciamento de pool de servidores NTP"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.ntp_service = NTPService()
        
        # Configurações do pool
        self.max_concurrent_checks = 10
        self.failover_threshold = 3  # Falhas consecutivas para failover
        self.recovery_check_interval = timedelta(minutes=5)
        self.health_check_interval = timedelta(minutes=1)
        
        # Estado do pool
        self._server_pools = {}  # pool_id -> pool_config
        self._server_states = {}  # server_id -> server_state
        self._load_balance_counters = {}  # pool_id -> counter
        
        # Configurações de balanceamento
        self.default_load_balance_method = LoadBalanceMethod.WEIGHTED
        
        # Cache de performance
        self._performance_cache = {}
        self._cache_ttl = timedelta(minutes=5)
        
    async def create_server_pool(
        self,
        name: str,
        description: str,
        server_ids: List[int],
        load_balance_method: str = "weighted",
        weights: Optional[Dict[int, float]] = None,
        failover_enabled: bool = True
    ) -> int:
        """
        Criar um novo pool de servidores
        
        Args:
            name: Nome do pool
            description: Descrição do pool
            server_ids: IDs dos servidores no pool
            load_balance_method: Método de balanceamento
            weights: Pesos para balanceamento (opcional)
            failover_enabled: Habilitar failover automático
            
        Returns:
            ID do pool criado
        """
        try:
            logger.info(f"Criando pool de servidores: {name}")
            
            # Validar servidores
            valid_servers = []
            for server_id in server_ids:
                server = self.db_service.get_server_by_id(server_id)
                if server:
                    valid_servers.append(server_id)
                else:
                    logger.warning(f"Servidor {server_id} não encontrado, ignorando")
            
            if len(valid_servers) < 2:
                raise ValueError("Pool deve ter pelo menos 2 servidores válidos")
            
            # Criar pool no banco
            pool_data = {
                'name': name,
                'description': description,
                'load_balance_method': load_balance_method,
                'failover_enabled': failover_enabled,
                'created_at': datetime.now(),
                'status': 'active'
            }
            
            pool_id = self.db_service.create_server_pool(pool_data)
            
            # Adicionar servidores ao pool
            for server_id in valid_servers:
                weight = weights.get(server_id, 1.0) if weights else 1.0
                self.db_service.add_server_to_pool(pool_id, server_id, weight)
            
            # Inicializar estado do pool
            await self._initialize_pool_state(pool_id)
            
            logger.info(f"Pool {name} criado com sucesso (ID: {pool_id})")
            return pool_id
            
        except Exception as e:
            logger.error(f"Erro ao criar pool de servidores: {e}")
            raise
    
    async def _initialize_pool_state(self, pool_id: int) -> None:
        """Inicializar estado interno do pool"""
        try:
            pool_config = self.db_service.get_pool_config(pool_id)
            servers = self.db_service.get_pool_servers(pool_id)
            
            self._server_pools[pool_id] = {
                'config': pool_config,
                'servers': servers,
                'last_health_check': datetime.now(),
                'active_servers': [s['server_id'] for s in servers],
                'failed_servers': [],
                'current_server_index': 0
            }
            
            # Inicializar estados dos servidores
            for server in servers:
                server_id = server['server_id']
                self._server_states[server_id] = {
                    'status': ServerStatus.ACTIVE,
                    'consecutive_failures': 0,
                    'last_check': None,
                    'last_success': None,
                    'response_times': [],
                    'pool_id': pool_id
                }
            
            # Inicializar contador de balanceamento
            self._load_balance_counters[pool_id] = 0
            
            logger.info(f"Estado do pool {pool_id} inicializado")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar estado do pool {pool_id}: {e}")
            raise
    
    async def get_next_server(self, pool_id: int) -> Optional[Dict[str, Any]]:
        """
        Obter próximo servidor do pool baseado no método de balanceamento
        
        Args:
            pool_id: ID do pool
            
        Returns:
            Dados do servidor selecionado ou None se nenhum disponível
        """
        try:
            if pool_id not in self._server_pools:
                await self._initialize_pool_state(pool_id)
            
            pool_state = self._server_pools[pool_id]
            active_servers = pool_state['active_servers']
            
            if not active_servers:
                logger.warning(f"Nenhum servidor ativo no pool {pool_id}")
                return None
            
            # Obter método de balanceamento
            method = LoadBalanceMethod(pool_state['config']['load_balance_method'])
            
            # Selecionar servidor baseado no método
            if method == LoadBalanceMethod.ROUND_ROBIN:
                server_id = await self._select_round_robin(pool_id, active_servers)
            elif method == LoadBalanceMethod.WEIGHTED:
                server_id = await self._select_weighted(pool_id, active_servers)
            elif method == LoadBalanceMethod.LEAST_CONNECTIONS:
                server_id = await self._select_least_connections(pool_id, active_servers)
            elif method == LoadBalanceMethod.RESPONSE_TIME:
                server_id = await self._select_by_response_time(pool_id, active_servers)
            elif method == LoadBalanceMethod.RANDOM:
                server_id = random.choice(active_servers)
            else:
                # Fallback para round robin
                server_id = await self._select_round_robin(pool_id, active_servers)
            
            # Obter dados do servidor
            server_data = self.db_service.get_server_by_id(server_id)
            
            if server_data:
                logger.debug(f"Servidor selecionado do pool {pool_id}: {server_data['name']}")
                return server_data
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter próximo servidor do pool {pool_id}: {e}")
            return None
    
    async def _select_round_robin(self, pool_id: int, active_servers: List[int]) -> int:
        """Seleção round robin"""
        pool_state = self._server_pools[pool_id]
        current_index = pool_state['current_server_index']
        
        server_id = active_servers[current_index % len(active_servers)]
        pool_state['current_server_index'] = (current_index + 1) % len(active_servers)
        
        return server_id
    
    async def _select_weighted(self, pool_id: int, active_servers: List[int]) -> int:
        """Seleção baseada em pesos"""
        servers_with_weights = self.db_service.get_pool_servers_with_weights(pool_id)
        
        # Filtrar apenas servidores ativos
        active_weighted = [s for s in servers_with_weights if s['server_id'] in active_servers]
        
        if not active_weighted:
            return random.choice(active_servers)
        
        # Seleção baseada em pesos
        weights = [s['weight'] for s in active_weighted]
        server_ids = [s['server_id'] for s in active_weighted]
        
        return random.choices(server_ids, weights=weights)[0]
    
    async def _select_least_connections(self, pool_id: int, active_servers: List[int]) -> int:
        """Seleção baseada em menor número de conexões ativas"""
        # Para NTP, usamos como proxy o número de verificações recentes
        connection_counts = {}
        
        for server_id in active_servers:
            recent_checks = self.db_service.get_recent_server_checks(server_id, hours=1)
            connection_counts[server_id] = len(recent_checks)
        
        # Servidor com menos verificações recentes
        return min(connection_counts, key=connection_counts.get)
    
    async def _select_by_response_time(self, pool_id: int, active_servers: List[int]) -> int:
        """Seleção baseada no tempo de resposta"""
        response_times = {}
        
        for server_id in active_servers:
            if server_id in self._server_states:
                recent_times = self._server_states[server_id]['response_times']
                if recent_times:
                    response_times[server_id] = statistics.mean(recent_times[-10:])  # Média das últimas 10
                else:
                    response_times[server_id] = float('inf')
            else:
                response_times[server_id] = float('inf')
        
        # Servidor com menor tempo de resposta
        return min(response_times, key=response_times.get)
    
    async def check_pool_health(self, pool_id: int) -> Dict[str, Any]:
        """
        Verificar saúde do pool de servidores
        
        Args:
            pool_id: ID do pool
            
        Returns:
            Status de saúde do pool
        """
        try:
            logger.debug(f"Verificando saúde do pool {pool_id}")
            
            if pool_id not in self._server_pools:
                await self._initialize_pool_state(pool_id)
            
            pool_state = self._server_pools[pool_id]
            servers = pool_state['servers']
            
            health_results = []
            active_count = 0
            failed_count = 0
            
            # Verificar cada servidor
            for server_info in servers:
                server_id = server_info['server_id']
                server_data = self.db_service.get_server_by_id(server_id)
                
                if not server_data:
                    continue
                
                # Realizar verificação NTP
                try:
                    result = await self.ntp_service.check_server(
                        server_data['host'],
                        server_data.get('port', 123)
                    )
                    
                    # Atualizar estado do servidor
                    await self._update_server_state(server_id, result, True)
                    
                    health_results.append({
                        'server_id': server_id,
                        'server_name': server_data['name'],
                        'status': 'healthy',
                        'response_time': result.get('response_time', 0),
                        'offset': result.get('offset', 0)
                    })
                    
                    active_count += 1
                    
                except Exception as e:
                    # Atualizar estado do servidor (falha)
                    await self._update_server_state(server_id, {}, False)
                    
                    health_results.append({
                        'server_id': server_id,
                        'server_name': server_data['name'],
                        'status': 'failed',
                        'error': str(e)
                    })
                    
                    failed_count += 1
            
            # Atualizar lista de servidores ativos
            await self._update_active_servers(pool_id)
            
            # Calcular estatísticas do pool
            total_servers = len(servers)
            health_percentage = (active_count / total_servers * 100) if total_servers > 0 else 0
            
            pool_health = {
                'pool_id': pool_id,
                'total_servers': total_servers,
                'active_servers': active_count,
                'failed_servers': failed_count,
                'health_percentage': health_percentage,
                'status': 'healthy' if health_percentage >= 50 else 'degraded' if health_percentage > 0 else 'failed',
                'last_check': datetime.now(),
                'servers': health_results
            }
            
            # Atualizar timestamp da última verificação
            pool_state['last_health_check'] = datetime.now()
            
            logger.info(f"Verificação de saúde do pool {pool_id} concluída: {health_percentage:.1f}% saudável")
            
            return pool_health
            
        except Exception as e:
            logger.error(f"Erro na verificação de saúde do pool {pool_id}: {e}")
            raise
    
    async def _update_server_state(self, server_id: int, result: Dict[str, Any], success: bool) -> None:
        """Atualizar estado interno do servidor"""
        try:
            if server_id not in self._server_states:
                return
            
            state = self._server_states[server_id]
            state['last_check'] = datetime.now()
            
            if success:
                state['status'] = ServerStatus.ACTIVE
                state['consecutive_failures'] = 0
                state['last_success'] = datetime.now()
                
                # Atualizar tempos de resposta
                response_time = result.get('response_time', 0)
                state['response_times'].append(response_time)
                
                # Manter apenas os últimos 20 tempos
                if len(state['response_times']) > 20:
                    state['response_times'] = state['response_times'][-20:]
                
            else:
                state['consecutive_failures'] += 1
                
                # Marcar como falho se exceder threshold
                if state['consecutive_failures'] >= self.failover_threshold:
                    state['status'] = ServerStatus.FAILED
                    logger.warning(f"Servidor {server_id} marcado como falho após {state['consecutive_failures']} falhas consecutivas")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar estado do servidor {server_id}: {e}")
    
    async def _update_active_servers(self, pool_id: int) -> None:
        """Atualizar lista de servidores ativos do pool"""
        try:
            if pool_id not in self._server_pools:
                return
            
            pool_state = self._server_pools[pool_id]
            all_servers = [s['server_id'] for s in pool_state['servers']]
            
            active_servers = []
            failed_servers = []
            
            for server_id in all_servers:
                if server_id in self._server_states:
                    state = self._server_states[server_id]
                    if state['status'] == ServerStatus.ACTIVE:
                        active_servers.append(server_id)
                    elif state['status'] == ServerStatus.FAILED:
                        failed_servers.append(server_id)
                else:
                    # Assumir ativo se não há estado
                    active_servers.append(server_id)
            
            pool_state['active_servers'] = active_servers
            pool_state['failed_servers'] = failed_servers
            
            logger.debug(f"Pool {pool_id}: {len(active_servers)} ativos, {len(failed_servers)} falharam")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar servidores ativos do pool {pool_id}: {e}")
    
    async def attempt_server_recovery(self, pool_id: int) -> Dict[str, Any]:
        """
        Tentar recuperar servidores falhados do pool
        
        Args:
            pool_id: ID do pool
            
        Returns:
            Resultado da tentativa de recuperação
        """
        try:
            logger.info(f"Tentando recuperar servidores falhados do pool {pool_id}")
            
            if pool_id not in self._server_pools:
                await self._initialize_pool_state(pool_id)
            
            pool_state = self._server_pools[pool_id]
            failed_servers = pool_state['failed_servers'].copy()
            
            recovery_results = []
            recovered_count = 0
            
            for server_id in failed_servers:
                server_data = self.db_service.get_server_by_id(server_id)
                
                if not server_data:
                    continue
                
                try:
                    # Tentar verificação NTP
                    result = await self.ntp_service.check_server(
                        server_data['host'],
                        server_data.get('port', 123)
                    )
                    
                    # Servidor recuperado
                    await self._update_server_state(server_id, result, True)
                    
                    recovery_results.append({
                        'server_id': server_id,
                        'server_name': server_data['name'],
                        'status': 'recovered',
                        'response_time': result.get('response_time', 0)
                    })
                    
                    recovered_count += 1
                    logger.info(f"Servidor {server_data['name']} recuperado com sucesso")
                    
                except Exception as e:
                    recovery_results.append({
                        'server_id': server_id,
                        'server_name': server_data['name'],
                        'status': 'still_failed',
                        'error': str(e)
                    })
            
            # Atualizar lista de servidores ativos
            await self._update_active_servers(pool_id)
            
            return {
                'pool_id': pool_id,
                'attempted_recovery': len(failed_servers),
                'recovered_servers': recovered_count,
                'recovery_rate': (recovered_count / len(failed_servers) * 100) if failed_servers else 0,
                'results': recovery_results
            }
            
        except Exception as e:
            logger.error(f"Erro na tentativa de recuperação do pool {pool_id}: {e}")
            raise
    
    async def get_pool_statistics(self, pool_id: int) -> Dict[str, Any]:
        """
        Obter estatísticas detalhadas do pool
        
        Args:
            pool_id: ID do pool
            
        Returns:
            Estatísticas do pool
        """
        try:
            if pool_id not in self._server_pools:
                await self._initialize_pool_state(pool_id)
            
            pool_state = self._server_pools[pool_id]
            pool_config = pool_state['config']
            
            # Estatísticas básicas
            total_servers = len(pool_state['servers'])
            active_servers = len(pool_state['active_servers'])
            failed_servers = len(pool_state['failed_servers'])
            
            # Estatísticas de performance
            all_response_times = []
            server_stats = []
            
            for server_info in pool_state['servers']:
                server_id = server_info['server_id']
                server_data = self.db_service.get_server_by_id(server_id)
                
                if server_id in self._server_states:
                    state = self._server_states[server_id]
                    response_times = state['response_times']
                    
                    if response_times:
                        all_response_times.extend(response_times)
                        
                        server_stat = {
                            'server_id': server_id,
                            'server_name': server_data['name'] if server_data else f'Server {server_id}',
                            'status': state['status'].value,
                            'consecutive_failures': state['consecutive_failures'],
                            'avg_response_time': statistics.mean(response_times),
                            'min_response_time': min(response_times),
                            'max_response_time': max(response_times),
                            'last_success': state['last_success'].isoformat() if state['last_success'] else None
                        }
                    else:
                        server_stat = {
                            'server_id': server_id,
                            'server_name': server_data['name'] if server_data else f'Server {server_id}',
                            'status': state['status'].value,
                            'consecutive_failures': state['consecutive_failures'],
                            'avg_response_time': None,
                            'min_response_time': None,
                            'max_response_time': None,
                            'last_success': state['last_success'].isoformat() if state['last_success'] else None
                        }
                    
                    server_stats.append(server_stat)
            
            # Estatísticas agregadas
            pool_stats = {
                'pool_id': pool_id,
                'pool_name': pool_config['name'],
                'load_balance_method': pool_config['load_balance_method'],
                'failover_enabled': pool_config['failover_enabled'],
                'total_servers': total_servers,
                'active_servers': active_servers,
                'failed_servers': failed_servers,
                'availability_percentage': (active_servers / total_servers * 100) if total_servers > 0 else 0,
                'last_health_check': pool_state['last_health_check'].isoformat(),
                'server_statistics': server_stats
            }
            
            # Adicionar estatísticas de performance se houver dados
            if all_response_times:
                pool_stats['performance'] = {
                    'avg_response_time': statistics.mean(all_response_times),
                    'min_response_time': min(all_response_times),
                    'max_response_time': max(all_response_times),
                    'median_response_time': statistics.median(all_response_times),
                    'std_response_time': statistics.stdev(all_response_times) if len(all_response_times) > 1 else 0
                }
            
            return pool_stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do pool {pool_id}: {e}")
            raise
    
    async def start_pool_monitoring(self, pool_id: int) -> None:
        """Iniciar monitoramento contínuo do pool"""
        try:
            logger.info(f"Iniciando monitoramento do pool {pool_id}")
            
            while True:
                try:
                    # Verificar saúde do pool
                    await self.check_pool_health(pool_id)
                    
                    # Tentar recuperar servidores falhados
                    if pool_id in self._server_pools:
                        failed_servers = self._server_pools[pool_id]['failed_servers']
                        if failed_servers:
                            await self.attempt_server_recovery(pool_id)
                    
                    # Aguardar próxima verificação
                    await asyncio.sleep(self.health_check_interval.total_seconds())
                    
                except Exception as e:
                    logger.error(f"Erro no monitoramento do pool {pool_id}: {e}")
                    await asyncio.sleep(60)  # Aguardar 1 minuto em caso de erro
                    
        except asyncio.CancelledError:
            logger.info(f"Monitoramento do pool {pool_id} cancelado")
        except Exception as e:
            logger.error(f"Erro fatal no monitoramento do pool {pool_id}: {e}")
    
    async def get_all_pools(self) -> List[Dict[str, Any]]:
        """Obter todos os pools configurados"""
        try:
            return self.db_service.get_all_server_pools()
        except Exception as e:
            logger.error(f"Erro ao obter pools: {e}")
            raise