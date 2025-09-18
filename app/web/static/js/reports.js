/**
 * Reports Manager Module
 * Módulo responsável pelo gerenciamento de relatórios do sistema
 */

class ReportsManager {
    constructor() {
        this.reports = [];
        this.isInitialized = false;
        this.refreshInterval = null;
        this.refreshRate = 60000; // 1 minuto
    }

    /**
     * Inicializa o gerenciador de relatórios
     */
    async init() {
        if (this.isInitialized) return;

        try {
            await this.loadReports();
            this.setupEventListeners();
            this.startAutoRefresh();
            this.isInitialized = true;
            console.log('Gerenciador de relatórios inicializado');
        } catch (error) {
            console.error('Erro ao inicializar gerenciador de relatórios:', error);
            this.showError('Erro ao carregar relatórios');
        }
    }

    /**
     * Carrega lista de relatórios
     */
    async loadReports() {
        try {
            this.reports = await apiClient.getReports();
            this.renderReportsTable();
        } catch (error) {
            console.error('Erro ao carregar relatórios:', error);
            this.showReportsError('Erro ao carregar lista de relatórios');
        }
    }

    /**
     * Renderiza tabela de relatórios
     */
    renderReportsTable() {
        const tbody = document.getElementById('reports-table-body');
        
        if (!this.reports || this.reports.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="fas fa-file-pdf fa-2x mb-2"></i>
                        <br>Nenhum relatório gerado
                        <br><small>Clique em "Gerar Relatório" para criar um novo</small>
                    </td>
                </tr>
            `;
            return;
        }

        const html = this.reports.map(report => this.createReportRow(report)).join('');
        tbody.innerHTML = html;
    }

    /**
     * Cria linha da tabela para um relatório
     * @param {Object} report - Dados do relatório
     * @returns {string} HTML da linha
     */
    createReportRow(report) {
        const statusBadge = this.getStatusBadge(report.status);
        const typeBadge = this.getTypeBadge(report.type);
        const createdAt = this.formatDateTime(report.created_at);
        const fileSize = this.formatFileSize(report.file_size);

        return `
            <tr data-report-id="${report.id}" class="fade-in">
                <td>
                    <div class="d-flex align-items-center">
                        <i class="fas fa-file-pdf text-danger me-2"></i>
                        <div>
                            <strong>${this.escapeHtml(report.title)}</strong>
                            <br><small class="text-muted">${this.escapeHtml(report.description || '')}</small>
                        </div>
                    </div>
                </td>
                <td>${typeBadge}</td>
                <td>${statusBadge}</td>
                <td>
                    <span title="${createdAt}">${this.formatTimeAgo(report.created_at)}</span>
                </td>
                <td>
                    <span class="text-muted">${fileSize}</span>
                </td>
                <td class="report-actions">
                    ${report.status === 'completed' ? 
                        `<button class="btn btn-sm btn-outline-primary me-1" 
                                onclick="reportsManager.downloadReport(${report.id})" 
                                title="Download">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info me-1" 
                                onclick="reportsManager.previewReport(${report.id})" 
                                title="Visualizar">
                            <i class="fas fa-eye"></i>
                        </button>` : ''
                    }
                    ${report.status === 'failed' ? 
                        `<button class="btn btn-sm btn-outline-warning me-1" 
                                onclick="reportsManager.retryReport(${report.id})" 
                                title="Tentar Novamente">
                            <i class="fas fa-redo"></i>
                        </button>` : ''
                    }
                    <button class="btn btn-sm btn-outline-secondary me-1" 
                            onclick="reportsManager.viewReportDetails(${report.id})" 
                            title="Detalhes">
                        <i class="fas fa-info-circle"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" 
                            onclick="reportsManager.deleteReport(${report.id})" 
                            title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    /**
     * Obtém badge de status
     * @param {string} status - Status do relatório
     * @returns {string} HTML do badge
     */
    getStatusBadge(status) {
        const badges = {
            'pending': '<span class="badge bg-secondary"><i class="fas fa-clock"></i> Pendente</span>',
            'generating': '<span class="badge bg-info"><i class="fas fa-spinner fa-spin"></i> Gerando</span>',
            'completed': '<span class="badge bg-success"><i class="fas fa-check"></i> Concluído</span>',
            'failed': '<span class="badge bg-danger"><i class="fas fa-times"></i> Falhou</span>'
        };
        return badges[status] || badges.pending;
    }

    /**
     * Obtém badge de tipo
     * @param {string} type - Tipo do relatório
     * @returns {string} HTML do badge
     */
    getTypeBadge(type) {
        const badges = {
            'daily': '<span class="badge bg-primary">Diário</span>',
            'weekly': '<span class="badge bg-info">Semanal</span>',
            'monthly': '<span class="badge bg-warning">Mensal</span>',
            'custom': '<span class="badge bg-secondary">Personalizado</span>',
            'performance': '<span class="badge bg-success">Performance</span>',
            'availability': '<span class="badge bg-danger">Disponibilidade</span>'
        };
        return badges[type] || badges.custom;
    }

    /**
     * Exibe modal de geração de relatório
     */
    showGenerateReportModal() {
        const modalHTML = `
            <div class="modal fade" id="generateReportModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Gerar Novo Relatório</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="generateReportForm">
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="reportTitle" class="form-label">Título do Relatório</label>
                                        <input type="text" class="form-control" id="reportTitle" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="reportType" class="form-label">Tipo de Relatório</label>
                                        <select class="form-select" id="reportType" required>
                                            <option value="">Selecione o tipo</option>
                                            <option value="daily">Relatório Diário</option>
                                            <option value="weekly">Relatório Semanal</option>
                                            <option value="monthly">Relatório Mensal</option>
                                            <option value="performance">Análise de Performance</option>
                                            <option value="availability">Relatório de Disponibilidade</option>
                                            <option value="custom">Personalizado</option>
                                        </select>
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <label for="reportDescription" class="form-label">Descrição</label>
                                    <textarea class="form-control" id="reportDescription" rows="3"></textarea>
                                </div>

                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="reportStartDate" class="form-label">Data Inicial</label>
                                        <input type="date" class="form-control" id="reportStartDate" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="reportEndDate" class="form-label">Data Final</label>
                                        <input type="date" class="form-control" id="reportEndDate" required>
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <label class="form-label">Servidores</label>
                                    <div id="serverSelection" class="border rounded p-3" style="max-height: 200px; overflow-y: auto;">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="selectAllServers" checked>
                                            <label class="form-check-label fw-bold" for="selectAllServers">
                                                Todos os Servidores
                                            </label>
                                        </div>
                                        <hr>
                                        <div id="serversList">
                                            <!-- Será preenchido dinamicamente -->
                                        </div>
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <label class="form-label">Seções do Relatório</label>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="includeSummary" checked>
                                                <label class="form-check-label" for="includeSummary">
                                                    Resumo Executivo
                                                </label>
                                            </div>
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="includeMetrics" checked>
                                                <label class="form-check-label" for="includeMetrics">
                                                    Métricas Detalhadas
                                                </label>
                                            </div>
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="includeCharts" checked>
                                                <label class="form-check-label" for="includeCharts">
                                                    Gráficos e Visualizações
                                                </label>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="includeAlerts" checked>
                                                <label class="form-check-label" for="includeAlerts">
                                                    Histórico de Alertas
                                                </label>
                                            </div>
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="includeRecommendations">
                                                <label class="form-check-label" for="includeRecommendations">
                                                    Recomendações
                                                </label>
                                            </div>
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="includeAppendix">
                                                <label class="form-check-label" for="includeAppendix">
                                                    Apêndice Técnico
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="reportFormat" class="form-label">Formato</label>
                                        <select class="form-select" id="reportFormat">
                                            <option value="pdf" selected>PDF</option>
                                            <option value="html">HTML</option>
                                            <option value="excel">Excel</option>
                                        </select>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="reportLanguage" class="form-label">Idioma</label>
                                        <select class="form-select" id="reportLanguage">
                                            <option value="pt-BR" selected>Português (Brasil)</option>
                                            <option value="en-US">English (US)</option>
                                            <option value="es-ES">Español</option>
                                        </select>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" onclick="reportsManager.generateReport()">
                                <i class="fas fa-file-pdf me-1"></i>Gerar Relatório
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove modal anterior se existir
        const existingModal = document.getElementById('generateReportModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Carrega lista de servidores
        this.loadServersForReport();
        
        // Define datas padrão
        this.setDefaultDates();
        
        // Configura event listeners do modal
        this.setupModalEventListeners();

        const modal = new bootstrap.Modal(document.getElementById('generateReportModal'));
        modal.show();
    }

    /**
     * Carrega servidores para seleção no relatório
     */
    async loadServersForReport() {
        try {
            const servers = await apiClient.getServers();
            const serversList = document.getElementById('serversList');
            
            const html = servers.map(server => `
                <div class="form-check">
                    <input class="form-check-input server-checkbox" type="checkbox" value="${server.id}" id="server_${server.id}" checked>
                    <label class="form-check-label" for="server_${server.id}">
                        ${this.escapeHtml(server.name)} 
                        <small class="text-muted">(${this.escapeHtml(server.host)})</small>
                    </label>
                </div>
            `).join('');
            
            serversList.innerHTML = html;
        } catch (error) {
            console.error('Erro ao carregar servidores:', error);
        }
    }

    /**
     * Define datas padrão para o relatório
     */
    setDefaultDates() {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 7); // 7 dias atrás

        document.getElementById('reportEndDate').value = endDate.toISOString().split('T')[0];
        document.getElementById('reportStartDate').value = startDate.toISOString().split('T')[0];
    }

    /**
     * Configura event listeners do modal
     */
    setupModalEventListeners() {
        // Checkbox "Todos os Servidores"
        document.getElementById('selectAllServers').addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('.server-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = e.target.checked;
            });
        });

        // Atualiza checkbox "Todos os Servidores" baseado na seleção individual
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('server-checkbox')) {
                const allCheckboxes = document.querySelectorAll('.server-checkbox');
                const checkedCheckboxes = document.querySelectorAll('.server-checkbox:checked');
                const selectAllCheckbox = document.getElementById('selectAllServers');
                
                if (selectAllCheckbox) {
                    selectAllCheckbox.checked = allCheckboxes.length === checkedCheckboxes.length;
                    selectAllCheckbox.indeterminate = checkedCheckboxes.length > 0 && checkedCheckboxes.length < allCheckboxes.length;
                }
            }
        });

        // Atualiza campos baseado no tipo de relatório
        document.getElementById('reportType').addEventListener('change', (e) => {
            this.updateFormBasedOnType(e.target.value);
        });
    }

    /**
     * Atualiza formulário baseado no tipo de relatório
     * @param {string} type - Tipo do relatório
     */
    updateFormBasedOnType(type) {
        const titleField = document.getElementById('reportTitle');
        const startDateField = document.getElementById('reportStartDate');
        const endDateField = document.getElementById('reportEndDate');

        const today = new Date();
        let startDate = new Date();
        let title = '';

        switch (type) {
            case 'daily':
                startDate.setDate(today.getDate() - 1);
                title = `Relatório Diário - ${today.toLocaleDateString('pt-BR')}`;
                break;
            case 'weekly':
                startDate.setDate(today.getDate() - 7);
                title = `Relatório Semanal - ${startDate.toLocaleDateString('pt-BR')} a ${today.toLocaleDateString('pt-BR')}`;
                break;
            case 'monthly':
                startDate.setMonth(today.getMonth() - 1);
                title = `Relatório Mensal - ${today.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}`;
                break;
            case 'performance':
                startDate.setDate(today.getDate() - 30);
                title = `Análise de Performance - Últimos 30 dias`;
                break;
            case 'availability':
                startDate.setDate(today.getDate() - 30);
                title = `Relatório de Disponibilidade - Últimos 30 dias`;
                break;
            default:
                startDate.setDate(today.getDate() - 7);
                title = 'Relatório Personalizado';
        }

        if (titleField.value === '' || titleField.value.includes('Relatório')) {
            titleField.value = title;
        }
        
        startDateField.value = startDate.toISOString().split('T')[0];
        endDateField.value = today.toISOString().split('T')[0];
    }

    /**
     * Gera um novo relatório
     */
    async generateReport() {
        const form = document.getElementById('generateReportForm');
        const selectedServers = Array.from(document.querySelectorAll('.server-checkbox:checked'))
            .map(input => parseInt(input.value));

        if (selectedServers.length === 0) {
            this.showNotification('Selecione pelo menos um servidor', 'warning');
            return;
        }

        const reportData = {
            title: document.getElementById('reportTitle').value,
            description: document.getElementById('reportDescription').value,
            type: document.getElementById('reportType').value,
            start_date: document.getElementById('reportStartDate').value,
            end_date: document.getElementById('reportEndDate').value,
            server_ids: selectedServers,
            format: document.getElementById('reportFormat').value,
            language: document.getElementById('reportLanguage').value,
            sections: {
                summary: document.getElementById('includeSummary').checked,
                metrics: document.getElementById('includeMetrics').checked,
                charts: document.getElementById('includeCharts').checked,
                alerts: document.getElementById('includeAlerts').checked,
                recommendations: document.getElementById('includeRecommendations').checked,
                appendix: document.getElementById('includeAppendix').checked
            }
        };

        try {
            const result = await apiClient.generateReport(reportData);
            bootstrap.Modal.getInstance(document.getElementById('generateReportModal')).hide();
            this.showNotification('Relatório iniciado com sucesso. Você será notificado quando estiver pronto.', 'success');
            await this.loadReports();
            
            // Inicia polling para verificar status
            this.pollReportStatus(result.id);
        } catch (error) {
            console.error('Erro ao gerar relatório:', error);
            this.showNotification('Erro ao gerar relatório', 'error');
        }
    }

    /**
     * Faz polling do status de um relatório
     * @param {number} reportId - ID do relatório
     */
    async pollReportStatus(reportId) {
        const maxAttempts = 60; // 5 minutos (5s * 60)
        let attempts = 0;

        const checkStatus = async () => {
            try {
                const report = await apiClient.getReport(reportId);
                
                if (report.status === 'completed') {
                    this.showNotification(`Relatório "${report.title}" gerado com sucesso!`, 'success');
                    await this.loadReports();
                    return;
                } else if (report.status === 'failed') {
                    this.showNotification(`Falha ao gerar relatório "${report.title}"`, 'error');
                    await this.loadReports();
                    return;
                } else if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(checkStatus, 5000); // Verifica a cada 5 segundos
                }
            } catch (error) {
                console.error('Erro ao verificar status do relatório:', error);
            }
        };

        setTimeout(checkStatus, 5000);
    }

    /**
     * Faz download de um relatório
     * @param {number} reportId - ID do relatório
     */
    async downloadReport(reportId) {
        try {
            const blob = await apiClient.downloadReport(reportId);
            const report = this.reports.find(r => r.id === reportId);
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${report.title}.${report.format || 'pdf'}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showNotification('Download iniciado', 'success');
        } catch (error) {
            console.error('Erro ao fazer download do relatório:', error);
            this.showNotification('Erro ao fazer download do relatório', 'error');
        }
    }

    /**
     * Visualiza um relatório
     * @param {number} reportId - ID do relatório
     */
    async previewReport(reportId) {
        try {
            const report = this.reports.find(r => r.id === reportId);
            const previewUrl = await apiClient.getReportPreviewUrl(reportId);
            
            // Abre em nova janela
            window.open(previewUrl, '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes');
        } catch (error) {
            console.error('Erro ao visualizar relatório:', error);
            this.showNotification('Erro ao visualizar relatório', 'error');
        }
    }

    /**
     * Tenta gerar novamente um relatório que falhou
     * @param {number} reportId - ID do relatório
     */
    async retryReport(reportId) {
        try {
            await apiClient.retryReport(reportId);
            this.showNotification('Relatório sendo gerado novamente', 'success');
            await this.loadReports();
            
            // Inicia polling para verificar status
            this.pollReportStatus(reportId);
        } catch (error) {
            console.error('Erro ao tentar gerar relatório novamente:', error);
            this.showNotification('Erro ao tentar gerar relatório novamente', 'error');
        }
    }

    /**
     * Visualiza detalhes de um relatório
     * @param {number} reportId - ID do relatório
     */
    async viewReportDetails(reportId) {
        const report = this.reports.find(r => r.id === reportId);
        if (!report) return;

        try {
            const details = await apiClient.getReportDetails(reportId);
            this.showReportDetailsModal(report, details);
        } catch (error) {
            console.error('Erro ao carregar detalhes do relatório:', error);
            this.showNotification('Erro ao carregar detalhes', 'error');
        }
    }

    /**
     * Exibe modal com detalhes do relatório
     * @param {Object} report - Dados do relatório
     * @param {Object} details - Detalhes adicionais
     */
    showReportDetailsModal(report, details) {
        const modalHTML = `
            <div class="modal fade" id="reportDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-file-pdf text-danger me-2"></i>
                                Detalhes do Relatório
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>Título:</strong><br>
                                    ${this.escapeHtml(report.title)}
                                </div>
                                <div class="col-md-6">
                                    <strong>Status:</strong><br>
                                    ${this.getStatusBadge(report.status)}
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>Tipo:</strong><br>
                                    ${this.getTypeBadge(report.type)}
                                </div>
                                <div class="col-md-6">
                                    <strong>Formato:</strong><br>
                                    ${report.format?.toUpperCase() || 'PDF'}
                                </div>
                            </div>

                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>Período:</strong><br>
                                    ${this.formatDate(report.start_date)} a ${this.formatDate(report.end_date)}
                                </div>
                                <div class="col-md-6">
                                    <strong>Criado em:</strong><br>
                                    ${this.formatDateTime(report.created_at)}
                                </div>
                            </div>

                            ${report.description ? `
                                <div class="mb-3">
                                    <strong>Descrição:</strong><br>
                                    <div class="alert alert-light">
                                        ${this.escapeHtml(report.description)}
                                    </div>
                                </div>
                            ` : ''}

                            ${details.servers ? `
                                <div class="mb-3">
                                    <strong>Servidores Incluídos:</strong><br>
                                    <div class="mt-2">
                                        ${details.servers.map(server => 
                                            `<span class="badge bg-secondary me-1 mb-1">${this.escapeHtml(server.name)}</span>`
                                        ).join('')}
                                    </div>
                                </div>
                            ` : ''}

                            ${details.sections ? `
                                <div class="mb-3">
                                    <strong>Seções Incluídas:</strong><br>
                                    <div class="row mt-2">
                                        <div class="col-md-6">
                                            ${details.sections.summary ? '<i class="fas fa-check text-success me-1"></i>Resumo Executivo<br>' : ''}
                                            ${details.sections.metrics ? '<i class="fas fa-check text-success me-1"></i>Métricas Detalhadas<br>' : ''}
                                            ${details.sections.charts ? '<i class="fas fa-check text-success me-1"></i>Gráficos<br>' : ''}
                                        </div>
                                        <div class="col-md-6">
                                            ${details.sections.alerts ? '<i class="fas fa-check text-success me-1"></i>Histórico de Alertas<br>' : ''}
                                            ${details.sections.recommendations ? '<i class="fas fa-check text-success me-1"></i>Recomendações<br>' : ''}
                                            ${details.sections.appendix ? '<i class="fas fa-check text-success me-1"></i>Apêndice Técnico<br>' : ''}
                                        </div>
                                    </div>
                                </div>
                            ` : ''}

                            ${report.file_size ? `
                                <div class="mb-3">
                                    <strong>Tamanho do Arquivo:</strong><br>
                                    ${this.formatFileSize(report.file_size)}
                                </div>
                            ` : ''}

                            ${report.error_message ? `
                                <div class="mb-3">
                                    <strong>Erro:</strong><br>
                                    <div class="alert alert-danger">
                                        <i class="fas fa-exclamation-triangle me-2"></i>
                                        ${this.escapeHtml(report.error_message)}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            ${report.status === 'completed' ? 
                                `<button type="button" class="btn btn-primary" onclick="reportsManager.downloadReport(${report.id}); bootstrap.Modal.getInstance(document.getElementById('reportDetailsModal')).hide();">
                                    <i class="fas fa-download me-1"></i>Download
                                </button>` : ''
                            }
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove modal anterior se existir
        const existingModal = document.getElementById('reportDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('reportDetailsModal'));
        modal.show();
    }

    /**
     * Remove um relatório
     * @param {number} reportId - ID do relatório
     */
    async deleteReport(reportId) {
        const report = this.reports.find(r => r.id === reportId);
        if (!report) return;

        const confirmed = confirm(`Tem certeza que deseja excluir o relatório "${report.title}"?`);
        if (!confirmed) return;

        try {
            await apiClient.deleteReport(reportId);
            this.showNotification('Relatório excluído com sucesso', 'success');
            await this.loadReports();
        } catch (error) {
            console.error('Erro ao excluir relatório:', error);
            this.showNotification('Erro ao excluir relatório', 'error');
        }
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Event listeners específicos dos relatórios
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
     * Atualiza dados dos relatórios
     */
    async refresh() {
        try {
            await this.loadReports();
        } catch (error) {
            console.error('Erro ao atualizar relatórios:', error);
        }
    }

    /**
     * Exibe erro na tabela de relatórios
     * @param {string} message - Mensagem de erro
     */
    showReportsError(message) {
        const tbody = document.getElementById('reports-table-body');
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                    <br>${message}
                    <br><button class="btn btn-sm btn-outline-primary mt-2" onclick="reportsManager.refresh()">
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
     * Formata data
     * @param {string} date - Data ISO
     * @returns {string} Data formatada
     */
    formatDate(date) {
        if (!date) return '';
        return new Date(date).toLocaleDateString('pt-BR');
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
     * Formata tamanho de arquivo
     * @param {number} bytes - Tamanho em bytes
     * @returns {string} Tamanho formatado
     */
    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
    }

    /**
     * Destrói o gerenciador e limpa recursos
     */
    destroy() {
        this.stopAutoRefresh();
        this.reports = [];
        this.isInitialized = false;
    }
}

// Instância global
const reportsManager = new ReportsManager();
window.reportsManager = reportsManager;
window.ReportsManager = ReportsManager;