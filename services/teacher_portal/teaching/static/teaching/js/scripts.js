// Основные скрипты для портала преподавателя

document.addEventListener('DOMContentLoaded', function() {
    // Настройка сворачивания боковой панели
    const menuToggleBtn = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (menuToggleBtn) {
        menuToggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            mainContent.classList.toggle('expanded');
        });
    }
    
    // Активация текущего пункта меню
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/') {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
    
    // Настройка всплывающих подсказок
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Настройка уведомлений и выпадающих меню
    const dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
    
    // Обработка формы поиска
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(event) {
            const searchInput = this.querySelector('input[type="search"]');
            if (!searchInput.value.trim()) {
                event.preventDefault();
                searchInput.focus();
            }
        });
    }
    
    // Модальные окна подтверждения
    const confirmActionBtns = document.querySelectorAll('[data-confirm]');
    confirmActionBtns.forEach(btn => {
        btn.addEventListener('click', function(event) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
    
    // Добавление анимации к элементам при прокрутке
    const animateElements = document.querySelectorAll('.animate-on-scroll');
    
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('slide-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    animateElements.forEach(el => {
        observer.observe(el);
    });
    
    // Уведомления с автоматическим скрытием
    const alerts = document.querySelectorAll('.alert-dismissible');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });
    
    // Обработка вкладок и связанного контента
    const tabLinks = document.querySelectorAll('[data-bs-toggle="tab"]');
    
    tabLinks.forEach(tabLink => {
        tabLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Удаляем активный класс со всех вкладок
            tabLinks.forEach(link => link.classList.remove('active'));
            
            // Добавляем активный класс текущей вкладке
            this.classList.add('active');
            
            // Показываем соответствующий контент
            const target = document.querySelector(this.getAttribute('href'));
            const tabContents = document.querySelectorAll('.tab-pane');
            
            tabContents.forEach(content => content.classList.remove('active'));
            
            if (target) {
                target.classList.add('active');
            }
        });
    });

    // Добавление обработчика для кнопок выставления оценок
    const gradeButtons = document.querySelectorAll('.grade-btn');
    if (gradeButtons.length) {
        gradeButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const studentId = this.getAttribute('data-student-id');
                const assignmentId = this.getAttribute('data-assignment-id');
                const currentGrade = this.getAttribute('data-current-grade');
                
                const gradeValue = prompt('Введите оценку', currentGrade || '');
                
                if (gradeValue !== null && gradeValue.trim() !== '') {
                    // Здесь можно добавить AJAX-запрос для сохранения оценки
                    // Например:
                    /*
                    fetch('/api/grades/update', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        },
                        body: JSON.stringify({
                            student_id: studentId,
                            assignment_id: assignmentId,
                            grade: gradeValue
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            this.innerHTML = gradeValue;
                            this.setAttribute('data-current-grade', gradeValue);
                        } else {
                            alert('Ошибка при сохранении оценки');
                        }
                    });
                    */
                    
                    // Временное решение для демонстрации
                    this.innerHTML = gradeValue;
                    this.setAttribute('data-current-grade', gradeValue);
                }
            });
        });
    }

    // Обработка загрузки материалов
    const uploadForm = document.getElementById('upload-material-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const fileInput = this.querySelector('input[type="file"]');
            const titleInput = this.querySelector('input[name="title"]');
            
            if (!fileInput.files.length || !titleInput.value.trim()) {
                e.preventDefault();
                alert('Пожалуйста, выберите файл и введите название материала');
            }
        });
    }
}); 