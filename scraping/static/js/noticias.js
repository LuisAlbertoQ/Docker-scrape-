// ===== CONFIGURACIÓN GLOBAL MEJORADA =====
const CONFIG = {
    ANIMATION_DELAY: 100,
    NOTIFICATION_DURATION: 3000,
    SEARCH_DEBOUNCE: 300,
    MAX_RETRIES: 3,
    REQUEST_TIMEOUT: 30000,
    LAZY_LOAD_THRESHOLD: 0.1,
    LAZY_LOAD_ROOT_MARGIN: '50px'
};

// ===== CACHE DE DOM MEJORADO =====
class DOMCache {
    constructor() {
        this.cache = new Map();
        this.observers = new Map();
    }
    
    get(selector) {
        if (!this.cache.has(selector)) {
            this.cache.set(selector, document.querySelector(selector));
        }
        return this.cache.get(selector);
    }
    
    getAll(selector) {
        const key = `all:${selector}`;
        if (!this.cache.has(key)) {
            this.cache.set(key, document.querySelectorAll(selector));
        }
        return this.cache.get(key);
    }
    
    clear(selector = null) {
        if (selector) {
            this.cache.delete(selector);
            this.cache.delete(`all:${selector}`);
        } else {
            this.cache.clear();
        }
    }
}

// Inicializar cache global
const domCache = new DOMCache();

// ===== MANEJO DE ESTADO GLOBAL =====
class AppState {
    constructor() {
        this.state = {
            isLoading: false,
            filters: new Map(),
            currentPage: 1,
            scrollPosition: 0,
            pendingRequests: new Set()
        };
        
        this.listeners = new Map();
        this.debounceTimers = new Map();
    }
    
    set(key, value) {
        const oldValue = this.state[key];
        this.state[key] = value;
        this.notify(key, value, oldValue);
    }
    
    get(key) {
        return this.state[key];
    }
    
    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(callback);
        
        // Retornar función para desuscribirse
        return () => {
            this.listeners.get(key)?.delete(callback);
        };
    }
    
    notify(key, newValue, oldValue) {
        this.listeners.get(key)?.forEach(callback => {
            try {
                callback(newValue, oldValue);
            } catch (error) {
                console.error(`Error in listener for ${key}:`, error);
            }
        });
    }
    
    debounce(key, callback, delay = CONFIG.SEARCH_DEBOUNCE) {
        clearTimeout(this.debounceTimers.get(key));
        this.debounceTimers.set(key, setTimeout(callback, delay));
    }
    
    addPendingRequest(requestId) {
        this.state.pendingRequests.add(requestId);
        this.set('isLoading', this.state.pendingRequests.size > 0);
    }
    
    removePendingRequest(requestId) {
        this.state.pendingRequests.delete(requestId);
        this.set('isLoading', this.state.pendingRequests.size > 0);
    }
}

const appState = new AppState();

// ===== SISTEMA DE NOTIFICACIONES MEJORADO =====
class NotificationSystem {
    constructor() {
        this.container = null;
        this.queue = [];
        this.isShowing = false;
        this.init();
    }
    
    init() {
        // Crear contenedor de notificaciones
        this.container = document.createElement('div');
        this.container.className = 'notifications-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'info', duration = CONFIG.NOTIFICATION_DURATION) {
        const notification = {
            id: `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            message,
            type,
            duration,
            timestamp: Date.now()
        };
        
        this.queue.push(notification);
        this.processQueue();
    }
    
    processQueue() {
        if (this.isShowing || this.queue.length === 0) return;
        
        this.isShowing = true;
        const notification = this.queue.shift();
        this.createNotificationElement(notification);
    }
    
    createNotificationElement(notification) {
        const element = document.createElement('div');
        element.id = notification.id;
        element.className = `notification ${notification.type}`;
        
        const colors = {
            success: '#27ae60',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };
        
        element.style.cssText = `
            background: ${colors[notification.type] || colors.info};
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            animation: slideInFromRight 0.3s ease;
            max-width: 350px;
            font-weight: 500;
            pointer-events: auto;
            transform: translateX(0);
            transition: transform 0.3s ease, opacity 0.3s ease;
        `;
        
        element.innerHTML = `
            <i class="fas ${this.getIconForType(notification.type)}"></i>
            <span style="flex: 1;">${notification.message}</span>
            <button class="notification-close" style="background: none; border: none; color: white; cursor: pointer; font-size: 16px;">&times;</button>
        `;
        
        this.container.appendChild(element);
        
        const closeBtn = element.querySelector('.notification-close');
        this.setupNotificationEvents(element, closeBtn, notification);
        
        // Auto-remove
        const autoRemove = setTimeout(() => {
            this.removeNotification(element);
        }, notification.duration);
        
        // Guardar timer para cleanup
        element._autoRemoveTimer = autoRemove;
    }
    
    setupNotificationEvents(element, closeBtn, notification) {
        // Cerrar al hacer click
        closeBtn.addEventListener('click', () => {
            clearTimeout(element._autoRemoveTimer);
            this.removeNotification(element);
        });
        
        // Pausar en hover
        element.addEventListener('mouseenter', () => {
            clearTimeout(element._autoRemoveTimer);
        });
        
        element.addEventListener('mouseleave', () => {
            clearTimeout(element._autoRemoveTimer);
            element._autoRemoveTimer = setTimeout(() => {
                this.removeNotification(element);
            }, notification.duration);
        });
    }
    
    removeNotification(element) {
        if (!element || !element.parentNode) return;
        
        element.style.transform = 'translateX(100%)';
        element.style.opacity = '0';
        
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
            this.isShowing = false;
            this.processQueue();
        }, 300);
    }
    
    getIconForType(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }
    
    clearAll() {
        this.queue = [];
        const notifications = this.container.querySelectorAll('.notification');
        notifications.forEach(notification => {
            clearTimeout(notification._autoRemoveTimer);
            this.removeNotification(notification);
        });
    }
}

// Inicializar sistema de notificaciones
const notificationSystem = new NotificationSystem();

// Función global mejorada
function showNotification(message, type = 'info') {
    notificationSystem.show(message, type);
}

// ===== SISTEMA DE FILTROS AVANZADO MEJORADO =====
class FilterManager {
    constructor() {
        this.form = domCache.get('#filter-form');
        this.fechaSelect = domCache.get('#fecha-select');
        this.dateRangeGroup = domCache.get('#date-range-group');
        this.handlers = [];
        this.isInitialized = false;
    }
    
    init() {
        if (!this.form || this.isInitialized) return;
        
        try {
            // Manejar cambio en selector de fecha
            if (this.fechaSelect) {
                this.addHandler(this.fechaSelect, 'change', () => this.toggleDateRange());
                // Inicializar estado
                this.toggleDateRange();
            }
            
            // Prevenir submit si rango está incompleto
            this.addHandler(this.form, 'submit', (e) => this.validateForm(e));
            
            // Auto-submit mejorado
            this.setupAutoSubmit();
            
            // Sincronizar con estado global
            this.syncWithGlobalState();
            
            this.isInitialized = true;
            console.log('✅ FilterManager inicializado');
        } catch (error) {
            console.error('❌ Error inicializando FilterManager:', error);
        }
    }
    
    addHandler(element, event, handler) {
        if (!element) return;
        element.addEventListener(event, handler);
        this.handlers.push({ element, event, handler });
    }
    
    toggleDateRange() {
        if (!this.dateRangeGroup) return;
        
        const isRangoSelected = this.fechaSelect.value === 'rango';
        this.dateRangeGroup.style.display = isRangoSelected ? 'block' : 'none';
        
        // Animación suave
        if (isRangoSelected) {
            setTimeout(() => {
                this.dateRangeGroup.style.opacity = '1';
                this.dateRangeGroup.style.transform = 'translateY(0)';
            }, 50);
        } else {
            this.dateRangeGroup.style.opacity = '0';
            this.dateRangeGroup.style.transform = 'translateY(-10px)';
        }
        
        // Limpiar fechas si no es rango
        if (!isRangoSelected) {
            const inputs = this.dateRangeGroup.querySelectorAll('input[type="date"]');
            inputs.forEach(input => input.value = '');
        }
    }
    
    validateForm(e) {
        if (this.fechaSelect.value === 'rango') {
            const fechaDesde = domCache.get('input[name="fecha_desde"]');
            const fechaHasta = domCache.get('input[name="fecha_hasta"]');
            
            if (!fechaDesde?.value || !fechaHasta?.value) {
                e.preventDefault();
                showNotification('Por favor, selecciona ambas fechas para el rango', 'warning');
                return false;
            }
            
            if (new Date(fechaDesde.value) > new Date(fechaHasta.value)) {
                e.preventDefault();
                showNotification('La fecha inicial no puede ser mayor a la fecha final', 'error');
                return false;
            }
        }
        
        // Mostrar loading con estado global
        const submitBtn = this.form.querySelector('button[type="submit"]');
        if (submitBtn) {
            const requestId = `form-submit-${Date.now()}`;
            appState.addPendingRequest(requestId);
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Filtrando...';
            
            // Limpiar después de 30s por si falla
            setTimeout(() => {
                if (appState.get('pendingRequests').has(requestId)) {
                    appState.removePendingRequest(requestId);
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Filtrar';
                    showNotification('La solicitud tardó demasiado tiempo', 'error');
                }
            }, CONFIG.REQUEST_TIMEOUT);
        }
        
        return true;
    }
    
    setupAutoSubmit() {
        // Auto-submit para filtros rápidos
        const quickFilters = this.form.querySelectorAll('select.auto-submit, input.auto-submit');
        quickFilters.forEach(element => {
            this.addHandler(element, 'change', () => {
                if (this.validateForm({ preventDefault: () => {} })) {
                    this.form.submit();
                }
            });
        });
    }
    
    syncWithGlobalState() {
        // Sincronizar filtros activos con estado global
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.forEach((value, key) => {
            appState.set('filters', new Map([...appState.get('filters'), [key, value]]));
        });
    }
    
    clear() {
        clearFilters();
    }
    
    removeFilter(filterName) {
        removeFilter(filterName);
    }
    
    destroy() {
        this.handlers.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.handlers = [];
        this.isInitialized = false;
    }
}

// ===== MANEJO DE IMÁGENES MEJORADO =====
class ImageManager {
    constructor() {
        this.observer = null;
        this.failedImages = new Set();
        this.init();
    }
    
    init() {
        this.setupIntersectionObserver();
        this.setupImageErrorHandling();
    }
    
    setupIntersectionObserver() {
        if (!('IntersectionObserver' in window)) {
            this.loadAllImages();
            return;
        }
        
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadImage(entry.target);
                    this.observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: CONFIG.LAZY_LOAD_THRESHOLD,
            rootMargin: CONFIG.LAZY_LOAD_ROOT_MARGIN
        });
        
        this.observeImages();
    }
    
    observeImages() {
        const images = domCache.getAll('img[data-src]');
        images.forEach(img => {
            if (!this.failedImages.has(img.dataset.src)) {
                this.observer.observe(img);
            }
        });
    }
    
    loadImage(img) {
        const src = img.dataset.src;
        if (!src || this.failedImages.has(src)) return;
        
        img.style.opacity = '0.5';
        img.style.transition = 'opacity 0.3s ease';
        
        const tempImg = new Image();
        tempImg.onload = () => {
            img.src = src;
            img.removeAttribute('data-src');
            img.style.opacity = '1';
            img.closest('.image-container')?.classList.add('loaded');
            
            // Mejorar performance
            setTimeout(() => {
                img.style.transition = '';
            }, 300);
        };
        
        tempImg.onerror = () => {
            this.failedImages.add(src);
            this.showPlaceholder(img);
        };
        
        tempImg.src = src;
    }
    
    showPlaceholder(img) {
        const container = img.closest('.image-container');
        if (!container) return;
        
        const placeholder = document.createElement('div');
        placeholder.className = 'image-placeholder';
        placeholder.innerHTML = '<i class="fas fa-image"></i>';
        placeholder.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 24px;
            width: 100%;
            height: 100%;
            min-height: 150px;
        `;
        
        container.replaceChild(placeholder, img);
    }
    
    loadAllImages() {
        const images = domCache.getAll('img[data-src]');
        images.forEach(img => this.loadImage(img));
    }
    
    setupImageErrorHandling() {
        // Manejar errores de imágenes que no cargan
        document.addEventListener('error', (e) => {
            if (e.target.tagName === 'IMG' && e.target.hasAttribute('data-src')) {
                this.failedImages.add(e.target.dataset.src);
                this.showPlaceholder(e.target);
            }
        }, true);
    }
    
    refresh() {
        this.failedImages.clear();
        domCache.clear('img[data-src]');
        this.observeImages();
    }
}

// ===== SISTEMA DE CARD LAYOUT MEJORADO =====
class CardLayoutManager {
    constructor() {
        this.resizeObserver = null;
        this.currentLayout = 'auto';
        this.init();
    }
    
    init() {
        this.setupResizeObserver();
        this.assignInitialSizes();
    }
    
    setupResizeObserver() {
        if (!('ResizeObserver' in window)) return;
        
        this.resizeObserver = new ResizeObserver((entries) => {
            // Debounce para evitar múltiples ejecuciones
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 100);
        });
        
        const container = domCache.get('.news-grid, .cards-container');
        if (container) {
            this.resizeObserver.observe(container);
        }
    }
    
    handleResize() {
        const width = window.innerWidth;
        
        if (width < 768 && this.currentLayout !== 'mobile') {
            this.applyMobileLayout();
        } else if (width >= 768 && this.currentLayout !== 'desktop') {
            this.applyDesktopLayout();
        }
    }
    
    applyMobileLayout() {
        this.currentLayout = 'mobile';
        const cards = domCache.getAll('.news-card');
        
        cards.forEach(card => {
            card.classList.remove('large', 'medium', 'small');
            card.classList.add('mobile');
        });
    }
    
    applyDesktopLayout() {
        this.currentLayout = 'desktop';
        this.assignCardSizes();
    }
    
    assignInitialSizes() {
        if (window.innerWidth < 768) {
            this.applyMobileLayout();
        } else {
            this.assignCardSizes();
        }
    }
    
    assignCardSizes() {
        const cards = domCache.getAll('.news-card');
        const totalCards = cards.length;
        
        if (totalCards === 0) return;
        
        cards.forEach((card, index) => {
            card.classList.remove('large', 'medium', 'small', 'mobile');
            
            // Lógica mejorada de tamaños
            if (totalCards >= 8) {
                // Patrón para muchas cards
                if (index === 0 || (index + 1) % 8 === 0) {
                    card.classList.add('large');
                } else if ((index + 1) % 4 === 0 || (index + 1) % 5 === 0) {
                    card.classList.add('medium');
                } else {
                    card.classList.add('small');
                }
            } else if (totalCards >= 4) {
                // Patrón para cantidad media
                if (index === 0) {
                    card.classList.add('large');
                } else if (index === 1 || index === 2) {
                    card.classList.add('medium');
                } else {
                    card.classList.add('small');
                }
            } else {
                // Todas medianas para pocas cards
                card.classList.add('medium');
            }
            
            // Animación escalonada
            card.style.animationDelay = `${(index * 0.08)}s`;
        });
    }
    
    refresh() {
        domCache.clear('.news-card');
        this.assignInitialSizes();
    }
    
    destroy() {
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        clearTimeout(this.resizeTimeout);
    }
}

// ===== SCRAPING MANAGER MEJORADO =====
class ScrapingManager {
    constructor() {
        this.buttons = [
            { id: 'scraping-btn', endpoint: '/scraping/lista', category: 'general' },
            { id: 'scraping-tecnologia-btn', endpoint: '/scraping/tecnologia', category: 'tecnología' },
            { id: 'scraping-mundo-btn', endpoint: '/scraping/mundo', category: 'mundo' },
            { id: 'scraping-economia-btn', endpoint: '/scraping/economia', category: 'economía' },
            { id: 'scraping-politica-btn', endpoint: '/scraping/politica', category: 'política' },
            { id: 'scraping-lista-btn', endpoint: '/scraping/lista', category: 'lista' },
            { id: 'scraping-peru21-btn', endpoint: '/scraping/peru21', category: 'perugeneral' },
            { id: 'scraping-peru21-deportes-btn', endpoint: '/scraping/peru21/deportes', category: 'perudeportes' },
            { id: 'scraping-peru21-gastronomia-btn', endpoint: '/scraping/peru21/gastronomia', category: 'perugastronomia' },
            { id: 'scraping-peru21-investigacion-btn', endpoint: '/scraping/peru21/investigacion', category: 'peruinvestigacion' },
            { id: 'scraping-peru21-lima-btn', endpoint: '/scraping/peru21/lima', category: 'perulima' }
        ];
        
        this.activeRequests = new Map();
    }
    
    init() {
        this.setupButtons();
        this.setupGlobalHandlers();
    }
    
    setupButtons() {
        this.buttons.forEach(({ id, endpoint, category }) => {
            const btn = domCache.get(`#${id}`);
            if (btn) {
                btn.addEventListener('click', () => this.handleScraping(btn, endpoint, category));
            }
        });
    }
    
    async handleScraping(button, endpoint, category) {
        const requestId = `scraping-${category}-${Date.now()}`;
        
        if (this.activeRequests.has(requestId)) {
            showNotification('Ya hay una solicitud de scraping en proceso', 'warning');
            return;
        }
        
        const originalHTML = button.innerHTML;
        const originalDisabled = button.disabled;
        
        try {
            appState.addPendingRequest(requestId);
            this.activeRequests.set(requestId, button);
            
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scrapeando...';
            button.classList.add('loading', 'scraping-active');
            
            // Obtener el token CSRF
            const csrfToken = this.getCSRFToken();
            
            // SIN TIMEOUT para scraping
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `csrfmiddlewaretoken=${encodeURIComponent(csrfToken)}`,
                credentials: 'same-origin'
            });
            
            // Verificar respuesta
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Respuesta no JSON: ${text.substring(0, 100)}...`);
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `Error HTTP ${response.status}`);
            }
            
            if (data.status === 'ok') {
                showNotification(data.message || `¡Scraping de ${category} completado!`, 'success');
                
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
                
            } else {
                throw new Error(data.message || data.error || 'Error desconocido');
            }
            
        } catch (error) {
            console.error(`Error en scraping (${category}):`, error);
            
            let errorMessage = 'Error en el scraping';
            if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                errorMessage = 'Error de conexión. Verifica tu internet.';
            } else if (error.message.includes('403')) {
                errorMessage = 'Error de permisos. Recarga la página.';
            } else if (error.message.includes('Respuesta no JSON')) {
                errorMessage = 'Error en el servidor. La respuesta no es válida.';
            }
            
            showNotification(`${errorMessage}: ${category}`, 'error');
            
            // Restaurar botón
            button.disabled = originalDisabled;
            button.innerHTML = originalHTML;
            button.classList.remove('loading', 'scraping-active');
            
        } finally {
            appState.removePendingRequest(requestId);
            this.activeRequests.delete(requestId);
        }
    }
    
    getCSRFToken() {
        // Método 1: Buscar en las cookies
        const cookieToken = getCookie('csrftoken');
        if (cookieToken) return cookieToken;
        
        // Método 2: Buscar en el meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) return metaToken.getAttribute('content');
        
        // Método 3: Buscar en el form
        const formToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (formToken) return formToken.value;
        
        console.error('No se pudo encontrar el token CSRF');
        showNotification('Error de seguridad: no se pudo verificar la solicitud', 'error');
        return '';
    }
    
    async fetchWithTimeout(url, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                credentials: 'same-origin' // Importante para incluir cookies
            });
            
            clearTimeout(timeoutId);
            return response;
            
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }
    
    setupGlobalHandlers() {
        // Cancelar todas las solicitudes al salir de la página
        window.addEventListener('beforeunload', () => {
            this.activeRequests.forEach((button, requestId) => {
                appState.removePendingRequest(requestId);
            });
        });
    }
    
    cancelAll() {
        this.activeRequests.forEach((button, requestId) => {
            appState.removePendingRequest(requestId);
            button.disabled = false;
            button.innerHTML = 'Scraping';
            button.classList.remove('loading', 'scraping-active');
        });
        this.activeRequests.clear();
    }
}

// ===== FUNCIONES GLOBALES MEJORADAS =====
window.clearFilters = function() {
    const url = new URL(window.location);
    const perPage = url.searchParams.get('per_page');
    url.search = '';
    if (perPage) {
        url.searchParams.set('per_page', perPage);
    }
    window.location.href = url.toString();
};

window.removeFilter = function(filterName) {
    const url = new URL(window.location);
    url.searchParams.delete(filterName);
    
    // Si se elimina fecha, también eliminar rango
    if (filterName === 'fecha') {
        url.searchParams.delete('fecha_desde');
        url.searchParams.delete('fecha_hasta');
    }
    
    window.location.href = url.toString();
};

window.compartirNoticia = function(titulo, enlace) {
    const url = enlace || window.location.href;
    const texto = `📰 ${titulo}`;
    
    if (navigator.share) {
        navigator.share({
            title: titulo,
            text: texto,
            url: url
        }).catch(err => {
            if (err.name !== 'AbortError') {
                this.fallbackShare(texto, url);
            }
        });
    } else {
        this.fallbackShare(texto, url);
    }
};

window.fallbackShare = function(texto, url) {
    const shareText = `${texto}\n${url}`;
    
    if (navigator.clipboard && !this.isMobileDevice()) {
        navigator.clipboard.writeText(shareText)
            .then(() => {
                showNotification('¡Enlace copiado al portapapeles!', 'success');
            })
            .catch(() => {
                this.legacyCopy(shareText);
            });
    } else {
        this.legacyCopy(shareText);
    }
};

window.legacyCopy = function(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.cssText = `
        position: fixed;
        left: -9999px;
        opacity: 0;
        pointer-events: none;
    `;
    
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (successful) {
            showNotification('¡Enlace copiado al portapapeles!', 'success');
        } else {
            showNotification('No se pudo copiar el enlace', 'error');
        }
    } catch (err) {
        document.body.removeChild(textArea);
        showNotification('Error al copiar el enlace', 'error');
    }
};

window.isMobileDevice = function() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

// ===== MANEJO DE PAGINACIÓN MEJORADO =====
function setupPagination() {
    const paginacion = domCache.get('.pagination');
    if (!paginacion) return;
    
    paginacion.addEventListener('click', function(e) {
        const target = e.target.closest('.page-link');
        if (!target) return;
        
        e.preventDefault();
        
        // Scroll suave al inicio
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        // Mostrar indicador de carga
        const requestId = `pagination-${Date.now()}`;
        appState.addPendingRequest(requestId);
        
        // Navegar después de un pequeño delay para que se vea la animación
        setTimeout(() => {
            window.location.href = target.href;
        }, 150);
    });
}

// ===== SELECTOR DE ELEMENTOS POR PÁGINA MEJORADO =====
function setupPerPageSelector() {
    const select = domCache.get('#per-page');
    if (!select) return;
    
    select.addEventListener('change', function() {
        const perPage = this.value;
        const url = new URL(window.location);
        url.searchParams.set('per_page', perPage);
        url.searchParams.set('page', '1');
        
        showNotification(`Mostrando ${perPage} noticias por página`, 'info');
        
        const requestId = `perpage-${Date.now()}`;
        appState.addPendingRequest(requestId);
        
        window.location.href = url.toString();
    });
}

// ===== BÚSQUEDA EN TIEMPO REAL MEJORADA =====
function setupLiveSearch() {
    const searchInput = domCache.get('input[name="q"]');
    if (!searchInput) return;
    
    let searchTimeout;
    const originalPlaceholder = searchInput.placeholder;
    const form = searchInput.closest('form');
    
    // Debounced search
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        
        const value = this.value.trim();
        
        if (value.length > 2) {
            searchTimeout = setTimeout(() => {
                this.placeholder = 'Buscando...';
                form.submit();
            }, CONFIG.SEARCH_DEBOUNCE);
        } else if (value.length === 0) {
            this.placeholder = originalPlaceholder;
        }
    });
    
    // Búsqueda al presionar Enter
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            clearTimeout(searchTimeout);
            form.submit();
        }
    });
    
    // Limpiar búsqueda
    const clearBtn = domCache.get('.search-clear');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            searchInput.value = '';
            searchInput.focus();
            form.submit();
        });
    }
}

// ===== NAVEGACIÓN MÓVIL MEJORADA =====
function setupMobileNavigation() {
    const mobileToggle = domCache.get('.mobile-toggle');
    const navWrapper = domCache.get('.nav-wrapper');
    
    if (!mobileToggle || !navWrapper) return;
    
    let isAnimating = false;
    
    mobileToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        
        if (isAnimating) return;
        isAnimating = true;
        
        navWrapper.classList.toggle('active');
        
        const icon = mobileToggle.querySelector('i');
        if (navWrapper.classList.contains('active')) {
            icon.className = 'fas fa-times';
            document.body.style.overflow = 'hidden';
        } else {
            icon.className = 'fas fa-bars';
            document.body.style.overflow = '';
        }
        
        setTimeout(() => {
            isAnimating = false;
        }, 300);
    });

    // Cerrar al hacer click en un link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768 && navWrapper.classList.contains('active')) {
                navWrapper.classList.remove('active');
                mobileToggle.querySelector('i').className = 'fas fa-bars';
                document.body.style.overflow = '';
            }
        });
    });

    // Cerrar al hacer click fuera
    document.addEventListener('click', (e) => {
        if (!mobileToggle.contains(e.target) && !navWrapper.contains(e.target)) {
            if (navWrapper.classList.contains('active')) {
                navWrapper.classList.remove('active');
                mobileToggle.querySelector('i').className = 'fas fa-bars';
                document.body.style.overflow = '';
            }
        }
    });
    
    // Cerrar con Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && navWrapper.classList.contains('active')) {
            navWrapper.classList.remove('active');
            mobileToggle.querySelector('i').className = 'fas fa-bars';
            document.body.style.overflow = '';
        }
    });
}

// ===== ANIMACIONES DE SCROLL MEJORADAS =====
function initScrollAnimations() {
    if (!('IntersectionObserver' in window)) {
        document.querySelectorAll('.news-card').forEach(card => {
            card.classList.add('fade-in');
        });
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: CONFIG.LAZY_LOAD_THRESHOLD,
        rootMargin: CONFIG.LAZY_LOAD_ROOT_MARGIN
    });

    document.querySelectorAll('.news-card, .fade-on-scroll').forEach(element => {
        observer.observe(element);
    });
}

// ===== MANEJO DE ERRORES MEJORADO =====
function setupErrorHandling() {
    // Error global
    window.addEventListener('error', function(e) {
        console.error('Error global:', e.error);
        // En producción, podrías enviar esto a un servicio de tracking
        if (window.location.hostname !== 'localhost') {
            // trackError(e.error);
        }
    });

    // Promise rejections
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Promise rechazada:', e.reason);
        e.preventDefault(); // Prevenir log en consola
    });

    // Error en carga de recursos
    window.addEventListener('error', function(e) {
        if (e.target.tagName === 'IMG') {
            const img = e.target;
            img.style.opacity = '0';
            setTimeout(() => {
                const placeholder = document.createElement('div');
                placeholder.className = 'image-placeholder';
                placeholder.innerHTML = '<i class="fas fa-image"></i>';
                img.parentNode.replaceChild(placeholder, img);
            }, 300);
        }
    }, true);
}

// ===== ACCESIBILIDAD MEJORADA =====
function setupKeyboardNavigation() {
    // Cards navegables
    document.querySelectorAll('.news-card').forEach((card, index) => {
        card.setAttribute('tabindex', '0');
        card.setAttribute('role', 'article');
        card.setAttribute('aria-label', `Noticia ${index + 1}`);
        
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const link = card.querySelector('.read-more, .card-link');
                if (link) {
                    link.click();
                }
            }
        });
    });

    // Navegación con teclado
    document.addEventListener('keydown', (e) => {
        // Skip to main content
        if (e.key === 'Tab' && e.shiftKey && e.altKey) {
            const main = domCache.get('main, .main-content');
            if (main) {
                e.preventDefault();
                main.focus();
            }
        }
        
        // Cerrar notificaciones con Escape
        if (e.key === 'Escape') {
            notificationSystem.clearAll();
        }
    });

    // Mejorar focus visible
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });

    document.addEventListener('mousedown', () => {
        document.body.classList.remove('keyboard-navigation');
    });
}

// ===== FUNCIÓN PARA CSRF TOKEN (MEJORADA) =====
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ===== GESTIÓN DE MEMORIA Y PERFORMANCE =====
function setupPerformanceMonitoring() {
    // Cleanup antes de recargar la página
    window.addEventListener('beforeunload', () => {
        if (window.cardLayoutManager) {
            window.cardLayoutManager.destroy();
        }
        if (window.filterManager) {
            window.filterManager.destroy();
        }
        notificationSystem.clearAll();
    });
    
    // Monitor de performance (solo en desarrollo)
    if (window.location.hostname === 'localhost') {
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach((entry) => {
                if (entry.loadTime > 1000) {
                    console.warn('🕐 Lento:', entry.name, entry.loadTime);
                }
            });
        });
        
        observer.observe({ entryTypes: ['navigation', 'resource'] });
    }
}

// ===== INYECCIÓN DE ESTILOS MEJORADA =====
function injectStyles() {
    // Solo inyectar si no existen
    if (document.querySelector('style[data-injected="news-portal"]')) return;
    
    const styles = `
        @keyframes slideInFromRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideOutToRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .loading {
            position: relative;
            overflow: hidden;
        }

        .loading::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shimmer 1.5s infinite;
        }

        .fade-in {
            animation: fadeInUp 0.6s ease forwards;
        }

        .keyboard-navigation *:focus {
            outline: 2px solid #3498db;
            outline-offset: 2px;
        }

        .scraping-active {
            position: relative;
        }

        .scraping-active::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            border: 2px solid #27ae60;
            border-radius: inherit;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        /* Mejoras de accesibilidad */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
    `;

    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    styleSheet.setAttribute('data-injected', 'news-portal');
    document.head.appendChild(styleSheet);
}

// ===== INICIALIZACIÓN PRINCIPAL MEJORADA =====
class NewsPortalApp {
    constructor() {
        this.modules = new Map();
        this.isInitialized = false;
    }
    
    async initialize() {
        if (this.isInitialized) return;
        
        console.log('🚀 Inicializando portal de noticias mejorado...');
        
        try {
            // Inyectar estilos primero
            injectStyles();
            
            // Configurar manejo de errores
            setupErrorHandling();
            
            // Inicializar estado global
            this.setupGlobalState();
            
            // Inicializar módulos en orden de prioridad
            await this.initializeCriticalModules();
            
            // Inicializar módulos secundarios (lazy)
            requestIdleCallback(() => {
                this.initializeSecondaryModules();
            });
            
            // Configurar performance
            setupPerformanceMonitoring();
            
            this.isInitialized = true;
            console.log('✅ Portal mejorado inicializado correctamente');
            
        } catch (error) {
            console.error('❌ Error durante la inicialización:', error);
            showNotification('Error al cargar algunas funciones de la página', 'error');
            this.showFallbackUI();
        }
    }
    
    setupGlobalState() {
        // Suscribirse a cambios de estado global
        appState.subscribe('isLoading', (isLoading) => {
            if (isLoading) {
                document.body.classList.add('loading');
            } else {
                document.body.classList.remove('loading');
            }
        });
    }
    
    initializeCriticalModules() {
        return new Promise((resolve) => {
            // Módulos críticos que deben cargarse inmediatamente
            window.filterManager = new FilterManager();
            window.filterManager.init();
            
            window.imageManager = new ImageManager();
            
            window.cardLayoutManager = new CardLayoutManager();
            
            // Módulos que necesitan DOM completo
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', resolve);
            } else {
                resolve();
            }
        });
    }
    
    initializeSecondaryModules() {
        // Módulos que pueden cargarse cuando el navegador esté libre
        window.scrapingManager = new ScrapingManager();
        window.scrapingManager.init();
        
        // Funcionalidades adicionales
        setupPagination();
        setupPerPageSelector();
        setupLiveSearch();
        setupMobileNavigation();
        setupKeyboardNavigation();
        initScrollAnimations();
        
        // Configurar utilidades globales
        this.setupGlobalUtilities();
    }
    
    setupGlobalUtilities() {
        // Exponer utilidades globalmente
        window.appState = appState;
        window.notificationSystem = notificationSystem;
        
        // Info de debug (solo desarrollo)
        if (window.location.hostname === 'localhost') {
            this.setupDebugInfo();
        }
    }
    
    setupDebugInfo() {
        const urlParams = new URLSearchParams(window.location.search);
        const hasFilters = urlParams.has('fecha') || urlParams.has('con_imagen') || urlParams.has('q');
        
        if (hasFilters) {
            console.log('🔍 Filtros activos:', Object.fromEntries(urlParams));
        }
        
        console.log('📊 Módulos cargados:', Array.from(this.modules.keys()));
    }
    
    showFallbackUI() {
        // UI de fallback para cuando hay errores críticos
        const fallbackStyle = `
            .news-card { opacity: 1 !important; }
            .loading { animation: none !important; }
        `;
        
        const style = document.createElement('style');
        style.textContent = fallbackStyle;
        document.head.appendChild(style);
    }
    
    destroy() {
        // Cleanup para SPA o recargas
        this.modules.forEach(module => {
            if (module.destroy) module.destroy();
        });
        this.modules.clear();
        this.isInitialized = false;
    }
}

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', () => {
    window.newsPortalApp = new NewsPortalApp();
    window.newsPortalApp.initialize();
});

// ===== UTILIDADES GLOBALES MEJORADAS =====
window.truncateText = function(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text || '';
    
    // Mantener palabras completas
    const truncated = text.slice(0, maxLength);
    return truncated.slice(0, truncated.lastIndexOf(' ')) + '...';
};

window.formatDate = function(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    const diffHours = Math.ceil(diffTime / (1000 * 60 * 60));
    const diffMinutes = Math.ceil(diffTime / (1000 * 60));
    
    if (diffMinutes < 60) {
        return `Hace ${diffMinutes} min`;
    } else if (diffHours < 24) {
        return `Hace ${diffHours} h`;
    } else if (diffDays === 1) {
        return 'Ayer';
    } else if (diffDays < 7) {
        return `Hace ${diffDays} días`;
    }
    
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
};

window.smoothScrollTo = function(element) {
    if (!element) return;
    
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
};

window.debounce = function(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
};

console.log('📰 Sistema de noticias mejorado cargado completamente');