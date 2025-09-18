/**
 * Utilities Module
 * Módulo com funções utilitárias para toda a aplicação
 */

/**
 * Classe para formatação de dados
 */
class DataFormatter {
    /**
     * Formata timestamp para data/hora legível
     * @param {string|Date} timestamp - Timestamp a ser formatado
     * @param {Object} options - Opções de formatação
     * @returns {string} Data formatada
     */
    static formatDateTime(timestamp, options = {}) {
        if (!timestamp) return 'Nunca';
        
        const date = new Date(timestamp);
        if (isNaN(date.getTime())) return 'Data inválida';
        
        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZone: 'America/Sao_Paulo'
        };
        
        return date.toLocaleString('pt-BR', { ...defaultOptions, ...options });
    }

    /**
     * Formata data sem horário
     * @param {string|Date} date - Data a ser formatada
     * @returns {string} Data formatada
     */
    static formatDate(date) {
        if (!date) return '';
        
        const dateObj = new Date(date);
        if (isNaN(dateObj.getTime())) return 'Data inválida';
        
        return dateObj.toLocaleDateString('pt-BR');
    }

    /**
     * Formata tempo relativo (ex: "2 horas atrás")
     * @param {string|Date} timestamp - Timestamp de referência
     * @returns {string} Tempo relativo formatado
     */
    static formatTimeAgo(timestamp) {
        if (!timestamp) return 'Nunca';
        
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        
        if (diffMs < 0) return 'No futuro';
        
        const diffSeconds = Math.floor(diffMs / 1000);
        const diffMinutes = Math.floor(diffSeconds / 60);
        const diffHours = Math.floor(diffMinutes / 60);
        const diffDays = Math.floor(diffHours / 24);
        const diffWeeks = Math.floor(diffDays / 7);
        const diffMonths = Math.floor(diffDays / 30);
        
        if (diffSeconds < 60) return 'Agora mesmo';
        if (diffMinutes < 60) return `${diffMinutes} min atrás`;
        if (diffHours < 24) return `${diffHours}h atrás`;
        if (diffDays < 7) return `${diffDays}d atrás`;
        if (diffWeeks < 4) return `${diffWeeks} sem atrás`;
        if (diffMonths < 12) return `${diffMonths} mês${diffMonths > 1 ? 'es' : ''} atrás`;
        
        const diffYears = Math.floor(diffMonths / 12);
        return `${diffYears} ano${diffYears > 1 ? 's' : ''} atrás`;
    }

    /**
     * Formata duração em milissegundos para formato legível
     * @param {number} ms - Duração em milissegundos
     * @returns {string} Duração formatada
     */
    static formatDuration(ms) {
        if (!ms || ms < 0) return '0ms';
        
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (ms < 1000) return `${ms}ms`;
        if (seconds < 60) return `${seconds}s`;
        if (minutes < 60) return `${minutes}min ${seconds % 60}s`;
        if (hours < 24) return `${hours}h ${minutes % 60}min`;
        return `${days}d ${hours % 24}h`;
    }

    /**
     * Formata tamanho de arquivo
     * @param {number} bytes - Tamanho em bytes
     * @param {number} decimals - Número de casas decimais
     * @returns {string} Tamanho formatado
     */
    static formatFileSize(bytes, decimals = 1) {
        if (!bytes || bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
    }

    /**
     * Formata número com separadores de milhares
     * @param {number} num - Número a ser formatado
     * @param {number} decimals - Número de casas decimais
     * @returns {string} Número formatado
     */
    static formatNumber(num, decimals = 0) {
        if (num === null || num === undefined) return '0';
        
        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    }

    /**
     * Formata porcentagem
     * @param {number} value - Valor decimal (0-1)
     * @param {number} decimals - Número de casas decimais
     * @returns {string} Porcentagem formatada
     */
    static formatPercentage(value, decimals = 1) {
        if (value === null || value === undefined) return '0%';
        
        return new Intl.NumberFormat('pt-BR', {
            style: 'percent',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    }

    /**
     * Formata latência/delay
     * @param {number} ms - Latência em milissegundos
     * @returns {string} Latência formatada
     */
    static formatLatency(ms) {
        if (ms === null || ms === undefined) return 'N/A';
        if (ms < 0) return 'Timeout';
        if (ms < 1) return '<1ms';
        return `${Math.round(ms)}ms`;
    }

    /**
     * Formata offset de tempo
     * @param {number} offset - Offset em milissegundos
     * @returns {string} Offset formatado
     */
    static formatOffset(offset) {
        if (offset === null || offset === undefined) return 'N/A';
        
        const absOffset = Math.abs(offset);
        const sign = offset >= 0 ? '+' : '-';
        
        if (absOffset < 1) return '±0ms';
        if (absOffset < 1000) return `${sign}${Math.round(absOffset)}ms`;
        
        const seconds = absOffset / 1000;
        if (seconds < 60) return `${sign}${seconds.toFixed(2)}s`;
        
        const minutes = seconds / 60;
        return `${sign}${minutes.toFixed(2)}min`;
    }
}

/**
 * Classe para validação de dados
 */
class DataValidator {
    /**
     * Valida endereço IP
     * @param {string} ip - Endereço IP
     * @returns {boolean} True se válido
     */
    static isValidIP(ip) {
        if (!ip || typeof ip !== 'string') return false;
        
        // IPv4
        const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        if (ipv4Regex.test(ip)) return true;
        
        // IPv6 (simplificado)
        const ipv6Regex = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
        return ipv6Regex.test(ip);
    }

    /**
     * Valida hostname
     * @param {string} hostname - Nome do host
     * @returns {boolean} True se válido
     */
    static isValidHostname(hostname) {
        if (!hostname || typeof hostname !== 'string') return false;
        
        const hostnameRegex = /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/;
        return hostnameRegex.test(hostname) && hostname.length <= 253;
    }

    /**
     * Valida porta
     * @param {number|string} port - Número da porta
     * @returns {boolean} True se válido
     */
    static isValidPort(port) {
        const portNum = parseInt(port);
        return !isNaN(portNum) && portNum >= 1 && portNum <= 65535;
    }

    /**
     * Valida email
     * @param {string} email - Endereço de email
     * @returns {boolean} True se válido
     */
    static isValidEmail(email) {
        if (!email || typeof email !== 'string') return false;
        
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Valida URL
     * @param {string} url - URL
     * @returns {boolean} True se válido
     */
    static isValidURL(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Valida intervalo numérico
     * @param {number} value - Valor a validar
     * @param {number} min - Valor mínimo
     * @param {number} max - Valor máximo
     * @returns {boolean} True se válido
     */
    static isInRange(value, min, max) {
        const num = parseFloat(value);
        return !isNaN(num) && num >= min && num <= max;
    }
}

/**
 * Classe para manipulação de DOM
 */
class DOMUtils {
    /**
     * Escapa HTML para prevenir XSS
     * @param {string} text - Texto a escapar
     * @returns {string} Texto escapado
     */
    static escapeHtml(text) {
        if (!text) return '';
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Remove todos os filhos de um elemento
     * @param {HTMLElement} element - Elemento pai
     */
    static clearChildren(element) {
        while (element.firstChild) {
            element.removeChild(element.firstChild);
        }
    }

    /**
     * Adiciona classe com animação
     * @param {HTMLElement} element - Elemento
     * @param {string} className - Nome da classe
     */
    static addClassWithAnimation(element, className) {
        element.classList.add(className);
        element.offsetHeight; // Force reflow
    }

    /**
     * Remove classe com animação
     * @param {HTMLElement} element - Elemento
     * @param {string} className - Nome da classe
     */
    static removeClassWithAnimation(element, className) {
        element.classList.remove(className);
        element.offsetHeight; // Force reflow
    }

    /**
     * Cria elemento com atributos
     * @param {string} tag - Tag do elemento
     * @param {Object} attributes - Atributos do elemento
     * @param {string} content - Conteúdo do elemento
     * @returns {HTMLElement} Elemento criado
     */
    static createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'dataset') {
                Object.entries(value).forEach(([dataKey, dataValue]) => {
                    element.dataset[dataKey] = dataValue;
                });
            } else {
                element.setAttribute(key, value);
            }
        });
        
        if (content) {
            element.innerHTML = content;
        }
        
        return element;
    }

    /**
     * Verifica se elemento está visível na viewport
     * @param {HTMLElement} element - Elemento a verificar
     * @returns {boolean} True se visível
     */
    static isElementVisible(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    /**
     * Rola suavemente até um elemento
     * @param {HTMLElement} element - Elemento de destino
     * @param {Object} options - Opções de scroll
     */
    static scrollToElement(element, options = {}) {
        const defaultOptions = {
            behavior: 'smooth',
            block: 'start',
            inline: 'nearest'
        };
        
        element.scrollIntoView({ ...defaultOptions, ...options });
    }
}

/**
 * Classe para manipulação de cores
 */
class ColorUtils {
    /**
     * Converte hex para RGB
     * @param {string} hex - Cor em hexadecimal
     * @returns {Object} Objeto com r, g, b
     */
    static hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    /**
     * Converte RGB para hex
     * @param {number} r - Vermelho (0-255)
     * @param {number} g - Verde (0-255)
     * @param {number} b - Azul (0-255)
     * @returns {string} Cor em hexadecimal
     */
    static rgbToHex(r, g, b) {
        return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
    }

    /**
     * Obtém cor baseada no status
     * @param {string} status - Status
     * @returns {string} Classe CSS da cor
     */
    static getStatusColor(status) {
        const colors = {
            'online': 'success',
            'offline': 'danger',
            'warning': 'warning',
            'unknown': 'secondary',
            'active': 'success',
            'inactive': 'secondary',
            'error': 'danger',
            'pending': 'warning',
            'completed': 'success',
            'failed': 'danger',
            'running': 'info'
        };
        
        return colors[status?.toLowerCase()] || 'secondary';
    }

    /**
     * Obtém cor baseada na qualidade (0-100)
     * @param {number} quality - Qualidade (0-100)
     * @returns {string} Classe CSS da cor
     */
    static getQualityColor(quality) {
        if (quality >= 90) return 'success';
        if (quality >= 70) return 'warning';
        if (quality >= 50) return 'danger';
        return 'dark';
    }

    /**
     * Obtém cor baseada na latência
     * @param {number} latency - Latência em ms
     * @returns {string} Classe CSS da cor
     */
    static getLatencyColor(latency) {
        if (latency < 50) return 'success';
        if (latency < 100) return 'warning';
        if (latency < 200) return 'danger';
        return 'dark';
    }
}

/**
 * Classe para debounce e throttle
 */
class FunctionUtils {
    /**
     * Cria função com debounce
     * @param {Function} func - Função a ser executada
     * @param {number} wait - Tempo de espera em ms
     * @param {boolean} immediate - Executar imediatamente
     * @returns {Function} Função com debounce
     */
    static debounce(func, wait, immediate = false) {
        let timeout;
        
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            
            if (callNow) func.apply(this, args);
        };
    }

    /**
     * Cria função com throttle
     * @param {Function} func - Função a ser executada
     * @param {number} limit - Limite de tempo em ms
     * @returns {Function} Função com throttle
     */
    static throttle(func, limit) {
        let inThrottle;
        
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Executa função de forma assíncrona com retry
     * @param {Function} func - Função a ser executada
     * @param {number} maxRetries - Número máximo de tentativas
     * @param {number} delay - Delay entre tentativas em ms
     * @returns {Promise} Promise da execução
     */
    static async retry(func, maxRetries = 3, delay = 1000) {
        let lastError;
        
        for (let i = 0; i <= maxRetries; i++) {
            try {
                return await func();
            } catch (error) {
                lastError = error;
                if (i < maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
                }
            }
        }
        
        throw lastError;
    }
}

/**
 * Classe para manipulação de localStorage
 */
class StorageUtils {
    /**
     * Salva item no localStorage com serialização JSON
     * @param {string} key - Chave
     * @param {*} value - Valor
     */
    static setItem(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Erro ao salvar no localStorage:', error);
        }
    }

    /**
     * Obtém item do localStorage com deserialização JSON
     * @param {string} key - Chave
     * @param {*} defaultValue - Valor padrão
     * @returns {*} Valor deserializado
     */
    static getItem(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Erro ao ler do localStorage:', error);
            return defaultValue;
        }
    }

    /**
     * Remove item do localStorage
     * @param {string} key - Chave
     */
    static removeItem(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Erro ao remover do localStorage:', error);
        }
    }

    /**
     * Limpa todo o localStorage
     */
    static clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('Erro ao limpar localStorage:', error);
        }
    }

    /**
     * Verifica se localStorage está disponível
     * @returns {boolean} True se disponível
     */
    static isAvailable() {
        try {
            const test = '__localStorage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch {
            return false;
        }
    }
}

/**
 * Classe para manipulação de URLs e parâmetros
 */
class URLUtils {
    /**
     * Obtém parâmetros da URL atual
     * @returns {Object} Objeto com parâmetros
     */
    static getURLParams() {
        const params = {};
        const urlParams = new URLSearchParams(window.location.search);
        
        for (const [key, value] of urlParams) {
            params[key] = value;
        }
        
        return params;
    }

    /**
     * Atualiza parâmetro da URL sem recarregar a página
     * @param {string} key - Chave do parâmetro
     * @param {string} value - Valor do parâmetro
     */
    static updateURLParam(key, value) {
        const url = new URL(window.location);
        
        if (value) {
            url.searchParams.set(key, value);
        } else {
            url.searchParams.delete(key);
        }
        
        window.history.replaceState({}, '', url);
    }

    /**
     * Constrói URL com parâmetros
     * @param {string} baseUrl - URL base
     * @param {Object} params - Parâmetros
     * @returns {string} URL completa
     */
    static buildURL(baseUrl, params = {}) {
        const url = new URL(baseUrl);
        
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                url.searchParams.set(key, value);
            }
        });
        
        return url.toString();
    }
}

/**
 * Classe para notificações
 */
class NotificationUtils {
    /**
     * Exibe notificação toast
     * @param {string} message - Mensagem
     * @param {string} type - Tipo (success, error, warning, info)
     * @param {number} duration - Duração em ms
     */
    static showToast(message, type = 'info', duration = 5000) {
        const toastContainer = this.getOrCreateToastContainer();
        const toast = this.createToastElement(message, type);
        
        toastContainer.appendChild(toast);
        
        // Anima entrada
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove automaticamente
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }

    /**
     * Obtém ou cria container de toasts
     * @returns {HTMLElement} Container de toasts
     */
    static getOrCreateToastContainer() {
        let container = document.getElementById('toast-container');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        
        return container;
    }

    /**
     * Cria elemento de toast
     * @param {string} message - Mensagem
     * @param {string} type - Tipo
     * @returns {HTMLElement} Elemento de toast
     */
    static createToastElement(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${ColorUtils.getStatusColor(type)} border-0`;
        toast.setAttribute('role', 'alert');
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="${icons[type] || icons.info} me-2"></i>
                    ${DOMUtils.escapeHtml(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        return toast;
    }
}

// Exporta classes para uso global
window.DataFormatter = DataFormatter;
window.DataValidator = DataValidator;
window.DOMUtils = DOMUtils;
window.ColorUtils = ColorUtils;
window.FunctionUtils = FunctionUtils;
window.StorageUtils = StorageUtils;
window.URLUtils = URLUtils;
window.NotificationUtils = NotificationUtils;

// Funções globais de conveniência
window.formatDateTime = DataFormatter.formatDateTime;
window.formatTimeAgo = DataFormatter.formatTimeAgo;
window.formatFileSize = DataFormatter.formatFileSize;
window.formatLatency = DataFormatter.formatLatency;
window.escapeHtml = DOMUtils.escapeHtml;
window.showToast = NotificationUtils.showToast;
window.debounce = FunctionUtils.debounce;
window.throttle = FunctionUtils.throttle;