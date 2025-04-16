/**
 * Основной JavaScript-файл для портала преподавателя
 */

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех компонентов
    initSidebar();
    initDropdowns();
    initTooltips();
    initTabsNavigation();
    initGradeInputs();
    initNotifications();
    initScrollAnimations();
    initDataTables();
});

/**
 * Управление боковой панелью
 */
function initSidebar() {
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const wrapper = document.querySelector('.wrapper');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            sidebar.classList.toggle('show');
        });
        
        // Закрытие сайдбара при клике вне его на мобильных устройствах
        document.addEventListener('click', function(e) {
            if (window.innerWidth < 992 && 
                !e.target.closest('.sidebar') && 
                !e.target.closest('.menu-toggle') && 
                sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
            }
        });
        
        // Адаптивное поведение при изменении размера окна
        window.addEventListener('resize', function() {
            if (window.innerWidth >= 992) {
                sidebar.classList.remove('show');
            }
        });
    }
}

/**
 * Инициализация выпадающих меню
 */
function initDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const dropdownMenu = this.nextElementSibling;
            
            // Закрыть все другие открытые выпадающие меню
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                if (menu !== dropdownMenu) {
                    menu.classList.remove('show');
                }
            });
            
            dropdownMenu.classList.toggle('show');
        });
    });
    
    // Закрытие выпадающих меню при клике вне их
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
            });
        }
    });
}

/**
 * Инициализация всплывающих подсказок
 */
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (typeof bootstrap !== 'undefined') {
        tooltipTriggerList.forEach(function(tooltipTriggerEl) {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Навигация по вкладкам
 */
function initTabsNavigation() {
    const tabLinks = document.querySelectorAll('.nav-tabs .nav-link');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Удаляем класс active у всех вкладок
            tabLinks.forEach(tab => tab.classList.remove('active'));
            
            // Добавляем класс active текущей вкладке
            this.classList.add('active');
            
            // Показываем соответствующий контент
            const targetId = this.getAttribute('href');
            const tabContents = document.querySelectorAll('.tab-pane');
            
            tabContents.forEach(content => {
                content.classList.remove('active', 'show');
                if ('#' + content.id === targetId) {
                    content.classList.add('active', 'show');
                }
            });
        });
    });
}

/**
 * Обработка ввода оценок
 */
function initGradeInputs() {
    const gradeDisplays = document.querySelectorAll('.grade-display');
    
    gradeDisplays.forEach(display => {
        display.addEventListener('click', function() {
            const container = this.closest('.grade-input-container');
            const form = container.querySelector('.grade-form');
            
            // Закрыть другие открытые формы оценок
            document.querySelectorAll('.grade-form.show').forEach(openForm => {
                if (openForm !== form) {
                    openForm.classList.remove('show');
                }
            });
            
            form.classList.toggle('show');
        });
    });
    
    // Обработка формы ввода оценок
    const gradeForms = document.querySelectorAll('.grade-form');
    gradeForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const container = this.closest('.grade-input-container');
            const display = container.querySelector('.grade-display');
            const input = this.querySelector('input[name="grade"]');
            
            if (input && display) {
                display.textContent = input.value;
                this.classList.remove('show');
                
                // Здесь можно добавить AJAX-запрос для сохранения оценки
                saveGrade(input.value, input.dataset.studentId, input.dataset.assignmentId);
            }
        });
    });
    
    // Закрытие форм ввода оценок при клике вне их
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.grade-input-container')) {
            document.querySelectorAll('.grade-form.show').forEach(form => {
                form.classList.remove('show');
            });
        }
    });
}

/**
 * Отправка AJAX-запроса для сохранения оценки
 */
function saveGrade(grade, studentId, assignmentId) {
    // Пример AJAX-запроса для сохранения оценки
    fetch('/api/grades/save/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            grade: grade,
            student_id: studentId,
            assignment_id: assignmentId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Оценка успешно сохранена', 'success');
        } else {
            showNotification('Ошибка при сохранении оценки', 'error');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Произошла ошибка при сохранении', 'error');
    });
}

/**
 * Получение CSRF-токена из cookie
 */
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    
    return cookieValue || '';
}

/**
 * Обработка уведомлений
 */
function initNotifications() {
    // Пример получения уведомлений через AJAX
    const notificationsBadge = document.querySelector('.notifications-badge');
    const notificationsDropdown = document.querySelector('.notifications-dropdown');
    
    if (notificationsBadge && notificationsDropdown) {
        // Получение данных о непрочитанных уведомлениях
        fetch('/api/notifications/unread/')
            .then(response => response.json())
            .then(data => {
                if (data.count > 0) {
                    notificationsBadge.textContent = data.count > 99 ? '99+' : data.count;
                    notificationsBadge.classList.remove('d-none');
                    
                    // Заполнение выпадающего меню уведомлениями
                    const notificationsList = notificationsDropdown.querySelector('.notifications-list');
                    if (notificationsList && data.notifications) {
                        notificationsList.innerHTML = '';
                        
                        data.notifications.forEach(notification => {
                            const item = document.createElement('a');
                            item.href = notification.url || '#';
                            item.className = 'dropdown-item d-flex align-items-center';
                            item.dataset.id = notification.id;
                            
                            item.innerHTML = `
                                <div class="me-3">
                                    <i class="fas fa-${notification.icon || 'bell'} text-${notification.type || 'primary'}"></i>
                                </div>
                                <div>
                                    <div class="small text-muted">${notification.time}</div>
                                    <div class="${notification.read ? '' : 'fw-bold'}">${notification.message}</div>
                                </div>
                            `;
                            
                            notificationsList.appendChild(item);
                            
                            // Обработчик клика по уведомлению
                            item.addEventListener('click', function() {
                                markNotificationAsRead(notification.id);
                            });
                        });
                    }
                }
            })
            .catch(error => console.error('Ошибка загрузки уведомлений:', error));
    }
}

/**
 * Отметка уведомления как прочитанного
 */
function markNotificationAsRead(notificationId) {
    fetch(`/api/notifications/mark-as-read/${notificationId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const notificationItem = document.querySelector(`.dropdown-item[data-id="${notificationId}"]`);
            if (notificationItem) {
                notificationItem.querySelector('div:last-child div:last-child').classList.remove('fw-bold');
            }
            
            // Обновление счетчика непрочитанных уведомлений
            const badge = document.querySelector('.notifications-badge');
            if (badge) {
                const currentCount = parseInt(badge.textContent);
                if (currentCount > 1) {
                    badge.textContent = currentCount - 1;
                } else {
                    badge.classList.add('d-none');
                }
            }
        }
    })
    .catch(error => console.error('Ошибка при отметке уведомления:', error));
}

/**
 * Показ уведомления
 */
function showNotification(message, type = 'info') {
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
            container.appendChild(toast);
        } else {
            toastContainer.appendChild(toast);
        }
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Удаление уведомления после скрытия
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    } else {
        // Fallback для случая, если Bootstrap недоступен
        alert(message);
    }
}

/**
 * Анимация при прокрутке
 */
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    if (animatedElements.length > 0) {
        const checkIfInView = function() {
            animatedElements.forEach(element => {
                const rect = element.getBoundingClientRect();
                const windowHeight = window.innerHeight || document.documentElement.clientHeight;
                
                if (rect.top <= windowHeight * 0.8 && rect.bottom >= 0) {
                    element.classList.add('visible');
                }
            });
        };
        
        // Первичная проверка
        checkIfInView();
        
        // Проверка при прокрутке
        window.addEventListener('scroll', checkIfInView);
    }
}

/**
 * Инициализация таблиц данных
 */
function initDataTables() {
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.datatable').DataTable({
            language: {
                url: '/static/teaching/js/libs/dataTables.russian.json'
            },
            responsive: true,
            pageLength: 10,
            lengthMenu: [[5, 10, 25, 50], [5, 10, 25, 50]]
        });
    }
}

/**
 * Обработка форм с AJAX
 */
function initAjaxForms() {
    const ajaxForms = document.querySelectorAll('form.ajax-form');
    
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('[type="submit"]');
            const originalText = submitBtn ? submitBtn.innerHTML : '';
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Загрузка...';
            }
            
            fetch(this.action, {
                method: this.method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message || 'Операция выполнена успешно', 'success');
                    
                    if (data.redirect) {
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 1000);
                    }
                    
                    if (data.reset) {
                        form.reset();
                    }
                } else {
                    showNotification(data.message || 'Произошла ошибка', 'danger');
                    
                    // Отображение ошибок валидации
                    if (data.errors) {
                        Object.keys(data.errors).forEach(key => {
                            const field = form.querySelector(`[name="${key}"]`);
                            const feedbackElement = field.nextElementSibling;
                            
                            field.classList.add('is-invalid');
                            
                            if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
                                feedbackElement.textContent = data.errors[key].join(' ');
                            } else {
                                const feedback = document.createElement('div');
                                feedback.className = 'invalid-feedback';
                                feedback.textContent = data.errors[key].join(' ');
                                field.parentNode.insertBefore(feedback, field.nextSibling);
                            }
                        });
                    }
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                showNotification('Произошла ошибка при отправке формы', 'danger');
            })
            .finally(() => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
            });
        });
    });
} 