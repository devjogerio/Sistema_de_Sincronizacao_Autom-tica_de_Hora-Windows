/**
 * API Client Module
 * Módulo responsável pela comunicação com a API REST
 */

class APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.token = localStorage.getItem('auth_token');
    }

    /**
     * Configura o token de autenticação
     * @param {string} token - Token JWT
     */
    setAuthToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('auth_token', token);
        } else {
            localStorage.removeItem('auth_token');
        }
    }

    /**
     * Obtém os headers padrão para requisições
     * @returns {Object} Headers
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    /**
     * Realiza requisição HTTP genérica
     * @param {string} endpoint - Endpoint da API
     * @param {Object} options - Opções da requisição
     * @returns {Promise} Resposta da API
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options,
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new APIError(
                    errorData.message || `HTTP ${response.status}`,
                    response.status,
                    errorData
                );
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return response;
        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError('Erro de conexão com a API', 0, { originalError: error });
        }
    }

    /**
     * Requisição GET
     * @param {string} endpoint - Endpoint da API
     * @param {Object} params - Parâmetros de query
     * @returns {Promise} Resposta da API
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * Requisição POST
     * @param {string} endpoint - Endpoint da API
     * @param {Object} data - Dados para envio
     * @returns {Promise} Resposta da API
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * Requisição PUT
     * @param {string} endpoint - Endpoint da API
     * @param {Object} data - Dados para envio
     * @returns {Promise} Resposta da API
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    /**
     * Requisição DELETE
     * @param {string} endpoint - Endpoint da API
     * @returns {Promise} Resposta da API
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // === HEALTH ENDPOINTS ===

    /**
     * Verifica o status da API
     * @returns {Promise} Status da API
     */
    async getHealth() {
        return this.get('/health');
    }

    // === SERVER ENDPOINTS ===

    /**
     * Lista todos os servidores
     * @returns {Promise} Lista de servidores
     */
    async getServers() {
        return this.get('/api/servers');
    }

    /**
     * Obtém um servidor específico
     * @param {number} serverId - ID do servidor
     * @returns {Promise} Dados do servidor
     */
    async getServer(serverId) {
        return this.get(`/api/servers/${serverId}`);
    }

    /**
     * Cria um novo servidor
     * @param {Object} serverData - Dados do servidor
     * @returns {Promise} Servidor criado
     */
    async createServer(serverData) {
        return this.post('/api/servers', serverData);
    }

    /**
     * Atualiza um servidor
     * @param {number} serverId - ID do servidor
     * @param {Object} serverData - Dados atualizados
     * @returns {Promise} Servidor atualizado
     */
    async updateServer(serverId, serverData) {
        return this.put(`/api/servers/${serverId}`, serverData);
    }

    /**
     * Remove um servidor
     * @param {number} serverId - ID do servidor
     * @returns {Promise} Confirmação de remoção
     */
    async deleteServer(serverId) {
        return this.delete(`/api/servers/${serverId}`);
    }

    /**
     * Testa conectividade com um servidor
     * @param {number} serverId - ID do servidor
     * @returns {Promise} Resultado do teste
     */
    async testServer(serverId) {
        return this.post(`/api/servers/${serverId}/test`);
    }

    // === METRICS ENDPOINTS ===

    /**
     * Obtém métricas históricas
     * @param {Object} params - Parâmetros de consulta
     * @returns {Promise} Métricas históricas
     */
    async getMetrics(params = {}) {
        return this.get('/api/metrics', params);
    }

    /**
     * Obtém estatísticas agregadas
     * @param {Object} params - Parâmetros de consulta
     * @returns {Promise} Estatísticas
     */
    async getStats(params = {}) {
        return this.get('/api/metrics/stats', params);
    }

    /**
     * Obtém última métrica de um servidor
     * @param {number} serverId - ID do servidor
     * @returns {Promise} Última métrica
     */
    async getLatestMetric(serverId) {
        return this.get(`/api/metrics/latest/${serverId}`);
    }

    /**
     * Obtém tendência de métricas
     * @param {Object} params - Parâmetros de consulta
     * @returns {Promise} Dados de tendência
     */
    async getTrend(params = {}) {
        return this.get('/api/metrics/trend', params);
    }

    /**
     * Consulta avançada de métricas
     * @param {Object} queryData - Dados da consulta
     * @returns {Promise} Resultados da consulta
     */
    async queryMetrics(queryData) {
        return this.post('/api/metrics/query', queryData);
    }

    // === MONITORING ENDPOINTS ===

    /**
     * Obtém status do monitoramento
     * @returns {Promise} Status do monitoramento
     */
    async getMonitoringStatus() {
        return this.get('/api/monitoring/status');
    }

    /**
     * Inicia o monitoramento
     * @returns {Promise} Confirmação de início
     */
    async startMonitoring() {
        return this.post('/api/monitoring/start');
    }

    /**
     * Para o monitoramento
     * @returns {Promise} Confirmação de parada
     */
    async stopMonitoring() {
        return this.post('/api/monitoring/stop');
    }

    /**
     * Atualiza configuração do monitoramento
     * @param {Object} config - Nova configuração
     * @returns {Promise} Configuração atualizada
     */
    async updateMonitoringConfig(config) {
        return this.put('/api/monitoring/config', config);
    }

    /**
     * Executa verificação manual
     * @param {number} serverId - ID do servidor (opcional)
     * @returns {Promise} Resultado da verificação
     */
    async manualCheck(serverId = null) {
        const endpoint = serverId 
            ? `/api/monitoring/check/${serverId}` 
            : '/api/monitoring/check';
        return this.post(endpoint);
    }

    /**
     * Lista alertas ativos
     * @returns {Promise} Lista de alertas
     */
    async getAlerts() {
        return this.get('/api/monitoring/alerts');
    }

    /**
     * Reconhece um alerta
     * @param {number} alertId - ID do alerta
     * @returns {Promise} Confirmação
     */
    async acknowledgeAlert(alertId) {
        return this.post(`/api/monitoring/alerts/${alertId}/acknowledge`);
    }

    /**
     * Resolve um alerta
     * @param {number} alertId - ID do alerta
     * @returns {Promise} Confirmação
     */
    async resolveAlert(alertId) {
        return this.post(`/api/monitoring/alerts/${alertId}/resolve`);
    }

    // === REPORTS ENDPOINTS ===

    /**
     * Lista relatórios disponíveis
     * @returns {Promise} Lista de relatórios
     */
    async getReports() {
        return this.get('/api/reports');
    }

    /**
     * Obtém um relatório específico
     * @param {number} reportId - ID do relatório
     * @returns {Promise} Dados do relatório
     */
    async getReport(reportId) {
        return this.get(`/api/reports/${reportId}`);
    }

    /**
     * Gera um novo relatório
     * @param {Object} reportData - Dados do relatório
     * @returns {Promise} Relatório gerado
     */
    async generateReport(reportData) {
        return this.post('/api/reports/generate', reportData);
    }

    /**
     * Baixa um relatório em PDF
     * @param {number} reportId - ID do relatório
     * @returns {Promise} Blob do PDF
     */
    async downloadReport(reportId) {
        const response = await this.request(`/api/reports/${reportId}/download`, {
            method: 'GET',
        });
        return response.blob();
    }

    /**
     * Remove um relatório
     * @param {number} reportId - ID do relatório
     * @returns {Promise} Confirmação de remoção
     */
    async deleteReport(reportId) {
        return this.delete(`/api/reports/${reportId}`);
    }

    // === POOL ENDPOINTS ===

    /**
     * Lista pools de servidores
     * @returns {Promise} Lista de pools
     */
    async getPools() {
        return this.get('/api/pools');
    }

    /**
     * Obtém um pool específico
     * @param {number} poolId - ID do pool
     * @returns {Promise} Dados do pool
     */
    async getPool(poolId) {
        return this.get(`/api/pools/${poolId}`);
    }

    /**
     * Cria um novo pool
     * @param {Object} poolData - Dados do pool
     * @returns {Promise} Pool criado
     */
    async createPool(poolData) {
        return this.post('/api/pools', poolData);
    }

    /**
     * Atualiza um pool
     * @param {number} poolId - ID do pool
     * @param {Object} poolData - Dados atualizados
     * @returns {Promise} Pool atualizado
     */
    async updatePool(poolId, poolData) {
        return this.put(`/api/pools/${poolId}`, poolData);
    }

    /**
     * Remove um pool
     * @param {number} poolId - ID do pool
     * @returns {Promise} Confirmação de remoção
     */
    async deletePool(poolId) {
        return this.delete(`/api/pools/${poolId}`);
    }

    /**
     * Obtém estatísticas de um pool
     * @param {number} poolId - ID do pool
     * @returns {Promise} Estatísticas do pool
     */
    async getPoolStats(poolId) {
        return this.get(`/api/pools/${poolId}/stats`);
    }
}

/**
 * Classe para erros da API
 */
class APIError extends Error {
    constructor(message, status = 0, data = {}) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

// Instância global do cliente da API
const apiClient = new APIClient();

// Exporta para uso em outros módulos
window.APIClient = APIClient;
window.APIError = APIError;
window.apiClient = apiClient;