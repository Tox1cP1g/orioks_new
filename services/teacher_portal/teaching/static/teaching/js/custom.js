/**
 * Основные функции для портала преподавателя
 */

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех компонентов
    initSidebar();
    initNotifications();
    initDataTables();
    initTooltips();
    initPopovers();
    initTabs();
    initGradeUI();
});

/**
 * Инициализация бокового меню
 */
function initSidebar() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const menuToggle = document.querySelector('.menu-toggle');
    
    // Обработчик для сворачивания/разворачивания сайдбара на десктопе
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        });
    }
    
    // Обработчик для показа/скрытия сайдбара на мобильных устройствах
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('visible');
        });
    }
    
    // Закрытие сайдбара при клике вне его на мобильных устройствах
    document.addEventListener('click', function(event) {
        const isClickInsideSidebar = sidebar.contains(event.target);
        const isClickInsideMenuToggle = menuToggle && menuToggle.contains(event.target);
        
        if (!isClickInsideSidebar && !isClickInsideMenuToggle && window.innerWidth < 992 && sidebar.classList.contains('visible')) {
            sidebar.classList.remove('visible');
        }
    });
}

/**
 * Инициализация уведомлений
 */
function initNotifications() {
    const notificationsToggle = document.querySelector('.notifications-toggle');
    const notificationsMenu = document.querySelector('.notifications-menu');
    
    if (notificationsToggle && notificationsMenu) {
        notificationsToggle.addEventListener('click', function(event) {
            event.stopPropagation();
            notificationsMenu.classList.toggle('show');
            
            // Обновление статуса уведомлений при открытии
            if (notificationsMenu.classList.contains('show')) {
                updateNotificationStatus();
            }
        });
        
        // Закрытие меню уведомлений при клике вне его
        document.addEventListener('click', function(event) {
            const isClickInsideNotifications = notificationsMenu.contains(event.target) || notificationsToggle.contains(event.target);
            
            if (!isClickInsideNotifications && notificationsMenu.classList.contains('show')) {
                notificationsMenu.classList.remove('show');
            }
        });
    }
}

/**
 * Обновление статуса уведомлений
 * Отправляет AJAX-запрос для пометки уведомлений как прочитанных
 */
function updateNotificationStatus() {
    // В реальном приложении здесь должен быть AJAX-запрос
    console.log('Обновление статуса уведомлений...');
    
    const unreadItems = document.querySelectorAll('.notification-item.unread');
    unreadItems.forEach(item => {
        item.classList.remove('unread');
    });
    
    // Обновление счетчика
    const badge = document.querySelector('.notifications-badge');
    if (badge) {
        badge.textContent = '0';
        badge.style.display = 'none';
    }
}

/**
 * Инициализация DataTables
 */
function initDataTables() {
    if ($.fn.DataTable) {
        $('.datatable').each(function() {
            const table = $(this);
            const options = {
                language: {
                    url: '/static/teaching/js/libs/dataTables.russian.json'
                },
                responsive: true,
                pageLength: 25,
                lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Все"]],
                dom: 'Bfrtip',
                buttons: [
                    {
                        extend: 'excel',
                        text: '<i class="fas fa-file-excel"></i> Excel',
                        className: 'btn btn-sm btn-success',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                    {
                        extend: 'pdf',
                        text: '<i class="fas fa-file-pdf"></i> PDF',
                        className: 'btn btn-sm btn-danger',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                    {
                        extend: 'print',
                        text: '<i class="fas fa-print"></i> Печать',
                        className: 'btn btn-sm btn-info',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                    {
                        extend: 'colvis',
                        text: '<i class="fas fa-columns"></i> Колонки',
                        className: 'btn btn-sm btn-secondary'
                    }
                ]
            };
            
            // Проверяем наличие атрибута data-export
            if (table.attr('data-export') === 'false') {
                options.dom = 'frtip';
                delete options.buttons;
            }
            
            // Проверяем наличие атрибута data-ordering
            if (table.attr('data-ordering') === 'false') {
                options.ordering = false;
            }
            
            // Проверяем наличие атрибута data-paging
            if (table.attr('data-paging') === 'false') {
                options.paging = false;
            }
            
            // Инициализация DataTable
            table.DataTable(options);
        });
    }
}

/**
 * Инициализация всплывающих подсказок
 */
function initTooltips() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    } else if ($.fn.tooltip) {
        $('[data-toggle="tooltip"]').tooltip();
    }
}

/**
 * Инициализация всплывающих окон
 */
function initPopovers() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    } else if ($.fn.popover) {
        $('[data-toggle="popover"]').popover();
    }
}

/**
 * Инициализация вкладок
 */
function initTabs() {
    const tabLinks = document.querySelectorAll('.nav-tabs .nav-link');
    const tabContents = document.querySelectorAll('.tab-content .tab-pane');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Удаление активного класса со всех ссылок и контентов
            tabLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Добавление активного класса к выбранной ссылке
            this.classList.add('active');
            
            // Получение ID таба и активация соответствующего контента
            const tabId = this.getAttribute('data-target') || this.getAttribute('href');
            const tabContent = document.querySelector(tabId);
            if (tabContent) {
                tabContent.classList.add('active');
            }
            
            // Сохранение выбранной вкладки в localStorage
            const tabGroup = this.closest('.nav-tabs').getAttribute('id');
            if (tabGroup) {
                localStorage.setItem(`activeTab_${tabGroup}`, tabId);
            }
        });
    });
    
    // Восстановление выбранных вкладок из localStorage
    const tabGroups = document.querySelectorAll('.nav-tabs[id]');
    tabGroups.forEach(group => {
        const groupId = group.getAttribute('id');
        const activeTabId = localStorage.getItem(`activeTab_${groupId}`);
        
        if (activeTabId) {
            const tabLink = group.querySelector(`[data-target="${activeTabId}"], [href="${activeTabId}"]`);
            if (tabLink) {
                tabLink.click();
            }
        } else {
            // Если нет сохраненной вкладки, активируем первую
            const firstTabLink = group.querySelector('.nav-link');
            if (firstTabLink) {
                firstTabLink.click();
            }
        }
    });
}

/**
 * Инициализация интерфейса для работы с оценками
 */
function initGradeUI() {
    // Показ/скрытие всплывающих окон для ввода комментариев к оценкам
    const gradeInputs = document.querySelectorAll('.grade-input');
    
    gradeInputs.forEach(input => {
        input.addEventListener('focus', function() {
            const gradeCell = this.closest('.grade-cell');
            const popover = gradeCell.querySelector('.grade-popover');
            
            if (popover) {
                popover.classList.add('show');
            }
        });
        
        input.addEventListener('blur', function() {
            const gradeCell = this.closest('.grade-cell');
            const popover = gradeCell.querySelector('.grade-popover');
            
            if (popover) {
                // Добавляем небольшую задержку, чтобы можно было кликнуть на элементы в popover
                setTimeout(() => {
                    if (!popover.matches(':hover')) {
                        popover.classList.remove('show');
                    }
                }, 100);
            }
        });
    });
    
    // Сохранение оценок при изменении
    gradeInputs.forEach(input => {
        input.addEventListener('change', function() {
            saveGrade(this);
        });
        
        // Добавление обработчика для кнопки сохранения в popover, если она есть
        const gradeCell = input.closest('.grade-cell');
        const saveButton = gradeCell.querySelector('.save-grade-btn');
        
        if (saveButton) {
            saveButton.addEventListener('click', function() {
                const input = this.closest('.grade-cell').querySelector('.grade-input');
                saveGrade(input);
            });
        }
    });
}

/**
 * Сохранение оценки
 * @param {HTMLElement} inputElement Элемент ввода оценки
 */
function saveGrade(inputElement) {
    const studentId = inputElement.getAttribute('data-student-id');
    const taskId = inputElement.getAttribute('data-task-id');
    const gradeValue = inputElement.value;
    const commentElement = inputElement.closest('.grade-cell').querySelector('.grade-comment');
    const comment = commentElement ? commentElement.value : '';
    
    // В реальном приложении здесь должен быть AJAX-запрос
    console.log(`Сохранение оценки: студент=${studentId}, задание=${taskId}, оценка=${gradeValue}, комментарий=${comment}`);
    
    // Индикация успешного сохранения
    const gradeCell = inputElement.closest('.grade-cell');
    gradeCell.classList.add('saved');
    
    setTimeout(() => {
        gradeCell.classList.remove('saved');
    }, 2000);
}

/**
 * Форматирование даты в локальный формат
 * @param {string} dateString Строка с датой
 * @returns {string} Отформатированная дата
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

/**
 * Форматирование даты и времени в локальный формат
 * @param {string} dateString Строка с датой и временем
 * @returns {string} Отформатированная дата и время
 */
function formatDateTime(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Ajax-запрос с использованием Fetch API
 * @param {string} url URL запроса
 * @param {Object} options Опции запроса
 * @returns {Promise} Промис с результатом запроса
 */
function fetchData(url, options = {}) {
    // Добавление CSRF токена для POST, PUT, DELETE запросов
    if (options.method && options.method !== 'GET') {
        if (!options.headers) {
            options.headers = {};
        }
        
        options.headers['X-CSRFToken'] = getCsrfToken();
    }
    
    return fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                return response.text();
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            throw error;
        });
}

/**
 * Получение CSRF токена из cookie
 * @returns {string} CSRF токен
 */
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    return cookieValue;
}

/**
 * Показ уведомления пользователю
 * @param {string} message Сообщение
 * @param {string} type Тип уведомления (success, info, warning, danger)
 * @param {number} duration Длительность показа в миллисекундах
 */
function showNotification(message, type = 'info', duration = 3000) {
    // Проверяем, существует ли контейнер для уведомлений
    let notificationsContainer = document.getElementById('notifications-container');
    
    if (!notificationsContainer) {
        // Создаем контейнер, если его нет
        notificationsContainer = document.createElement('div');
        notificationsContainer.id = 'notifications-container';
        notificationsContainer.style.position = 'fixed';
        notificationsContainer.style.top = '20px';
        notificationsContainer.style.right = '20px';
        notificationsContainer.style.zIndex = '9999';
        document.body.appendChild(notificationsContainer);
    }
    
    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} fade-in`;
    notification.style.marginBottom = '10px';
    notification.style.minWidth = '250px';
    notification.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
    notification.innerHTML = message;
    
    // Добавляем кнопку закрытия
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'close';
    closeButton.style.marginLeft = '10px';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', function() {
        notificationsContainer.removeChild(notification);
    });
    
    notification.appendChild(closeButton);
    
    // Добавляем уведомление в контейнер
    notificationsContainer.appendChild(notification);
    
    // Удаляем уведомление через указанное время
    setTimeout(() => {
        if (notification.parentNode === notificationsContainer) {
            notification.classList.remove('fade-in');
            notification.classList.add('fade-out');
            
            // Добавляем стиль для анимации исчезновения
            const style = document.createElement('style');
            style.textContent = `
                .fade-out {
                    animation: fadeOut 0.5s forwards;
                }
                @keyframes fadeOut {
                    from { opacity: 1; }
                    to { opacity: 0; }
                }
            `;
            document.head.appendChild(style);
            
            // Удаляем уведомление после завершения анимации
            setTimeout(() => {
                if (notification.parentNode === notificationsContainer) {
                    notificationsContainer.removeChild(notification);
                }
            }, 500);
        }
    }, duration);
} 