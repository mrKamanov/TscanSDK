document.addEventListener('DOMContentLoaded', () => {
    // Инициализация соединения WebSocket
    const socket = io();

    // Получение элементов интерфейса
    const settingsGearButton = document.getElementById('settings-gear');
    const rightSidebar = document.getElementById('right-sidebar');
    const closeButton = document.getElementById('close-settings');

    // Слайдеры для настройки параметров камеры
    const sliders = {
        brightness: document.getElementById('brightness'),
        contrast: document.getElementById('contrast'),
        saturation: document.getElementById('saturation'),
        sharpness: document.getElementById('sharpness')
    };

    // Элементы отображения значений
    const valueDisplays = {
        brightness: document.getElementById('brightness-value'),
        contrast: document.getElementById('contrast-value'),
        saturation: document.getElementById('saturation-value'),
        sharpness: document.getElementById('sharpness-value')
    };

    // Функция для обновления отображаемого значения
    const updateValueDisplay = (sliderId, value) => {
        const display = valueDisplays[sliderId];
        if (display) {
            // Преобразуем value в число и форматируем его
            const numValue = Number(value);
            display.textContent = sliderId === 'sharpness' ? 
                numValue.toFixed(1) : 
                Math.round(numValue);
        }
    };

    // Открываем правое меню при нажатии на кнопку шестеренки
    settingsGearButton?.addEventListener('click', () => {
        rightSidebar.classList.add('open');
        // Добавляем анимацию для каждой группы настроек
        document.querySelectorAll('.input-group').forEach((group, index) => {
            group.style.setProperty('--index', index);
        });
    });

    // Закрываем правое меню при нажатии на кнопку "X"
    closeButton?.addEventListener('click', () => {
        rightSidebar.classList.remove('open');
    });

    // Закрываем меню при клике вне его области
    document.addEventListener('click', (e) => {
        if (!rightSidebar.contains(e.target) && 
            !settingsGearButton.contains(e.target) && 
            rightSidebar.classList.contains('open')) {
            rightSidebar.classList.remove('open');
        }
    });

    // Обработка изменения значений ползунков
    Object.entries(sliders).forEach(([sliderId, slider]) => {
        if (slider) {
            slider.addEventListener('input', () => {
                updateValueDisplay(sliderId, slider.value);
                
                // Формируем объект с текущими значениями параметров
                const settings = {
                    brightness: parseInt(sliders.brightness.value),
                    contrast: parseInt(sliders.contrast.value) / 100,
                    saturation: parseInt(sliders.saturation.value) / 100,
                    sharpness: parseFloat(sliders.sharpness.value)
                };

                // Отправляем параметры на сервер
                socket.emit('update_camera_settings', settings);
            });

            // Инициализация начальных значений
            updateValueDisplay(sliderId, slider.value);
        }
    });

    // Добавляем красивый эффект при наведении на группы настроек
    document.querySelectorAll('.input-group').forEach(group => {
        group.addEventListener('mouseenter', () => {
            group.style.transform = 'translateY(-2px)';
        });
        
        group.addEventListener('mouseleave', () => {
            group.style.transform = 'translateY(0)';
        });
    });
});