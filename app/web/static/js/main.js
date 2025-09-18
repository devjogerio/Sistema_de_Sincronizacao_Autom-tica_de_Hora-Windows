/**
 * Main Application Module
 * Módulo principal responsável pela coordenação da aplicação web
 */

class NTPMonitorApp {
    constructor() {
        this.currentSection = 'dashboard';
        this.modules = {};
        this.isInitialized = false;
        this.notifications = [];
    }

    /**
     * Inicializa a aplicação
     */
    async init() {
        if (this.isInitialized) return;

        try {
            this.showLoadingScreen();
            
            // Verifica conectividade com a API
            await this.checkAPIConnection();
            
            // Inicializa módulos
            await this.initializeModules();
            
            // Configura navegação
            this.setupNavigation();
            
            // Configura eventos globais
            this.setupGlobalEvents();
            
            // Carrega seção inicial
            await this.showSection('dashboard');
            
            this.hideLoadingScreen();
            this.isInitialized = true;
            
            this.showNotification('Aplicação inicializada com sucesso', 'success');
            console.log('NTP Monitor App inicializado com sucesso');
            
        } catch (error) {
            console.error('Erro ao inicializar aplicação:', error);
            this.hideLoadingScreen();
            this.showError('Erro ao inicializar aplicação', error.message);
        }
    }

    /**
     * Verifica conectividade com a API
     */
    async checkAPIConnection() {
        try {
            await apiClient.getHealth();
        } catch (error) {
            throw new Error('Não foi possível conectar com a API. Verifique se o servidor está rodando.');
        }
    }

    /**
     * Inicializa todos os módulos
     */
    async initializeModules() {
        // Inicializa Dashboard
        this.modules.dashboard = new Dashboard();
        
        // Inicializa outros módulos quando disponíveis
        if (window.ServersManager) {
            this.modules.servers = new ServersManager();
        }
        
        if (window.PoolsManager) {
            this.modules.pools = new PoolsManager();
        }
        
        if (window.AlertsManager) {
            this.modules.alerts = new AlertsManager();
        }
        
        if (window.ReportsManager) {
            this.modules.reports = new ReportsManager();
        }
    }

    /**
     * Configura navegação entre seções
     */
    setupNavigation() {
        const navLinks = document.querySelectorAll('[data-section]');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('data-section');
                this.showSection(section);
            });
        });
    }

    /**
     * Configura eventos globais
     */
    setupGlobalEvents() {
        // Tratamento de erros globais
        window.addEventListener('error', (e) => {
            console.error('Erro global:', e.error);
            this.showNotification('Ocorreu um erro inesperado', 'error');
        });

        // Tratamento de promessas rejeitadas
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Promise rejeitada:', e.reason);
            this.showNotification('Erro de comunicação', 'error');
        });

        // Detecta mudanças de conectividade
        window.addEventListener('online', () => {
            this.showNotification('Conexão restaurada', 'success');
            this.refreshCurrentSection();
        });

        window.addEventListener('offline', () => {
            this.showNotification('Conexão perdida', 'warning');
        });

        // Atalhos de teclado
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        // Auto-refresh periódico
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                this.refreshCurrentSection();
            }
        }, 60000); // 1 minuto
    }

    /**
     * Exibe uma seção específica
     * @param {string} sectionName - Nome da seção
     */
    async showSection(sectionName) {
        try {
            // Oculta todas as seções
            const sections = document.querySelectorAll('.content-section');
            sections.forEach(section => {
                section.classList.add('d-none');
            });

            // Atualiza navegação
            this.updateNavigation(sectionName);

            // Exibe seção solicitada
            const targetSection = document.getElementById(`${sectionName}-section`);
            if (targetSection) {
                targetSection.classList.remove('d-none');
                targetSection.classList.add('fade-in');
            }

            // Inicializa módulo da seção se necessário
            await this.initializeSectionModule(sectionName);

            this.currentSection = sectionName;
            
            // Atualiza URL sem recarregar página
            history.pushState({ section: sectionName }, '', `#${sectionName}`);

        } catch (error) {
            console.error(`Erro ao exibir seção ${sectionName}:`, error);
            this.showNotification(`Erro ao carregar ${sectionName}`, 'error');
        }
    }

    /**
     * Atualiza estado da navegação
     * @param {string} activeSection - Seção ativa
     */
    updateNavigation(activeSection) {
        const navLinks = document.querySelectorAll('[data-section]');
        
        navLinks.forEach(link => {
            const section = link.getAttribute('data-section');
            if (section === activeSection) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    /**
     * Inicializa módulo específico da seção
     * @param {string} sectionName - Nome da seção
     */
    async initializeSectionModule(sectionName) {
        const module = this.modules[sectionName];
        
        if (module && typeof module.init === 'function' && !module.isInitialized) {
            await module.init();
        }
    }

    /**
     * Atualiza seção atual
     */
    async refreshCurrentSection() {
        const module = this.modules[this.currentSection];
        
        if (module && typeof module.refresh === 'function') {
            try {
                await module.refresh();
            } catch (error) {
                console.error(`Erro ao atualizar ${this.currentSection}:`, error);
            }
        }
    }

    /**
     * Trata atalhos de teclado
     * @param {KeyboardEvent} e - Evento de teclado
     */
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + R - Refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            this.refreshCurrentSection();
            return;
        }

        // Esc - Fechar modais
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
            return;
        }

        // Navegação por números (1-5)
        const sectionKeys = {
            '1': 'dashboard',
            '2': 'servers',
            '3': 'pools',
            '4': 'alerts',
            '5': 'reports'
        };

        if (e.altKey && sectionKeys[e.key]) {
            e.preventDefault();
            this.showSection(sectionKeys[e.key]);
        }
    }

    /**
     * Exibe tela de carregamento
     */
    showLoadingScreen() {
        const loadingHTML = `
            <div id="loading-screen" class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" 
                 style="background: rgba(255,255,255,0.9); z-index: 9999;">
                <div class="text-center">
                    <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <h5>Inicializando NTP Monitor...</h5>
                    <p class="text-muted">Conectando com a API e carregando dados</p>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', loadingHTML);
    }

    /**
     * Oculta tela de carregamento
     */
    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.remove();
        }
    }

    /**
     * Exibe notificação
     * @param {string} message - Mensagem
     * @param {string} type - Tipo (success, error, warning, info)
     * @param {number} duration - Duração em ms
     */
    showNotification(message, type = 'info', duration = 5000) {
        const notification = {
            id: Date.now(),
            message,
            type,
            timestamp: new Date()
        };

        this.notifications.push(notification);
        this.renderNotification(notification);

        // Remove automaticamente após duração especificada
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notification.id);
            }, duration);
        }
    }

    /**
     * Renderiza notificação na tela
     * @param {Object} notification - Dados da notificação
     */
    renderNotification(notification) {
        let container = document.getElementById('notifications-container');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const typeClasses = {
            success: 'alert-success',
            error: 'alert-danger',
            warning: 'alert-warning',
            info: 'alert-info'
        };

        const typeIcons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        const notificationHTML = `
            <div id="notification-${notification.id}" class="alert ${typeClasses[notification.type]} alert-dismissible fade show" role="alert">
                <i class="fas ${typeIcons[notification.type]} me-2"></i>
                ${notification.message}
                <button type="button" class="btn-close" onclick="app.removeNotification(${notification.id})"></button>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', notificationHTML);
    }

    /**
     * Remove notificação
     * @param {number} notificationId - ID da notificação
     */
    removeNotification(notificationId) {
        const element = document.getElementById(`notification-${notificationId}`);
        if (element) {
            element.classList.remove('show');
            setTimeout(() => element.remove(), 150);
        }

        this.notifications = this.notifications.filter(n => n.id !== notificationId);
    }

    /**
     * Exibe erro com detalhes
     * @param {string} title - Título do erro
     * @param {string} details - Detalhes do erro
     */
    showError(title, details = '') {
        const errorModal = `
            <div class="modal fade" id="errorModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-circle me-2"></i>
                                ${title}
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${details}</p>
                            <div class="mt-3">
                                <small class="text-muted">
                                    Verifique a console do navegador para mais detalhes técnicos.
                                </small>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                            <button type="button" class="btn btn-primary" onclick="location.reload()">
                                <i class="fas fa-sync-alt me-2"></i>Recarregar Página
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove modal anterior se existir
        const existingModal = document.getElementById('errorModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', errorModal);
        const modal = new bootstrap.Modal(document.getElementById('errorModal'));
        modal.show();
    }

    /**
     * Destrói a aplicação e limpa recursos
     */
    destroy() {
        // Para todos os módulos
        Object.values(this.modules).forEach(module => {
            if (module && typeof module.destroy === 'function') {
                module.destroy();
            }
        });

        // Limpa notificações
        this.notifications = [];
        const container = document.getElementById('notifications-container');
        if (container) {
            container.remove();
        }

        this.isInitialized = false;
    }
}

// Funções globais para formulários
window.addServer = async function() {
    const form = document.getElementById('addServerForm');
    const formData = new FormData(form);
    
    const serverData = {
        name: formData.get('serverName'),
        host: formData.get('serverHost'),
        port: parseInt(formData.get('serverPort')) || 123,
        description: formData.get('serverDescription') || ''
    };

    try {
        await apiClient.createServer(serverData);
        bootstrap.Modal.getInstance(document.getElementById('addServerModal')).hide();
        form.reset();
        app.showNotification('Servidor adicionado com sucesso', 'success');
        
        if (app.modules.servers) {
            app.modules.servers.refresh();
        }
    } catch (error) {
        console.error('Erro ao adicionar servidor:', error);
        app.showNotification('Erro ao adicionar servidor', 'error');
    }
};

window.generateReport = async function() {
    const form = document.getElementById('generateReportForm');
    const formData = new FormData(form);
    
    const reportData = {
        title: formData.get('reportTitle'),
        type: formData.get('reportType'),
        start_date: formData.get('reportStartDate'),
        end_date: formData.get('reportEndDate'),
        include_charts: formData.get('includeCharts') === 'on'
    };

    try {
        await apiClient.generateReport(reportData);
        bootstrap.Modal.getInstance(document.getElementById('generateReportModal')).hide();
        form.reset();
        app.showNotification('Relatório gerado com sucesso', 'success');
        
        if (app.modules.reports) {
            app.modules.reports.refresh();
        }
    } catch (error) {
        console.error('Erro ao gerar relatório:', error);
        app.showNotification('Erro ao gerar relatório', 'error');
    }
};

// Inicialização da aplicação
let app;

document.addEventListener('DOMContentLoaded', async () => {
    app = new NTPMonitorApp();
    window.app = app; // Disponibiliza globalmente
    
    try {
        await app.init();
    } catch (error) {
        console.error('Erro fatal na inicialização:', error);
    }
});

// Tratamento de navegação do browser
window.addEventListener('popstate', (e) => {
    if (e.state && e.state.section) {
        app.showSection(e.state.section);
    }
});

// Exporta para uso global
window.NTPMonitorApp = NTPMonitorApp;