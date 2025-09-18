/**
 * Pools Manager Module
 * Módulo responsável pelo gerenciamento de pools de servidores NTP
 */

class PoolsManager {
    constructor() {
        this.pools = [];
        this.availableServers = [];
        this.isInitialized = false;
        this.refreshInterval = null;
        this.refreshRate = 30000; // 30 segundos
    }

    /**
     * Inicializa o gerenciador de pools
     */
    async init() {
        if (this.isInitialized) return;

        try {
            await this.loadPools();
            await this.loadAvailableServers();
            this.setupEventListeners();
            this.startAutoRefresh();
            this.isInitialized = true;
            console.log('Gerenciador de pools inicializado');
        } catch (error) {
            console.error('Erro ao inicializar gerenciador de pools:', error);
            this.showError('Erro ao carregar pools');
        }
    }

    /**
     * Carrega lista de pools
     */
    async loadPools() {
        try {
            this.pools = await apiClient.getPools();
            this.renderPoolsGrid();
        } catch (error) {
            console.error('Erro ao carregar pools:', error);
            this.showPoolsError('Erro ao carregar lista de pools');
        }
    }

    /**
     * Carrega servidores disponíveis
     */
    async loadAvailableServers() {
        try {
            this.availableServers = await apiClient.getServers();
        } catch (error) {
            console.error('Erro ao carregar servidores:', error);
        }
    }

    /**
     * Renderiza grid de pools
     */
    renderPoolsGrid() {
        const container = document.getElementById('pools-grid');
        
        if (!this.pools || this.pools.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="card text-center">
                        <div class="card-body">
                            <i class="fas fa-layer-group fa-3x text-muted mb-3"></i>
                            <h5 class="card-title">Nenhum pool configurado</h5>
                            <p class="card-text text-muted">
                                Crie um pool para agrupar servidores NTP com balanceamento de carga
                            </p>
                            <button class="btn btn-primary" onclick="poolsManager.showCreatePoolModal()">
                                <i class="fas fa-plus me-1"></i>Criar Pool
                            </button>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        const html = this.pools.map(pool => this.createPoolCard(pool)).join('');
        container.innerHTML = html;
    }

    /**
     * Cria card de pool
     * @param {Object} pool - Dados do pool
     * @returns {string} HTML do card
     */
    createPoolCard(pool) {
        const statusBadge = this.getPoolStatusBadge(pool.status);
        const balancingMethod = this.getBalancingMethodLabel(pool.balancing_method);
        const activeServers = pool.servers ? pool.servers.filter(s => s.status === 'online').length : 0;
        const totalServers = pool.servers ? pool.servers.length : 0;

        return `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card pool-card fade-in" data-pool-id="${pool.id}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${this.escapeHtml(pool.name)}</h6>
                        ${statusBadge}
                    </div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <div class="col-6">
                                <small class="text-muted">Servidores Ativos</small>
                                <div class="h5 mb-0 text-success">${activeServers}/${totalServers}</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Balanceamento</small>
                                <div class="small">${balancingMethod}</div>
                            </div>
                        </div>
                        
                        ${pool.description ? `<p class="card-text small text-muted">${this.escapeHtml(pool.description)}</p>` : ''}
                        
                        <div class="servers-list mb-3">
                            <small class="text-muted">Servidores:</small>
                            <div class="mt-1">
                                ${this.renderPoolServers(pool.servers)}
                            </div>
                        </div>
                        
                        <div class="pool-stats">
                            <div class="row text-center">
                                <div class="col-4">
                                    <small class="text-muted">Avg Response</small>
                                    <div class="small fw-bold">${pool.avg_response_time || 0}ms</div>
                                </div>
                                <div class="col-4">
                                    <small class="text-muted">Requests</small>
                                    <div class="small fw-bold">${pool.total_requests || 0}</div>
                                </div>
                                <div class="col-4">
                                    <small class="text-muted">Uptime</small>
                                    <div class="small fw-bold">${pool.uptime_percentage || 0}%</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="btn-group w-100" role="group">
                            <button class="btn btn-sm btn-outline-primary" 
                                    onclick="poolsManager.testPool(${pool.id})" 
                                    title="Testar Pool">
                                <i class="fas fa-play"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" 
                                    onclick="poolsManager.editPool(${pool.id})" 
                                    title="Editar">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-info" 
                                    onclick="poolsManager.viewPoolMetrics(${pool.id})" 
                                    title="Métricas">
                                <i class="fas fa-chart-line"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" 
                                    onclick="poolsManager.deletePool(${pool.id})" 
                                    title="Remover">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderiza servidores do pool
     * @param {Array} servers - Lista de servidores
     * @returns {string} HTML dos servidores
     */
    renderPoolServers(servers) {
        if (!servers || servers.length === 0) {
            return '<span class="text-muted small">Nenhum servidor</span>';
        }

        return servers.map(server => {
            const statusClass = server.status === 'online' ? 'success' : 'danger';
            return `<span class="badge bg-${statusClass} me-1 mb-1">${this.escapeHtml(server.name)}</span>`;
        }).join('');
    }

    /**
     * Obtém badge de status do pool
     * @param {string} status - Status do pool
     * @returns {string} HTML do badge
     */
    getPoolStatusBadge(status) {
        const badges = {
            'active': '<span class="badge bg-success">Ativo</span>',
            'inactive': '<span class="badge bg-secondary">Inativo</span>',
            'degraded': '<span class="badge bg-warning">Degradado</span>',
            'failed': '<span class="badge bg-danger">Falhou</span>'
        };
        return badges[status] || badges.inactive;
    }

    /**
     * Obtém label do método de balanceamento
     * @param {string} method - Método de balanceamento
     * @returns {string} Label do método
     */
    getBalancingMethodLabel(method) {
        const methods = {
            'round_robin': 'Round Robin',
            'weighted': 'Ponderado',
            'least_connections': 'Menos Conexões',
            'response_time': 'Tempo de Resposta',
            'random': 'Aleatório'
        };
        return methods[method] || method;
    }

    /**
     * Exibe modal de criação de pool
     */
    showCreatePoolModal() {
        const modalHTML = `
            <div class="modal fade" id="createPoolModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Criar Pool de Servidores</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="createPoolForm">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="poolName" class="form-label">Nome do Pool</label>
                                            <input type="text" class="form-control" id="poolName" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="poolBalancingMethod" class="form-label">Método de Balanceamento</label>
                                            <select class="form-select" id="poolBalancingMethod" required>
                                                <option value="round_robin">Round Robin</option>
                                                <option value="weighted">Ponderado</option>
                                                <option value="least_connections">Menos Conexões</option>
                                                <option value="response_time">Tempo de Resposta</option>
                                                <option value="random">Aleatório</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label for="poolDescription" class="form-label">Descrição</label>
                                    <textarea class="form-control" id="poolDescription" rows="3"></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Servidores Disponíveis</label>
                                    <div id="availableServersList" class="border rounded p-3" style="max-height: 200px; overflow-y: auto;">
                                        ${this.renderAvailableServers()}
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="poolEnabled" checked>
                                        <label class="form-check-label" for="poolEnabled">
                                            Pool ativo
                                        </label>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" onclick="poolsManager.createPool()">Criar Pool</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove modal anterior se existir
        const existingModal = document.getElementById('createPoolModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('createPoolModal'));
        modal.show();
    }

    /**
     * Renderiza lista de servidores disponíveis
     * @returns {string} HTML dos servidores
     */
    renderAvailableServers() {
        if (!this.availableServers || this.availableServers.length === 0) {
            return '<p class="text-muted">Nenhum servidor disponível</p>';
        }

        return this.availableServers.map(server => `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="${server.id}" id="server_${server.id}">
                <label class="form-check-label" for="server_${server.id}">
                    <strong>${this.escapeHtml(server.name)}</strong> 
                    <small class="text-muted">(${this.escapeHtml(server.host)}:${server.port})</small>
                    <span class="badge bg-${server.status === 'online' ? 'success' : 'secondary'} ms-2">${server.status}</span>
                </label>
            </div>
        `).join('');
    }

    /**
     * Cria um novo pool
     */
    async createPool() {
        const form = document.getElementById('createPoolForm');
        const selectedServers = Array.from(document.querySelectorAll('#availableServersList input:checked'))
            .map(input => parseInt(input.value));

        if (selectedServers.length === 0) {
            this.showNotification('Selecione pelo menos um servidor', 'warning');
            return;
        }

        const poolData = {
            name: document.getElementById('poolName').value,
            description: document.getElementById('poolDescription').value,
            balancing_method: document.getElementById('poolBalancingMethod').value,
            enabled: document.getElementById('poolEnabled').checked,
            server_ids: selectedServers
        };

        try {
            await apiClient.createPool(poolData);
            bootstrap.Modal.getInstance(document.getElementById('createPoolModal')).hide();
            this.showNotification('Pool criado com sucesso', 'success');
            await this.loadPools();
        } catch (error) {
            console.error('Erro ao criar pool:', error);
            this.showNotification('Erro ao criar pool', 'error');
        }
    }

    /**
     * Edita um pool
     * @param {number} poolId - ID do pool
     */
    async editPool(poolId) {
        try {
            const pool = await apiClient.getPool(poolId);
            this.showEditPoolModal(pool);
        } catch (error) {
            console.error('Erro ao carregar dados do pool:', error);
            this.showNotification('Erro ao carregar dados do pool', 'error');
        }
    }

    /**
     * Exibe modal de edição de pool
     * @param {Object} pool - Dados do pool
     */
    showEditPoolModal(pool) {
        const modalHTML = `
            <div class="modal fade" id="editPoolModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Editar Pool</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editPoolForm">
                                <input type="hidden" id="editPoolId" value="${pool.id}">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="editPoolName" class="form-label">Nome do Pool</label>
                                            <input type="text" class="form-control" id="editPoolName" 
                                                   value="${this.escapeHtml(pool.name)}" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="editPoolBalancingMethod" class="form-label">Método de Balanceamento</label>
                                            <select class="form-select" id="editPoolBalancingMethod" required>
                                                <option value="round_robin" ${pool.balancing_method === 'round_robin' ? 'selected' : ''}>Round Robin</option>
                                                <option value="weighted" ${pool.balancing_method === 'weighted' ? 'selected' : ''}>Ponderado</option>
                                                <option value="least_connections" ${pool.balancing_method === 'least_connections' ? 'selected' : ''}>Menos Conexões</option>
                                                <option value="response_time" ${pool.balancing_method === 'response_time' ? 'selected' : ''}>Tempo de Resposta</option>
                                                <option value="random" ${pool.balancing_method === 'random' ? 'selected' : ''}>Aleatório</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label for="editPoolDescription" class="form-label">Descrição</label>
                                    <textarea class="form-control" id="editPoolDescription" rows="3">${this.escapeHtml(pool.description || '')}</textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Servidores Disponíveis</label>
                                    <div id="editAvailableServersList" class="border rounded p-3" style="max-height: 200px; overflow-y: auto;">
                                        ${this.renderAvailableServersForEdit(pool.servers)}
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="editPoolEnabled" ${pool.enabled ? 'checked' : ''}>
                                        <label class="form-check-label" for="editPoolEnabled">
                                            Pool ativo
                                        </label>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" onclick="poolsManager.savePoolEdit()">Salvar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove modal anterior se existir
        const existingModal = document.getElementById('editPoolModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('editPoolModal'));
        modal.show();
    }

    /**
     * Renderiza servidores disponíveis para edição
     * @param {Array} poolServers - Servidores do pool
     * @returns {string} HTML dos servidores
     */
    renderAvailableServersForEdit(poolServers) {
        if (!this.availableServers || this.availableServers.length === 0) {
            return '<p class="text-muted">Nenhum servidor disponível</p>';
        }

        const poolServerIds = poolServers ? poolServers.map(s => s.id) : [];

        return this.availableServers.map(server => {
            const isSelected = poolServerIds.includes(server.id);
            return `
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${server.id}" 
                           id="edit_server_${server.id}" ${isSelected ? 'checked' : ''}>
                    <label class="form-check-label" for="edit_server_${server.id}">
                        <strong>${this.escapeHtml(server.name)}</strong> 
                        <small class="text-muted">(${this.escapeHtml(server.host)}:${server.port})</small>
                        <span class="badge bg-${server.status === 'online' ? 'success' : 'secondary'} ms-2">${server.status}</span>
                    </label>
                </div>
            `;
        }).join('');
    }

    /**
     * Salva edição do pool
     */
    async savePoolEdit() {
        const poolId = document.getElementById('editPoolId').value;
        const selectedServers = Array.from(document.querySelectorAll('#editAvailableServersList input:checked'))
            .map(input => parseInt(input.value));

        if (selectedServers.length === 0) {
            this.showNotification('Selecione pelo menos um servidor', 'warning');
            return;
        }

        const poolData = {
            name: document.getElementById('editPoolName').value,
            description: document.getElementById('editPoolDescription').value,
            balancing_method: document.getElementById('editPoolBalancingMethod').value,
            enabled: document.getElementById('editPoolEnabled').checked,
            server_ids: selectedServers
        };

        try {
            await apiClient.updatePool(poolId, poolData);
            bootstrap.Modal.getInstance(document.getElementById('editPoolModal')).hide();
            this.showNotification('Pool atualizado com sucesso', 'success');
            await this.loadPools();
        } catch (error) {
            console.error('Erro ao atualizar pool:', error);
            this.showNotification('Erro ao atualizar pool', 'error');
        }
    }

    /**
     * Testa um pool
     * @param {number} poolId - ID do pool
     */
    async testPool(poolId) {
        const button = document.querySelector(`button[onclick="poolsManager.testPool(${poolId})"]`);
        const originalContent = button.innerHTML;
        
        try {
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            button.disabled = true;

            const result = await apiClient.testPool(poolId);
            
            if (result.success) {
                this.showNotification(`Pool testado com sucesso: ${result.active_servers}/${result.total_servers} servidores ativos`, 'success');
            } else {
                this.showNotification(`Falha no teste do pool: ${result.error}`, 'warning');
            }

            await this.loadPools();

        } catch (error) {
            console.error('Erro ao testar pool:', error);
            this.showNotification('Erro ao testar pool', 'error');
        } finally {
            button.innerHTML = originalContent;
            button.disabled = false;
        }
    }

    /**
     * Remove um pool
     * @param {number} poolId - ID do pool
     */
    async deletePool(poolId) {
        const pool = this.pools.find(p => p.id === poolId);
        if (!pool) return;

        const confirmed = confirm(`Tem certeza que deseja remover o pool "${pool.name}"?`);
        if (!confirmed) return;

        try {
            await apiClient.deletePool(poolId);
            this.showNotification('Pool removido com sucesso', 'success');
            await this.loadPools();
        } catch (error) {
            console.error('Erro ao remover pool:', error);
            this.showNotification('Erro ao remover pool', 'error');
        }
    }

    /**
     * Visualiza métricas de um pool
     * @param {number} poolId - ID do pool
     */
    async viewPoolMetrics(poolId) {
        const pool = this.pools.find(p => p.id === poolId);
        if (!pool) return;

        try {
            const metrics = await apiClient.getPoolMetrics(poolId);
            this.showPoolMetricsModal(pool, metrics);
        } catch (error) {
            console.error('Erro ao carregar métricas do pool:', error);
            this.showNotification('Erro ao carregar métricas do pool', 'error');
        }
    }

    /**
     * Exibe modal com métricas do pool
     * @param {Object} pool - Dados do pool
     * @param {Object} metrics - Métricas do pool
     */
    showPoolMetricsModal(pool, metrics) {
        const modalHTML = `
            <div class="modal fade" id="poolMetricsModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Métricas do Pool - ${this.escapeHtml(pool.name)}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-4">
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title">Servidores Ativos</h5>
                                            <p class="card-text h3 text-success">${metrics.active_servers}/${metrics.total_servers}</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title">Tempo Médio</h5>
                                            <p class="card-text h3">${metrics.avg_response_time}ms</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title">Total Requests</h5>
                                            <p class="card-text h3">${metrics.total_requests}</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title">Uptime</h5>
                                            <p class="card-text h3 text-info">${metrics.uptime_percentage}%</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Distribuição de Carga</h6>
                                    <canvas id="poolLoadChart" width="400" height="200"></canvas>
                                </div>
                                <div class="col-md-6">
                                    <h6>Tempo de Resposta por Servidor</h6>
                                    <canvas id="poolResponseChart" width="400" height="200"></canvas>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove modal anterior se existir
        const existingModal = document.getElementById('poolMetricsModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('poolMetricsModal'));
        modal.show();

        // Cria gráficos após o modal ser exibido
        modal._element.addEventListener('shown.bs.modal', () => {
            this.createPoolCharts(metrics);
        });
    }

    /**
     * Cria gráficos de métricas do pool
     * @param {Object} metrics - Dados das métricas
     */
    createPoolCharts(metrics) {
        // Gráfico de distribuição de carga
        const loadCtx = document.getElementById('poolLoadChart').getContext('2d');
        new Chart(loadCtx, {
            type: 'doughnut',
            data: {
                labels: metrics.server_distribution.map(s => s.name),
                datasets: [{
                    data: metrics.server_distribution.map(s => s.requests),
                    backgroundColor: [
                        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', 
                        '#e74a3b', '#858796', '#5a5c69'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // Gráfico de tempo de resposta
        const responseCtx = document.getElementById('poolResponseChart').getContext('2d');
        new Chart(responseCtx, {
            type: 'bar',
            data: {
                labels: metrics.server_distribution.map(s => s.name),
                datasets: [{
                    label: 'Tempo de Resposta (ms)',
                    data: metrics.server_distribution.map(s => s.avg_response_time),
                    backgroundColor: 'rgba(78, 115, 223, 0.8)',
                    borderColor: 'rgba(78, 115, 223, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Tempo (ms)'
                        }
                    }
                }
            }
        });
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Event listeners específicos dos pools
    }

    /**
     * Inicia atualização automática
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        this.refreshInterval = setInterval(() => {
            this.refresh();
        }, this.refreshRate);
    }

    /**
     * Para atualização automática
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Atualiza dados dos pools
     */
    async refresh() {
        try {
            await this.loadPools();
            await this.loadAvailableServers();
        } catch (error) {
            console.error('Erro ao atualizar pools:', error);
        }
    }

    /**
     * Exibe erro na grid de pools
     * @param {string} message - Mensagem de erro
     */
    showPoolsError(message) {
        const container = document.getElementById('pools-grid');
        container.innerHTML = `
            <div class="col-12">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                        <h5 class="card-title text-danger">${message}</h5>
                        <button class="btn btn-outline-primary" onclick="poolsManager.refresh()">
                            <i class="fas fa-sync-alt me-1"></i>Tentar Novamente
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Exibe notificação
     * @param {string} message - Mensagem
     * @param {string} type - Tipo da notificação
     */
    showNotification(message, type) {
        if (window.app && typeof window.app.showNotification === 'function') {
            window.app.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    /**
     * Exibe erro
     * @param {string} message - Mensagem de erro
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * Escapa HTML para prevenir XSS
     * @param {string} text - Texto a escapar
     * @returns {string} Texto escapado
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Destrói o gerenciador e limpa recursos
     */
    destroy() {
        this.stopAutoRefresh();
        this.pools = [];
        this.availableServers = [];
        this.isInitialized = false;
    }
}

// Instância global
const poolsManager = new PoolsManager();
window.poolsManager = poolsManager;
window.PoolsManager = PoolsManager;