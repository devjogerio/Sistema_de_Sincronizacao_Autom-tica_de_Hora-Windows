/**
 * Servers Manager Module
 * Módulo responsável pelo gerenciamento de servidores NTP
 */

class ServersManager {
    constructor() {
        this.servers = [];
        this.isInitialized = false;
        this.refreshInterval = null;
        this.refreshRate = 30000; // 30 segundos
    }

    /**
     * Inicializa o gerenciador de servidores
     */
    async init() {
        if (this.isInitialized) return;

        try {
            await this.loadServers();
            this.setupEventListeners();
            this.startAutoRefresh();
            this.isInitialized = true;
            console.log('Gerenciador de servidores inicializado');
        } catch (error) {
            console.error('Erro ao inicializar gerenciador de servidores:', error);
            this.showError('Erro ao carregar servidores');
        }
    }

    /**
     * Carrega lista de servidores
     */
    async loadServers() {
        try {
            this.servers = await apiClient.getServers();
            this.renderServersTable();
        } catch (error) {
            console.error('Erro ao carregar servidores:', error);
            this.showServerError('Erro ao carregar lista de servidores');
        }
    }

    /**
     * Renderiza tabela de servidores
     */
    renderServersTable() {
        const tbody = document.getElementById('servers-table-body');
        
        if (!this.servers || this.servers.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted">
                        <i class="fas fa-server fa-2x mb-2"></i>
                        <br>Nenhum servidor configurado
                        <br><small>Clique em "Adicionar Servidor" para começar</small>
                    </td>
                </tr>
            `;
            return;
        }

        const html = this.servers.map(server => this.createServerRow(server)).join('');
        tbody.innerHTML = html;
    }

    /**
     * Cria linha da tabela para um servidor
     * @param {Object} server - Dados do servidor
     * @returns {string} HTML da linha
     */
    createServerRow(server) {
        const statusBadge = this.getStatusBadge(server.status);
        const lastCheck = server.last_check ? this.formatDateTime(server.last_check) : 'Nunca';
        const responseTime = server.response_time ? `${server.response_time}ms` : '-';
        const offset = server.offset !== null ? `${server.offset}ms` : '-';

        return `
            <tr data-server-id="${server.id}" class="fade-in">
                <td>
                    <div class="d-flex align-items-center">
                        <div class="status-indicator status-${server.status.toLowerCase()}"></div>
                        <div>
                            <div class="fw-bold">${this.escapeHtml(server.name)}</div>
                            ${server.description ? `<small class="text-muted">${this.escapeHtml(server.description)}</small>` : ''}
                        </div>
                    </div>
                </td>
                <td>
                    <code>${this.escapeHtml(server.host)}:${server.port}</code>
                </td>
                <td>${statusBadge}</td>
                <td>
                    <span title="${lastCheck}">${this.formatTimeAgo(server.last_check)}</span>
                </td>
                <td>
                    <span class="${this.getResponseTimeClass(server.response_time)}">${responseTime}</span>
                </td>
                <td>
                    <span class="${this.getOffsetClass(server.offset)}">${offset}</span>
                </td>
                <td class="server-actions">
                    <button class="btn btn-sm btn-outline-primary me-1" 
                            onclick="serversManager.testServer(${server.id})" 
                            title="Testar Conectividade">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-secondary me-1" 
                            onclick="serversManager.editServer(${server.id})" 
                            title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-info me-1" 
                            onclick="serversManager.viewMetrics(${server.id})" 
                            title="Ver Métricas">
                        <i class="fas fa-chart-line"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" 
                            onclick="serversManager.deleteServer(${server.id})" 
                            title="Remover">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    /**
     * Obtém badge de status
     * @param {string} status - Status do servidor
     * @returns {string} HTML do badge
     */
    getStatusBadge(status) {
        const badges = {
            'online': '<span class="badge bg-success">Online</span>',
            'offline': '<span class="badge bg-danger">Offline</span>',
            'warning': '<span class="badge bg-warning">Alerta</span>',
            'unknown': '<span class="badge bg-secondary">Desconhecido</span>'
        };
        return badges[status.toLowerCase()] || badges.unknown;
    }

    /**
     * Obtém classe CSS para tempo de resposta
     * @param {number} responseTime - Tempo de resposta em ms
     * @returns {string} Classe CSS
     */
    getResponseTimeClass(responseTime) {
        if (!responseTime) return '';
        if (responseTime < 50) return 'text-success';
        if (responseTime < 100) return 'text-warning';
        return 'text-danger';
    }

    /**
     * Obtém classe CSS para offset
     * @param {number} offset - Offset em ms
     * @returns {string} Classe CSS
     */
    getOffsetClass(offset) {
        if (offset === null) return '';
        const absOffset = Math.abs(offset);
        if (absOffset < 10) return 'text-success';
        if (absOffset < 50) return 'text-warning';
        return 'text-danger';
    }

    /**
     * Testa conectividade com um servidor
     * @param {number} serverId - ID do servidor
     */
    async testServer(serverId) {
        const button = document.querySelector(`button[onclick="serversManager.testServer(${serverId})"]`);
        const originalContent = button.innerHTML;
        
        try {
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            button.disabled = true;

            const result = await apiClient.testServer(serverId);
            
            if (result.success) {
                this.showNotification(`Servidor testado com sucesso: ${result.response_time}ms`, 'success');
            } else {
                this.showNotification(`Falha no teste: ${result.error}`, 'warning');
            }

            // Atualiza a linha do servidor
            await this.refreshServer(serverId);

        } catch (error) {
            console.error('Erro ao testar servidor:', error);
            this.showNotification('Erro ao testar servidor', 'error');
        } finally {
            button.innerHTML = originalContent;
            button.disabled = false;
        }
    }

    /**
     * Edita um servidor
     * @param {number} serverId - ID do servidor
     */
    async editServer(serverId) {
        try {
            const server = await apiClient.getServer(serverId);
            this.showEditServerModal(server);
        } catch (error) {
            console.error('Erro ao carregar dados do servidor:', error);
            this.showNotification('Erro ao carregar dados do servidor', 'error');
        }
    }

    /**
     * Exibe modal de edição de servidor
     * @param {Object} server - Dados do servidor
     */
    showEditServerModal(server) {
        const modalHTML = `
            <div class="modal fade" id="editServerModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Editar Servidor</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editServerForm">
                                <input type="hidden" id="editServerId" value="${server.id}">
                                <div class="mb-3">
                                    <label for="editServerName" class="form-label">Nome</label>
                                    <input type="text" class="form-control" id="editServerName" 
                                           value="${this.escapeHtml(server.name)}" required>
                                </div>
                                <div class="mb-3">
                                    <label for="editServerHost" class="form-label">Host/IP</label>
                                    <input type="text" class="form-control" id="editServerHost" 
                                           value="${this.escapeHtml(server.host)}" required>
                                </div>
                                <div class="mb-3">
                                    <label for="editServerPort" class="form-label">Porta</label>
                                    <input type="number" class="form-control" id="editServerPort" 
                                           value="${server.port}">
                                </div>
                                <div class="mb-3">
                                    <label for="editServerDescription" class="form-label">Descrição</label>
                                    <textarea class="form-control" id="editServerDescription" rows="3">${this.escapeHtml(server.description || '')}</textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" onclick="serversManager.saveServerEdit()">Salvar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove modal anterior se existir
        const existingModal = document.getElementById('editServerModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('editServerModal'));
        modal.show();
    }

    /**
     * Salva edição do servidor
     */
    async saveServerEdit() {
        const form = document.getElementById('editServerForm');
        const serverId = document.getElementById('editServerId').value;
        
        const serverData = {
            name: document.getElementById('editServerName').value,
            host: document.getElementById('editServerHost').value,
            port: parseInt(document.getElementById('editServerPort').value) || 123,
            description: document.getElementById('editServerDescription').value
        };

        try {
            await apiClient.updateServer(serverId, serverData);
            bootstrap.Modal.getInstance(document.getElementById('editServerModal')).hide();
            this.showNotification('Servidor atualizado com sucesso', 'success');
            await this.loadServers();
        } catch (error) {
            console.error('Erro ao atualizar servidor:', error);
            this.showNotification('Erro ao atualizar servidor', 'error');
        }
    }

    /**
     * Remove um servidor
     * @param {number} serverId - ID do servidor
     */
    async deleteServer(serverId) {
        const server = this.servers.find(s => s.id === serverId);
        if (!server) return;

        const confirmed = confirm(`Tem certeza que deseja remover o servidor "${server.name}"?`);
        if (!confirmed) return;

        try {
            await apiClient.deleteServer(serverId);
            this.showNotification('Servidor removido com sucesso', 'success');
            await this.loadServers();
        } catch (error) {
            console.error('Erro ao remover servidor:', error);
            this.showNotification('Erro ao remover servidor', 'error');
        }
    }

    /**
     * Visualiza métricas de um servidor
     * @param {number} serverId - ID do servidor
     */
    async viewMetrics(serverId) {
        const server = this.servers.find(s => s.id === serverId);
        if (!server) return;

        try {
            const metrics = await apiClient.getMetrics({ 
                server_id: serverId, 
                limit: 100 
            });
            
            this.showMetricsModal(server, metrics);
        } catch (error) {
            console.error('Erro ao carregar métricas:', error);
            this.showNotification('Erro ao carregar métricas', 'error');
        }
    }

    /**
     * Exibe modal com métricas do servidor
     * @param {Object} server - Dados do servidor
     * @param {Array} metrics - Métricas do servidor
     */
    showMetricsModal(server, metrics) {
        const modalHTML = `
            <div class="modal fade" id="metricsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Métricas - ${this.escapeHtml(server.name)}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-4">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title">Última Verificação</h5>
                                            <p class="card-text">${this.formatDateTime(server.last_check)}</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title">Tempo de Resposta</h5>
                                            <p class="card-text">${server.response_time || 0}ms</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title">Offset</h5>
                                            <p class="card-text">${server.offset || 0}ms</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="chart-container">
                                <canvas id="serverMetricsChart" width="400" height="200"></canvas>
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
        const existingModal = document.getElementById('metricsModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('metricsModal'));
        modal.show();

        // Cria gráfico após o modal ser exibido
        modal._element.addEventListener('shown.bs.modal', () => {
            this.createMetricsChart(metrics);
        });
    }

    /**
     * Cria gráfico de métricas
     * @param {Array} metrics - Dados das métricas
     */
    createMetricsChart(metrics) {
        const ctx = document.getElementById('serverMetricsChart').getContext('2d');
        
        const labels = metrics.map(m => this.formatChartTime(m.timestamp));
        const responseTimeData = metrics.map(m => m.response_time);
        const offsetData = metrics.map(m => Math.abs(m.offset || 0));

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Tempo de Resposta (ms)',
                        data: responseTimeData,
                        borderColor: 'rgb(78, 115, 223)',
                        backgroundColor: 'rgba(78, 115, 223, 0.1)',
                        yAxisID: 'y'
                    },
                    {
                        label: 'Offset Absoluto (ms)',
                        data: offsetData,
                        borderColor: 'rgb(28, 200, 138)',
                        backgroundColor: 'rgba(28, 200, 138, 0.1)',
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Tempo de Resposta (ms)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Offset (ms)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
    }

    /**
     * Atualiza dados de um servidor específico
     * @param {number} serverId - ID do servidor
     */
    async refreshServer(serverId) {
        try {
            const server = await apiClient.getServer(serverId);
            const index = this.servers.findIndex(s => s.id === serverId);
            if (index !== -1) {
                this.servers[index] = server;
                this.renderServersTable();
            }
        } catch (error) {
            console.error('Erro ao atualizar servidor:', error);
        }
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Adicionar outros event listeners conforme necessário
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
     * Atualiza dados dos servidores
     */
    async refresh() {
        try {
            await this.loadServers();
        } catch (error) {
            console.error('Erro ao atualizar servidores:', error);
        }
    }

    /**
     * Exibe erro na tabela de servidores
     * @param {string} message - Mensagem de erro
     */
    showServerError(message) {
        const tbody = document.getElementById('servers-table-body');
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                    <br>${message}
                    <br><button class="btn btn-sm btn-outline-primary mt-2" onclick="serversManager.refresh()">
                        <i class="fas fa-sync-alt me-1"></i>Tentar Novamente
                    </button>
                </td>
            </tr>
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
     * Formata data/hora
     * @param {string} timestamp - Timestamp ISO
     * @returns {string} Data formatada
     */
    formatDateTime(timestamp) {
        if (!timestamp) return 'Nunca';
        return new Date(timestamp).toLocaleString('pt-BR');
    }

    /**
     * Formata tempo relativo
     * @param {string} timestamp - Timestamp ISO
     * @returns {string} Tempo relativo
     */
    formatTimeAgo(timestamp) {
        if (!timestamp) return 'Nunca';
        
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Agora';
        if (diffMins < 60) return `${diffMins}min atrás`;
        if (diffHours < 24) return `${diffHours}h atrás`;
        return `${diffDays}d atrás`;
    }

    /**
     * Formata tempo para gráficos
     * @param {string} timestamp - Timestamp ISO
     * @returns {string} Tempo formatado
     */
    formatChartTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    /**
     * Destrói o gerenciador e limpa recursos
     */
    destroy() {
        this.stopAutoRefresh();
        this.servers = [];
        this.isInitialized = false;
    }
}

// Instância global
const serversManager = new ServersManager();
window.serversManager = serversManager;
window.ServersManager = ServersManager;