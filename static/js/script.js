document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const videoElement = document.getElementById('video');
    const resultElement = document.getElementById('result');
    const toggleVideoButton = document.getElementById('toggle-video');
    const captureFrameButton = document.getElementById('capture-frame');
    const startCameraButton = document.getElementById('start-camera');
    const stopCameraButton = document.getElementById('stop-camera');
    const toggleSidebarButton = document.getElementById('toggle-sidebar');
    const sidebarContent = document.getElementById('sidebar-content');
    const questionsInput = document.getElementById('questions');
    const choicesInput = document.getElementById('choices');
    const applySettingsButton = document.getElementById('apply-settings');
    const updateAnswersButton = document.getElementById('update-answers');
    const toggleCheckboxesButton = document.getElementById('toggle-checkboxes');
    const checkboxGrid = document.getElementById('checkbox-grid');
    const mainContent = document.querySelector('.main-content');
    const sidebar = document.querySelector('.sidebar');
    const addToReportButton = document.getElementById('add-to-report');
    const toggleOverlayButton = document.getElementById('toggle-overlay');

    let videoVisible = true;
    let sidebarOpen = false;
    let checkboxesVisible = false;
    let isPaused = false;
    let overlayMode = false;

    // Обработчик клика для кнопки "Открыть/Закрыть меню"
    toggleSidebarButton.addEventListener('click', () => {
        sidebar.classList.toggle('open-sidebar');
        mainContent.classList.toggle('open-sidebar');
        updateCheckboxSize();
    });

    // Обработчик клика для кнопки "Скрыть видео"
    toggleVideoButton.addEventListener('click', () => {
        videoVisible = !videoVisible;
        videoElement.style.display = videoVisible ? 'block' : 'none';
        toggleVideoButton.textContent = videoVisible ? 'Скрыть видео' : 'Показать видео';
        updateCheckboxSize();
    });

    // Обработчик клика для кнопки "Показать/Скрыть сетку"
    toggleCheckboxesButton.addEventListener('click', () => {
        checkboxesVisible = !checkboxesVisible;
        checkboxGrid.style.display = checkboxesVisible ? 'grid' : 'none';
        // Обновляем иконку
        const icon = toggleCheckboxesButton.querySelector('i');
        icon.classList.toggle('fa-th');
        icon.classList.toggle('fa-th-large');
        // Обновляем title кнопки
        toggleCheckboxesButton.title = checkboxesVisible ? 'Скрыть сетку' : 'Показать сетку';
    });

    // Обработчик клика для кнопки "Создать стоп-кадр"
    captureFrameButton.addEventListener('click', () => {
        socket.emit('toggle_pause');
        isPaused = !isPaused;
        captureFrameButton.classList.toggle('paused');
        addToReportButton.disabled = !isPaused;
    });

    // Обработчик клавиши пробел для создания стоп-кадра
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && !e.repeat) {
            e.preventDefault(); // Предотвращаем прокрутку страницы
            socket.emit('toggle_pause');
            isPaused = !isPaused;
            captureFrameButton.classList.toggle('paused');
            addToReportButton.disabled = !isPaused;
        }
    });

    // Обработчик сочетания клавиш Alt + A для добавления в отчёт
    document.addEventListener('keydown', (e) => {
        if (e.code === 'KeyA' && e.altKey && !e.repeat) {
            e.preventDefault(); // Предотвращаем стандартное поведение
            if (!addToReportButton.disabled) {
                const result = localStorage.getItem('currentResult');
                if (result) {
                    socket.emit('add_to_report', { result });
                } else {
                    alert('Нет текущего результата для добавления в отчёт.');
                }
            }
        }
    });

    // Обработчик клика для кнопки "Включить камеру"
    startCameraButton.addEventListener('click', () => {
        socket.emit('start_camera');
        startCameraButton.disabled = true;
        stopCameraButton.disabled = false;
    });

    // Обработчик клика для кнопки "Выключить камеру"
    stopCameraButton.addEventListener('click', () => {
        socket.emit('stop_camera');
        startCameraButton.disabled = false;
        stopCameraButton.disabled = true;
        videoElement.src = '';
    });

    // Обработчик клика для кнопки "Применить настройки"
    applySettingsButton.addEventListener('click', () => {
        const questions = parseInt(questionsInput.value);
        const choices = parseInt(choicesInput.value);
        socket.emit('apply_settings', { questions, choices });
        createCheckboxes();
        updateCheckboxSize();
    });

    // Обработчик клика для кнопки "Обновить ответы"
    updateAnswersButton.addEventListener('click', () => {
        const answers = {};
        for (let i = 0; i < questionsInput.value; i++) {
            const selectedAnswer = document.querySelector(`input[name="question_${i}"]:checked`);
            if (selectedAnswer) {
                answers[`question_${i}`] = selectedAnswer.value;
            } else {
                alert(`Выберите ответ для вопроса ${i + 1}`);
                return;
            }
        }
        socket.emit('update_correct_answers', answers);
    });

    // Обработчик клика для кнопки "Добавить в отчет"
    addToReportButton.addEventListener('click', () => {
        const result = localStorage.getItem('currentResult');
        if (result) {
            socket.emit('add_to_report', { result });
        } else {
            alert('Нет текущего результата для добавления в отчёт.');
        }
    });

    // Обработчик клика для кнопки "Переключить режим отображения"
    toggleOverlayButton.addEventListener('click', () => {
        overlayMode = !overlayMode;
        socket.emit('toggle_overlay_mode', overlayMode);
        const icon = toggleOverlayButton.querySelector('i');
        icon.classList.toggle('fa-toggle-on');
        icon.classList.toggle('fa-toggle-off');
        toggleOverlayButton.title = overlayMode ? 'Режим наложения: ВКЛ' : 'Режим наложения: ВЫКЛ';
    });

    // Обработчик события "frame" от сервера
    socket.on('frame', (data) => {
        videoElement.src = `data:image/jpeg;base64,${data.image}`;
        resultElement.textContent = `Результат: ${data.result}`;
        localStorage.setItem('currentResult', data.result);
        updateCheckboxSize();
    });

    // Обработчик события "settings_applied" от сервера
    socket.on('settings_applied', (data) => {
        alert(data.message);
        createCheckboxes();
        updateCheckboxSize();
    });

    // Обработчик события "answers_updated" от сервера
    socket.on('answers_updated', (data) => {
        alert(data.message);
    });

    // Обработчик события "error" от сервера
    socket.on('error', (data) => {
        alert(data.message);
    });

    // Обработчик успешного добавления в отчёт
    socket.on('report_added', (response) => {
        console.log('Получен ответ от сервера:', response);
        if (response.success) {
            console.log('Создаю уведомление...');
            // Создаем элемент уведомления
            const notification = document.createElement('div');
            notification.className = 'notification success';
            notification.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <span>Результат успешно добавлен в отчёт</span>
            `;
            
            // Добавляем уведомление на страницу
            document.body.appendChild(notification);
            console.log('Уведомление добавлено на страницу');
            
            // Удаляем уведомление через 3 секунды
            setTimeout(() => {
                console.log('Начинаю анимацию исчезновения...');
                notification.classList.add('fade-out');
                setTimeout(() => {
                    console.log('Удаляю уведомление...');
                    notification.remove();
                }, 500);
            }, 3000);
        } else {
            console.error('Ошибка при добавлении в отчёт:', response.message);
            alert('Ошибка при добавлении в отчёт: ' + response.message);
        }
    });

    // Обработчик статуса камеры
    socket.on('camera_status', (data) => {
        if (data.status === 'error') {
            alert(data.message);
        }
    });

    // Функция для создания чекбоксов
    function createCheckboxes() {
        checkboxGrid.innerHTML = '';
        const questions = parseInt(questionsInput.value);
        const choices = parseInt(choicesInput.value);
        const videoWidth = videoElement.offsetWidth;
        const videoHeight = videoElement.offsetHeight;
        const cellWidth = videoWidth / choices;
        const cellHeight = videoHeight / questions;

        for (let i = 0; i < questions; i++) {
            for (let j = 0; j < choices; j++) {
                const label = document.createElement('label');
                label.innerHTML = `
                    <input type="radio" name="question_${i}" value="${j}">
                    <span class="custom-checkbox">${i + 1}.${j + 1}</span>
                `;
                label.style.position = 'absolute';
                label.style.left = `${j * cellWidth}px`;
                label.style.top = `${i * cellHeight}px`;
                label.style.width = `${cellWidth}px`;
                label.style.height = `${cellHeight}px`;
                label.style.display = 'flex';
                label.style.alignItems = 'center';
                label.style.justifyContent = 'center';
                label.style.pointerEvents = 'auto';
                label.style.fontSize = '14px';
                checkboxGrid.appendChild(label);
            }
        }
    }

    // Функция для обновления размера чекбоксов
    function updateCheckboxSize() {
        const questions = parseInt(questionsInput.value);
        const choices = parseInt(choicesInput.value);
        const videoWidth = videoElement.offsetWidth;
        const videoHeight = videoElement.offsetHeight;
        const cellWidth = videoWidth / choices;
        const cellHeight = videoHeight / questions;

        const labels = checkboxGrid.querySelectorAll('label');
        labels.forEach((label, index) => {
            const row = Math.floor(index / choices);
            const col = index % choices;
            label.style.width = `${cellWidth}px`;
            label.style.height = `${cellHeight}px`;
            label.style.left = `${col * cellWidth}px`;
            label.style.top = `${row * cellHeight}px`;
            label.style.display = 'flex';
            label.style.alignItems = 'center';
            label.style.justifyContent = 'center';
        });

        const customCheckboxes = checkboxGrid.querySelectorAll('.custom-checkbox');
        customCheckboxes.forEach(customCheckbox => {
            customCheckbox.style.width = `${cellWidth}px`;
            customCheckbox.style.height = `${cellHeight}px`;
        });
    }

    createCheckboxes();
    updateCheckboxSize();

    window.addEventListener('resize', () => {
        updateCheckboxSize();
    });
});