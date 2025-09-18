/**
 * Dashboard Module
 * Módulo responsável pelas funcionalidades do dashboard principal
 */

class Dashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = null;
        this.refreshRate = 30000; // 30 segundos
        this.isInitialized = false;
    }

    /**
     * Inicializa o dashboard
     */
    async init() {
        if (this.isInitialized) return;

        try {
            await this.loadInitialData();
            this.initializeCharts();
            this.startAutoRefresh();
            this.isInitialized = true;
            console.log('Dashboard inicializado com sucesso');
        } catch (error) {
            console.error('Erro ao inicializar dashboard:', error);
            this.showError('Erro ao carregar dados do dashboard');
        }
    }

    /**
     * Carrega dados iniciais do dashboard
     */
    async loadInitialData() {
        const promises = [
            this.updateStatusCards(),
            this.updateRecentActivity(),
            this.updateRecentAlerts(),
            this.loadChartData()
        ];

        await Promise.allSettled(promises);
    }

    /**
     * Atualiza os cards de status
     */
    async updateStatusCards() {
        try {
            const [servers, stats, alerts] = await Promise.all([
                apiClient.getServers(),
                apiClient.getStats({ period: '24h' }),
                apiClient.getAlerts()
            ]);

            // Servidores ativos
            const activeServers = servers.filter(s => s.status === 'online').length;
            document.getElementById('active-servers-count').textContent = activeServers;

            // Taxa de sucesso
            const successRate = stats.success_rate ? `${stats.success_rate.toFixed(1)}%` : '0%';
            document.getElementById('success-rate').textContent = successRate;

            // Tempo médio de resposta
            const avgResponseTime = stats.avg_response_time 
                ? `${stats.avg_response_time.toFixed(0)}ms` 
                : '0ms';
            document.getElementById('avg-response-time').textContent = avgResponseTime;

            // Alertas ativos
            const activeAlerts = alerts.filter(a => a.status === 'active').length;
            document.getElementById('active-alerts-count').textContent = activeAlerts;

        } catch (error) {
            console.error('Erro ao atualizar cards de status:', error);
            this.setLoadingState(['active-servers-count', 'success-rate', 'avg-response-time', 'active-alerts-count'], 'Erro');
        }
    }

    /**
     * Atualiza a lista de atividade recente
     */
    async updateRecentActivity() {
        try {
            const metrics = await apiClient.getMetrics({ 
                limit: 10, 
                order: 'desc' 
            });

            const container = document.getElementById('recent-activity');
            
            if (!metrics || metrics.length === 0) {
                container.innerHTML = '<div class="text-center text-muted">Nenhuma atividade recente</div>';
                return;
            }

            const html = metrics.map(metric => this.createActivityItem(metric)).join('');
            container.innerHTML = html;

        } catch (error) {
            console.error('Erro ao carregar atividade recente:', error);
            document.getElementById('recent-activity').innerHTML = 
                '<div class="text-center text-danger">Erro ao carregar atividades</div>';
        }
    }

    /**
     * Cria item de atividade
     * @param {Object} metric - Dados da métrica
     * @returns {string} HTML do item
     */
    createActivityItem(metric) {
        const iconClass = this.getActivityIcon(metric.status);
        const iconColor = this.getActivityColor(metric.status);
        const timeAgo = this.formatTimeAgo(metric.timestamp);

        return `
            <div class="activity-item fade-in">
                <div class="activity-icon bg-${iconColor}">
                    <i class="fas ${iconClass} text-white"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${metric.server_name}</div>
                    <div class="activity-description">
                        Resposta: ${metric.response_time}ms | Offset: ${metric.offset}ms
                    </div>
                </div>
                <div class="activity-time">${timeAgo}</div>
            </div>
        `;
    }

    /**
     * Atualiza a lista de alertas recentes
     */
    async updateRecentAlerts() {
        try {
            const alerts = await apiClient.getAlerts();
            const recentAlerts = alerts.slice(0, 5);

            const container = document.getElementById('recent-alerts');
            
            if (!recentAlerts || recentAlerts.length === 0) {
                container.innerHTML = '<div class="text-center text-muted">Nenhum alerta recente</div>';
                return;
            }

            const html = recentAlerts.map(alert => this.createAlertItem(alert)).join('');
            container.innerHTML = html;

        } catch (error) {
            console.error('Erro ao carregar alertas recentes:', error);
            document.getElementById('recent-alerts').innerHTML = 
                '<div class="text-center text-danger">Erro ao carregar alertas</div>';
        }
    }

    /**
     * Cria item de alerta
     * @param {Object} alert - Dados do alerta
     * @returns {string} HTML do item
     */
    createAlertItem(alert) {
        const severityClass = alert.severity.toLowerCase();
        const timeAgo = this.formatTimeAgo(alert.created_at);

        return `
            <div class="alert-item alert-${severityClass} fade-in">
                <div class="alert-header">
                    <h6 class="alert-title">${alert.title}</h6>
                    <span class="alert-severity ${severityClass}">${alert.severity}</span>
                </div>
                <div class="alert-description">${alert.description}</div>
                <div class="alert-meta">
                    <span>Servidor: ${alert.server_name}</span>
                    <span>${timeAgo}</span>
                </div>
            </div>
        `;
    }

    /**
     * Inicializa os gráficos
     */
    initializeCharts() {
        this.initResponseTimeChart();
        this.initServerStatusChart();
    }

    /**
     * Inicializa gráfico de tempo de resposta
     */
    initResponseTimeChart() {
        const ctx = document.getElementById('responseTimeChart').getContext('2d');
        
        this.charts.responseTime = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Tempo de Resposta (ms)',
                    data: [],
                    borderColor: 'rgb(78, 115, 223)',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Tempo'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Tempo de Resposta (ms)'
                        },
                        beginAtZero: true
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    /**
     * Inicializa gráfico de status dos servidores
     */
    initServerStatusChart() {
        const ctx = document.getElementById('serverStatusChart').getContext('2d');
        
        this.charts.serverStatus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Online', 'Offline', 'Warning'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        'rgb(28, 200, 138)',
                        'rgb(231, 74, 59)',
                        'rgb(246, 194, 62)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    /**
     * Carrega dados dos gráficos
     */
    async loadChartData() {
        try {
            await Promise.all([
                this.updateResponseTimeChart(),
                this.updateServerStatusChart()
            ]);
        } catch (error) {
            console.error('Erro ao carregar dados dos gráficos:', error);
        }
    }

    /**
     * Atualiza gráfico de tempo de resposta
     */
    async updateResponseTimeChart() {
        try {
            const metrics = await apiClient.getMetrics({ 
                period: '24h',
                interval: '1h'
            });

            if (!metrics || metrics.length === 0) return;

            const labels = metrics.map(m => this.formatChartTime(m.timestamp));
            const data = metrics.map(m => m.response_time);

            this.charts.responseTime.data.labels = labels;
            this.charts.responseTime.data.datasets[0].data = data;
            this.charts.responseTime.update('none');

        } catch (error) {
            console.error('Erro ao atualizar gráfico de tempo de resposta:', error);
        }
    }

    /**
     * Atualiza gráfico de status dos servidores
     */
    async updateServerStatusChart() {
        try {
            const servers = await apiClient.getServers();
            
            if (!servers || servers.length === 0) return;

            const statusCounts = servers.reduce((acc, server) => {
                acc[server.status] = (acc[server.status] || 0) + 1;
                return acc;
            }, {});

            const data = [
                statusCounts.online || 0,
                statusCounts.offline || 0,
                statusCounts.warning || 0
            ];

            this.charts.serverStatus.data.datasets[0].data = data;
            this.charts.serverStatus.update('none');

        } catch (error) {
            console.error('Erro ao atualizar gráfico de status:', error);
        }
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
     * Atualiza dados do dashboard
     */
    async refresh() {
        try {
            await this.loadInitialData();
        } catch (error) {
            console.error('Erro ao atualizar dashboard:', error);
        }
    }

    /**
     * Define estado de carregamento para elementos
     * @param {Array} elementIds - IDs dos elementos
     * @param {string} text - Texto a exibir
     */
    setLoadingState(elementIds, text = 'Carregando...') {
        elementIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = text.includes('Erro') 
                    ? `<i class="fas fa-exclamation-triangle text-danger"></i> ${text}`
                    : `<i class="fas fa-spinner fa-spin"></i> ${text}`;
            }
        });
    }

    /**
     * Exibe mensagem de erro
     * @param {string} message - Mensagem de erro
     */
    showError(message) {
        // Implementar sistema de notificações
        console.error(message);
    }

    /**
     * Obtém ícone para atividade baseado no status
     * @param {string} status - Status da atividade
     * @returns {string} Classe do ícone
     */
    getActivityIcon(status) {
        const icons = {
            'online': 'fa-check-circle',
            'offline': 'fa-times-circle',
            'warning': 'fa-exclamation-triangle',
            'default': 'fa-clock'
        };
        return icons[status] || icons.default;
    }

    /**
     * Obtém cor para atividade baseado no status
     * @param {string} status - Status da atividade
     * @returns {string} Classe de cor
     */
    getActivityColor(status) {
        const colors = {
            'online': 'success',
            'offline': 'danger',
            'warning': 'warning',
            'default': 'info'
        };
        return colors[status] || colors.default;
    }

    /**
     * Formata timestamp para exibição relativa
     * @param {string} timestamp - Timestamp ISO
     * @returns {string} Tempo formatado
     */
    formatTimeAgo(timestamp) {
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
     * Formata timestamp para gráficos
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
     * Destrói o dashboard e limpa recursos
     */
    destroy() {
        this.stopAutoRefresh();
        
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        
        this.charts = {};
        this.isInitialized = false;
    }
}

// Funções globais para interação com gráficos
window.refreshChart = function(chartName) {
    if (window.dashboard && window.dashboard.charts[chartName]) {
        const methodName = `update${chartName.charAt(0).toUpperCase() + chartName.slice(1)}`;
        if (typeof window.dashboard[methodName] === 'function') {
            window.dashboard[methodName]();
        }
    }
};

window.exportChart = function(chartName) {
    if (window.dashboard && window.dashboard.charts[chartName]) {
        const chart = window.dashboard.charts[chartName];
        const url = chart.toBase64Image();
        const link = document.createElement('a');
        link.download = `${chartName}.png`;
        link.href = url;
        link.click();
    }
};

// Exporta para uso global
window.Dashboard = Dashboard;