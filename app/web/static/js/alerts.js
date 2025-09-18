/**
 * Alerts Manager Module
 * Módulo responsável pelo gerenciamento de alertas do sistema
 */

class AlertsManager {
    constructor() {
        this.alerts = [];
        this.alertConfigs = [];
        this.isInitialized = false;
        this.refreshInterval = null;
        this.refreshRate = 15000; // 15 segundos
        this.soundEnabled = true;
        this.notificationPermission = 'default';
    }

    /**
     * Inicializa o gerenciador de alertas
     */
    async init() {
        if (this.isInitialized) return;

        try {
            await this.requestNotificationPermission();
            await this.loadAlerts();
            await this.loadAlertConfigs();
            this.setupEventListeners();
            this.startAutoRefresh();
            this.isInitialized = true;
            console.log('Gerenciador de alertas inicializado');
        } catch (error) {
            console.error('Erro ao inicializar gerenciador de alertas:', error);
            this.showError('Erro ao carregar alertas');
        }
    }

    /**
     * Solicita permissão para notificações
     */
    async requestNotificationPermission() {
        if ('Notification' in window) {
            this.notificationPermission = await Notification.requestPermission();
        }
    }

    /**
     * Carrega lista de alertas
     */
    async loadAlerts() {
        try {
            this.alerts = await apiClient.getAlerts();
            this.renderAlertsTable();
            this.updateAlertsSummary();
        } catch (error) {
            console.error('Erro ao carregar alertas:', error);
            this.showAlertsError('Erro ao carregar lista de alertas');
        }
    }

    /**
     * Carrega configurações de alertas
     */
    async loadAlertConfigs() {
        try {
            this.alertConfigs = await apiClient.getAlertConfigs();
        } catch (error) {
            console.error('Erro ao carregar configurações de alertas:', error);
        }
    }

    /**
     * Renderiza tabela de alertas
     */
    renderAlertsTable() {
        const tbody = document.getElementById('alerts-table-body');
        
        if (!this.alerts || this.alerts.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="fas fa-bell fa-2x mb-2"></i>
                        <br>Nenhum alerta ativo
                        <br><small>Sistema funcionando normalmente</small>
                    </td>
                </tr>
            `;
            return;
        }

        const html = this.alerts.map(alert => this.createAlertRow(alert)).join('');
        tbody.innerHTML = html;
    }

    /**
     * Cria linha da tabela para um alerta
     * @param {Object} alert - Dados do alerta
     * @returns {string} HTML da linha
     */
    createAlertRow(alert) {
        const severityBadge = this.getSeverityBadge(alert.severity);
        const statusBadge = this.getStatusBadge(alert.status);
        const createdAt = this.formatDateTime(alert.created_at);
        const acknowledgedBy = alert.acknowledged_by ? `por ${alert.acknowledged_by}` : '';

        return `
            <tr data-alert-id="${alert.id}" class="fade-in alert-row-${alert.severity}">
                <td>
                    ${severityBadge}
                    <div class="mt-1">
                        <strong>${this.escapeHtml(alert.title)}</strong>
                        <br><small class="text-muted">${this.escapeHtml(alert.message)}</small>
                    </div>
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="status-indicator status-${alert.server_status || 'unknown'}"></div>
                        <span>${this.escapeHtml(alert.server_name || 'Sistema')}</span>
                    </div>
                </td>
                <td>${statusBadge}</td>
                <td>
                    <span title="${createdAt}">${this.formatTimeAgo(alert.created_at)}</span>
                </td>
                <td>
                    ${alert.acknowledged_at ? 
                        `<small class="text-success">
                            <i class="fas fa-check"></i> ${this.formatTimeAgo(alert.acknowledged_at)}
                            <br>${acknowledgedBy}
                        </small>` : 
                        '<span class="text-muted">-</span>'
                    }
                </td>
                <td class="alert-actions">
                    ${!alert.acknowledged_at ? 
                        `<button class="btn btn-sm btn-outline-success me-1" 
                                onclick="alertsManager.acknowledgeAlert(${alert.id})" 
                                title="Reconhecer">
                            <i class="fas fa-check"></i>
                        </button>` : ''
                    }
                    <button class="btn btn-sm btn-outline-info me-1" 
                            onclick="alertsManager.viewAlertDetails(${alert.id})" 
                            title="Detalhes">
                        <i class="fas fa-info-circle"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" 
                            onclick="alertsManager.dismissAlert(${alert.id})" 
                            title="Descartar">
                        <i class="fas fa-times"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    /**
     * Obtém badge de severidade
     * @param {string} severity - Severidade do alerta
     * @returns {string} HTML do badge
     */
    getSeverityBadge(severity) {
        const badges = {
            'critical': '<span class="badge bg-danger"><i class="fas fa-exclamation-triangle"></i> Crítico</span>',
            'high': '<span class="badge bg-warning"><i class="fas fa-exclamation"></i> Alto</span>',
            'medium': '<span class="badge bg-info"><i class="fas fa-info"></i> Médio</span>',
            'low': '<span class="badge bg-secondary"><i class="fas fa-minus"></i> Baixo</span>'
        };
        return badges[severity] || badges.low;
    }

    /**
     * Obtém badge de status
     * @param {string} status - Status do alerta
     * @returns {string} HTML do badge
     */
    getStatusBadge(status) {
        const badges = {
            'active': '<span class="badge bg-danger">Ativo</span>',
            'acknowledged': '<span class="badge bg-warning">Reconhecido</span>',
            'resolved': '<span class="badge bg-success">Resolvido</span>',
            'dismissed': '<span class="badge bg-secondary">Descartado</span>'
        };
        return badges[status] || badges.active;
    }

    /**
     * Atualiza resumo de alertas
     */
    updateAlertsSummary() {
        const summary = this.calculateAlertsSummary();
        
        // Atualiza cards de resumo
        this.updateSummaryCard('critical-alerts-count', summary.critical);
        this.updateSummaryCard('high-alerts-count', summary.high);
        this.updateSummaryCard('total-alerts-count', summary.total);
        this.updateSummaryCard('acknowledged-alerts-count', summary.acknowledged);

        // Atualiza indicador na navegação
        this.updateNavigationBadge(summary.active);
    }

    /**
     * Calcula resumo de alertas
     * @returns {Object} Resumo dos alertas
     */
    calculateAlertsSummary() {
        const summary = {
            total: this.alerts.length,
            active: 0,
            acknowledged: 0,
            critical: 0,
            high: 0,
            medium: 0,
            low: 0
        };

        this.alerts.forEach(alert => {
            if (alert.status === 'active') summary.active++;
            if (alert.status === 'acknowledged') summary.acknowledged++;
            
            switch (alert.severity) {
                case 'critical': summary.critical++; break;
                case 'high': summary.high++; break;
                case 'medium': summary.medium++; break;
                case 'low': summary.low++; break;
            }
        });

        return summary;
    }

    /**
     * Atualiza card de resumo
     * @param {string} elementId - ID do elemento
     * @param {number} value - Valor a exibir
     */
    updateSummaryCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * Atualiza badge na navegação
     * @param {number} activeCount - Número de alertas ativos
     */
    updateNavigationBadge(activeCount) {
        const badge = document.querySelector('.nav-link[href="#alerts"] .badge');
        if (badge) {
            if (activeCount > 0) {
                badge.textContent = activeCount;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    /**
     * Reconhece um alerta
     * @param {number} alertId - ID do alerta
     */
    async acknowledgeAlert(alertId) {
        try {
            await apiClient.acknowledgeAlert(alertId);
            this.showNotification('Alerta reconhecido', 'success');
            await this.loadAlerts();
        } catch (error) {
            console.error('Erro ao reconhecer alerta:', error);
            this.showNotification('Erro ao reconhecer alerta', 'error');
        }
    }

    /**
     * Descarta um alerta
     * @param {number} alertId - ID do alerta
     */
    async dismissAlert(alertId) {
        const alert = this.alerts.find(a => a.id === alertId);
        if (!alert) return;

        const confirmed = confirm(`Tem certeza que deseja descartar este alerta?`);
        if (!confirmed) return;

        try {
            await apiClient.dismissAlert(alertId);
            this.showNotification('Alerta descartado', 'success');
            await this.loadAlerts();
        } catch (error) {
            console.error('Erro ao descartar alerta:', error);
            this.showNotification('Erro ao descartar alerta', 'error');
        }
    }

    /**
     * Visualiza detalhes de um alerta
     * @param {number} alertId - ID do alerta
     */
    async viewAlertDetails(alertId) {
        const alert = this.alerts.find(a => a.id === alertId);
        if (!alert) return;

        try {
            const details = await apiClient.getAlertDetails(alertId);
            this.showAlertDetailsModal(alert, details);
        } catch (error) {
            console.error('Erro ao carregar detalhes do alerta:', error);
            this.showNotification('Erro ao carregar detalhes', 'error');
        }
    }

    /**
     * Exibe modal com detalhes do alerta
     * @param {Object} alert - Dados do alerta
     * @param {Object} details - Detalhes adicionais
     */
    showAlertDetailsModal(alert, details) {
        const modalHTML = `
            <div class="modal fade" id="alertDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                ${this.getSeverityBadge(alert.severity)}
                                Detalhes do Alerta
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>Título:</strong><br>
                                    ${this.escapeHtml(alert.title)}
                                </div>
                                <div class="col-md-6">
                                    <strong>Status:</strong><br>
                                    ${this.getStatusBadge(alert.status)}
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>Servidor:</strong><br>
                                    ${this.escapeHtml(alert.server_name || 'Sistema')}
                                </div>
                                <div class="col-md-6">
                                    <strong>Criado em:</strong><br>
                                    ${this.formatDateTime(alert.created_at)}
                                </div>
                            </div>

                            <div class="mb-3">
                                <strong>Mensagem:</strong><br>
                                <div class="alert alert-light">
                                    ${this.escapeHtml(alert.message)}
                                </div>
                            </div>

                            ${details.context ? `
                                <div class="mb-3">
                                    <strong>Contexto:</strong><br>
                                    <pre class="bg-light p-2 rounded"><code>${JSON.stringify(details.context, null, 2)}</code></pre>
                                </div>
                            ` : ''}

                            ${alert.acknowledged_at ? `
                                <div class="mb-3">
                                    <strong>Reconhecimento:</strong><br>
                                    <div class="alert alert-success">
                                        <i class="fas fa-check me-2"></i>
                                        Reconhecido em ${this.formatDateTime(alert.acknowledged_at)}
                                        ${alert.acknowledged_by ? ` por ${alert.acknowledged_by}` : ''}
                                    </div>
                                </div>
                            ` : ''}

                            ${details.related_metrics ? `
                                <div class="mb-3">
                                    <strong>Métricas Relacionadas:</strong><br>
                                    <canvas id="alertMetricsChart" width="400" height="200"></canvas>
                                </div>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            ${!alert.acknowledged_at ? 
                                `<button type="button" class="btn btn-success" onclick="alertsManager.acknowledgeAlert(${alert.id}); bootstrap.Modal.getInstance(document.getElementById('alertDetailsModal')).hide();">
                                    <i class="fas fa-check me-1"></i>Reconhecer
                                </button>` : ''
                            }
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove modal anterior se existir
        const existingModal = document.getElementById('alertDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('alertDetailsModal'));
        modal.show();

        // Cria gráfico se houver métricas relacionadas
        if (details.related_metrics) {
            modal._element.addEventListener('shown.bs.modal', () => {
                this.createAlertMetricsChart(details.related_metrics);
            });
        }
    }

    /**
     * Cria gráfico de métricas relacionadas ao alerta
     * @param {Array} metrics - Métricas relacionadas
     */
    createAlertMetricsChart(metrics) {
        const ctx = document.getElementById('alertMetricsChart').getContext('2d');
        
        const labels = metrics.map(m => this.formatChartTime(m.timestamp));
        const values = metrics.map(m => m.value);

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Valor da Métrica',
                    data: values,
                    borderColor: 'rgb(220, 53, 69)',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * Exibe configurações de alertas
     */
    showAlertConfigModal() {
        const modalHTML = `
            <div class="modal fade" id="alertConfigModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Configurações de Alertas</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="alertConfigForm">
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <div class="form-check form-switch">
                                            <input class="form-check-input" type="checkbox" id="enableAlerts" checked>
                                            <label class="form-check-label" for="enableAlerts">
                                                Alertas Habilitados
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="form-check form-switch">
                                            <input class="form-check-input" type="checkbox" id="enableSound" ${this.soundEnabled ? 'checked' : ''}>
                                            <label class="form-check-label" for="enableSound">
                                                Som de Alerta
                                            </label>
                                        </div>
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <label for="emailNotifications" class="form-label">Email para Notificações</label>
                                    <input type="email" class="form-control" id="emailNotifications" 
                                           placeholder="admin@exemplo.com">
                                </div>

                                <h6>Thresholds de Alerta</h6>
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="responseTimeThreshold" class="form-label">Tempo de Resposta (ms)</label>
                                        <input type="number" class="form-control" id="responseTimeThreshold" value="1000">
                                    </div>
                                    <div class="col-md-6">
                                        <label for="offsetThreshold" class="form-label">Offset Máximo (ms)</label>
                                        <input type="number" class="form-control" id="offsetThreshold" value="100">
                                    </div>
                                </div>

                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="uptimeThreshold" class="form-label">Uptime Mínimo (%)</label>
                                        <input type="number" class="form-control" id="uptimeThreshold" value="95" min="0" max="100">
                                    </div>
                                    <div class="col-md-6">
                                        <label for="checkInterval" class="form-label">Intervalo de Verificação (min)</label>
                                        <input type="number" class="form-control" id="checkInterval" value="5" min="1">
                                    </div>
                                </div>

                                <h6>Detecção de Anomalias</h6>
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <div class="form-check form-switch">
                                            <input class="form-check-input" type="checkbox" id="enableAnomalyDetection" checked>
                                            <label class="form-check-label" for="enableAnomalyDetection">
                                                Detecção de Anomalias
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="anomalySensitivity" class="form-label">Sensibilidade</label>
                                        <select class="form-select" id="anomalySensitivity">
                                            <option value="low">Baixa</option>
                                            <option value="medium" selected>Média</option>
                                            <option value="high">Alta</option>
                                        </select>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" onclick="alertsManager.saveAlertConfig()">Salvar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove modal anterior se existir
        const existingModal = document.getElementById('alertConfigModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('alertConfigModal'));
        modal.show();
    }

    /**
     * Salva configurações de alertas
     */
    async saveAlertConfig() {
        const configData = {
            enabled: document.getElementById('enableAlerts').checked,
            sound_enabled: document.getElementById('enableSound').checked,
            email_notifications: document.getElementById('emailNotifications').value,
            response_time_threshold: parseInt(document.getElementById('responseTimeThreshold').value),
            offset_threshold: parseInt(document.getElementById('offsetThreshold').value),
            uptime_threshold: parseInt(document.getElementById('uptimeThreshold').value),
            check_interval: parseInt(document.getElementById('checkInterval').value),
            anomaly_detection_enabled: document.getElementById('enableAnomalyDetection').checked,
            anomaly_sensitivity: document.getElementById('anomalySensitivity').value
        };

        try {
            await apiClient.updateAlertConfig(configData);
            this.soundEnabled = configData.sound_enabled;
            bootstrap.Modal.getInstance(document.getElementById('alertConfigModal')).hide();
            this.showNotification('Configurações salvas com sucesso', 'success');
        } catch (error) {
            console.error('Erro ao salvar configurações:', error);
            this.showNotification('Erro ao salvar configurações', 'error');
        }
    }

    /**
     * Processa novos alertas recebidos
     * @param {Array} newAlerts - Novos alertas
     */
    processNewAlerts(newAlerts) {
        newAlerts.forEach(alert => {
            if (alert.severity === 'critical' || alert.severity === 'high') {
                this.showBrowserNotification(alert);
                if (this.soundEnabled) {
                    this.playAlertSound();
                }
            }
        });
    }

    /**
     * Exibe notificação do navegador
     * @param {Object} alert - Dados do alerta
     */
    showBrowserNotification(alert) {
        if (this.notificationPermission === 'granted') {
            new Notification(`Alerta ${alert.severity.toUpperCase()}`, {
                body: alert.message,
                icon: '/static/img/alert-icon.png',
                tag: `alert-${alert.id}`
            });
        }
    }

    /**
     * Reproduz som de alerta
     */
    playAlertSound() {
        try {
            const audio = new Audio('/static/sounds/alert.mp3');
            audio.volume = 0.5;
            audio.play().catch(e => console.log('Não foi possível reproduzir som de alerta'));
        } catch (error) {
            console.log('Som de alerta não disponível');
        }
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Event listeners específicos dos alertas
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
     * Atualiza dados dos alertas
     */
    async refresh() {
        try {
            const previousAlertsCount = this.alerts.length;
            await this.loadAlerts();
            
            // Verifica se há novos alertas
            if (this.alerts.length > previousAlertsCount) {
                const newAlerts = this.alerts.slice(0, this.alerts.length - previousAlertsCount);
                this.processNewAlerts(newAlerts);
            }
        } catch (error) {
            console.error('Erro ao atualizar alertas:', error);
        }
    }

    /**
     * Exibe erro na tabela de alertas
     * @param {string} message - Mensagem de erro
     */
    showAlertsError(message) {
        const tbody = document.getElementById('alerts-table-body');
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                    <br>${message}
                    <br><button class="btn btn-sm btn-outline-primary mt-2" onclick="alertsManager.refresh()">
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
        this.alerts = [];
        this.alertConfigs = [];
        this.isInitialized = false;
    }
}

// Instância global
const alertsManager = new AlertsManager();
window.alertsManager = alertsManager;
window.AlertsManager = AlertsManager;