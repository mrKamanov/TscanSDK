document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');
    const socket = io();
    const toggleSidebarButton = document.getElementById('toggle-sidebar');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const reportList = document.getElementById('report-list');
    const resetReportsButton = document.getElementById('reset-reports');
    const grade5Input = document.getElementById('grade_5');
    const grade4Input = document.getElementById('grade_4');
    const grade3Input = document.getElementById('grade_3');
    const grade2Input = document.getElementById('grade_2');
    const applyGradingButton = document.getElementById('apply-grading');
    const scanButton = document.querySelector('.sidebar-content .navigation-group .scan-button');
    const captureFrameButton = document.getElementById('capture-frame');
    const addToReportButton = document.getElementById('add-to-report');
    const downloadXlsxButton = document.getElementById('download-xlsx'); // Кнопка для скачивания XLSX

    // Глобальный массив для хранения данных о работах
    let reportsData = [];
    let gradingCriteria = {
        5: [90, 100],
        4: [70, 89],
        3: [50, 69],
        2: [0, 49]
    };

    // Проверяем наличие элементов canvas
    const gradeChartElement = document.getElementById('gradeChart');
    const percentageChartElement = document.getElementById('percentageChart');
    const correctChartElement = document.getElementById('correctAnswersChart');
    const incorrectChartElement = document.getElementById('incorrectAnswersChart');

    console.log('Canvas elements:', {
        gradeChart: gradeChartElement,
        percentageChart: percentageChartElement,
        correctChart: correctChartElement,
        incorrectChart: incorrectChartElement
    });

    if (!gradeChartElement || !percentageChartElement || !correctChartElement || !incorrectChartElement) {
        console.error('Some chart elements are missing!');
        return;
    }

    // Создаем контексты для диаграмм
    const gradeCtx = gradeChartElement.getContext('2d');
    const percentageCtx = percentageChartElement.getContext('2d');
    const correctCtx = correctChartElement.getContext('2d');
    const incorrectCtx = incorrectChartElement.getContext('2d');

    console.log('Creating charts...');

    // Инициализация диаграмм
    const gradeChart = new Chart(gradeCtx, {
        type: 'pie',
        data: {
            labels: ['Отлично (5)', 'Хорошо (4)', 'Удовлетворительно (3)', 'Неудовлетворительно (2)'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: ['#A3BE8C', '#EBCB8B', '#D08770', '#BF616A']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#ECEFF4'
                    }
                },
                title: {
                    display: true,
                    text: 'Распределение оценок',
                    color: '#ECEFF4',
                    font: {
                        size: 16
                    }
                }
            }
        }
    });

    const percentageChart = new Chart(percentageCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Процент выполнения',
                data: [],
                backgroundColor: '#88C0D0'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(236, 239, 244, 0.1)'
                    },
                    ticks: {
                        color: '#ECEFF4'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(236, 239, 244, 0.1)'
                    },
                    ticks: {
                        color: '#ECEFF4'
                    }
                }
            }
        }
    });

    const correctChart = new Chart(correctCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Правильные ответы',
                data: [],
                backgroundColor: '#A3BE8C'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: questions,
                    grid: {
                        color: 'rgba(236, 239, 244, 0.1)'
                    },
                    ticks: {
                        color: '#ECEFF4'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(236, 239, 244, 0.1)'
                    },
                    ticks: {
                        color: '#ECEFF4'
                    }
                }
            }
        }
    });

    const incorrectChart = new Chart(incorrectCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Неправильные ответы',
                data: [],
                backgroundColor: '#BF616A'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: questions,
                    grid: {
                        color: 'rgba(236, 239, 244, 0.1)'
                    },
                    ticks: {
                        color: '#ECEFF4'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(236, 239, 244, 0.1)'
                    },
                    ticks: {
                        color: '#ECEFF4'
                    }
                }
            }
        }
    });

    // Функция для получения данных из HTML
    function parseDataFromHTML() {
        console.log('Parsing data from HTML...');
        const reportItems = document.querySelectorAll('.report-item');
        console.log('Found report items:', reportItems.length);
        
        return Array.from(reportItems).map(item => {
            const workNumber = parseInt(item.id.replace('report-', ''));
            const correctAnswers = parseInt(item.querySelector(`#correct-answers-${workNumber}`).textContent.split(':')[1].trim());
            const incorrectAnswers = parseInt(item.querySelector(`#incorrect-answers-${workNumber}`).textContent.split(':')[1].trim());
            const scorePercentage = parseFloat(item.querySelector(`#score-percentage-${workNumber}`).textContent.split(':')[1].replace('%', '').trim());
            
            // Исправляем извлечение оценки
            const gradeText = item.querySelector(`#grade-${workNumber}`).textContent;
            const grade = parseInt(gradeText.match(/\d+/)[0]);
            
            console.log(`Parsed data for work ${workNumber}:`, {
                correctAnswers,
                incorrectAnswers,
                scorePercentage,
                grade
            });
            
            // Получаем списки правильных и неправильных вопросов
            const correctQuestionsText = item.querySelector(`#correct-questions-${workNumber}`).textContent.split(':')[1].trim();
            const incorrectQuestionsText = item.querySelector(`#incorrect-questions-${workNumber}`).textContent.split(':')[1].trim();
            
            const correct_questions = correctQuestionsText ? correctQuestionsText.split(',').map(n => parseInt(n.trim())) : [];
            const incorrect_question_numbers = incorrectQuestionsText ? incorrectQuestionsText.split(',').map(n => parseInt(n.trim())) : [];
            
            return {
                work_number: workNumber,
                correct_answers_count: correctAnswers,
                incorrect_answers_count: incorrectAnswers,
                score_percentage: scorePercentage,
                grade: grade,
                correct_questions: correct_questions,
                incorrect_question_numbers: incorrect_question_numbers
            };
        });
    }

    // Функция для создания XLSX отчета
    function createXlsxReport(reportsData) {
        try {
            if (reportsData.length === 0) {
                alert("Нет данных для создания отчета!");
                return;
            }

            const wb = XLSX.utils.book_new();
            const wsData = [
                ['№', '+', '-', 'Верно', 'Неверно', '%', 'Оценка']
            ];

            // Добавляем данные из reportsData
            reportsData.forEach((report, index) => {
                wsData.push([
                    `Работа ${report.work_number}`,
                    report.correct_answers_count,
                    report.incorrect_answers_count,
                    report.correct_questions.join(', '),
                    report.incorrect_question_numbers.join(', '),
                    `${report.score_percentage}%`,
                    report.grade
                ]);
            });

            // Добавляем сводные данные
            const totalStudents = reportsData.length;
            const excellentCount = reportsData.filter(report => report.grade === 5).length;
            const goodCount = reportsData.filter(report => report.grade === 4).length;
            const satisfactoryCount = reportsData.filter(report => report.grade === 3).length;

            const successRate = ((excellentCount + goodCount + satisfactoryCount) / totalStudents * 100).toFixed(2) + '%';
            const knowledgeQuality = ((excellentCount + goodCount) / totalStudents * 100).toFixed(2) + '%';

            wsData.push(['', '', '', '', '', 'Успеваемость:', successRate]);
            wsData.push(['', '', '', '', '', 'Качество знаний:', knowledgeQuality]);

            // Создаем worksheet
            const ws = XLSX.utils.aoa_to_sheet(wsData);

            // Добавляем worksheet в workbook
            XLSX.utils.book_append_sheet(wb, ws, 'Отчеты');

            // Сохраняем файл
            XLSX.writeFile(wb, 'отчет.xlsx', { bookType: 'xlsx', type: 'binary' });
        } catch (error) {
            console.error("Ошибка при создании XLSX:", error);
            alert("Произошла ошибка при создании отчета. Проверьте консоль разработчика.");
        }
    }

    // Функция обновления диаграмм
    function updateCharts() {
        console.log('Updating charts...');
        const reportData = parseDataFromHTML();
        console.log('Report data:', reportData);

        // Обновление диаграммы оценок
        const gradeData = {
            5: 0,
            4: 0,
            3: 0,
            2: 0
        };

        // Подсчет количества каждой оценки
        reportData.forEach(report => {
            if (report.grade >= 2 && report.grade <= 5) {
                gradeData[report.grade]++;
            } else {
                console.warn(`Некорректная оценка: ${report.grade} для работы ${report.work_number}`);
            }
        });

        console.log('Grade data:', gradeData);

        // Обновляем данные круговой диаграммы
        gradeChart.data.datasets[0].data = [
            gradeData[5], // Отлично
            gradeData[4], // Хорошо
            gradeData[3], // Удовлетворительно
            gradeData[2]  // Неудовлетворительно
        ];
        gradeChart.update();

        // Обновление диаграммы процентов
        const labels = reportData.map(r => `Работа ${r.work_number}`);
        percentageChart.data.labels = labels;
        percentageChart.data.datasets[0].data = reportData.map(r => r.score_percentage);
        percentageChart.update();

        // Подсчет частоты правильных ответов для каждого вопроса
        const correctQuestionsFrequency = {};
        reportData.forEach(report => {
            const correctQuestions = report.correct_questions;
            correctQuestions.forEach(question => {
                correctQuestionsFrequency[question] = (correctQuestionsFrequency[question] || 0) + 1;
            });
        });

        // Подсчет частоты неправильных ответов для каждого вопроса
        const incorrectQuestionsFrequency = {};
        reportData.forEach(report => {
            const incorrectQuestions = report.incorrect_question_numbers;
            incorrectQuestions.forEach(question => {
                incorrectQuestionsFrequency[question] = (incorrectQuestionsFrequency[question] || 0) + 1;
            });
        });

        // Обновление диаграммы правильных ответов
        const correctQuestionLabels = Object.keys(correctQuestionsFrequency).sort((a, b) => a - b);
        correctChart.data.labels = correctQuestionLabels.map(q => `Вопрос ${q}`);
        correctChart.data.datasets[0].data = correctQuestionLabels.map(q => correctQuestionsFrequency[q]);
        correctChart.update();

        // Обновление диаграммы неправильных ответов
        const incorrectQuestionLabels = Object.keys(incorrectQuestionsFrequency).sort((a, b) => a - b);
        incorrectChart.data.labels = incorrectQuestionLabels.map(q => `Вопрос ${q}`);
        incorrectChart.data.datasets[0].data = incorrectQuestionLabels.map(q => incorrectQuestionsFrequency[q]);
        incorrectChart.update();

        console.log('Charts updated');
    }

    // Обработчики событий
    socket.on('report_added', (response) => {
        console.log('Report added:', response);
        if (response.success) {
            location.reload();
        }
    });

    socket.on('reset_reports', () => {
        console.log('Reports reset');
        reportList.innerHTML = '';
        updateCharts();
    });

    // Обработчик для кнопки скачивания XLSX
    if (downloadXlsxButton) {
        downloadXlsxButton.addEventListener('click', () => {
            console.log('Download XLSX button clicked');
            const reportData = parseDataFromHTML();
            createXlsxReport(reportData);
        });
    }

    // Обработчик клика для кнопки "Открыть/Закрыть меню"
    if (toggleSidebarButton) {
        toggleSidebarButton.addEventListener('click', () => {
            sidebar.classList.toggle('open-sidebar');
            mainContent.classList.toggle('open-sidebar');
        });
    }

    // Обработчик клика для кнопки "Сбросить отчёты"
    if (resetReportsButton) {
        resetReportsButton.addEventListener('click', () => {
            if (confirm('Вы уверены, что хотите сбросить все отчёты?')) {
                socket.emit('reset_reports');
            }
        });
    }

    // Функция для парсинга критериев оценок
    function parseGradingCriteria() {
        const grade5Range = grade5Input.value.split('-').map(Number);
        const grade4Range = grade4Input.value.split('-').map(Number);
        const grade3Range = grade3Input.value.split('-').map(Number);
        const grade2Range = grade2Input.value.split('-').map(Number);

        return {
            5: grade5Range,
            4: grade4Range,
            3: grade3Range,
            2: grade2Range
        };
    }

    // Функция для валидации критериев оценок
    function validateGradingCriteria(criteria) {
        const ranges = Object.values(criteria);
        for (let i = 0; i < ranges.length - 1; i++) {
            if (ranges[i][1] >= ranges[i + 1][0]) {
                return false;
            }
        }
        return true;
    }

    // Функция для загрузки сохраненных критериев из localStorage
    function loadGradingCriteria() {
        const savedCriteria = JSON.parse(localStorage.getItem('gradingCriteria'));
        if (savedCriteria) {
            gradingCriteria = savedCriteria;
            grade5Input.value = `${gradingCriteria[5][0]}-${gradingCriteria[5][1]}`;
            grade4Input.value = `${gradingCriteria[4][0]}-${gradingCriteria[4][1]}`;
            grade3Input.value = `${gradingCriteria[3][0]}-${gradingCriteria[3][1]}`;
            grade2Input.value = `${gradingCriteria[2][0]}-${gradingCriteria[2][1]}`;
            console.log('Загружены критерии оценок:', gradingCriteria);
        } else {
            console.warn('Критерии оценок не найдены в localStorage. Используются значения по умолчанию.');
        }
    }

    // Загружаем критерии при загрузке страницы
    loadGradingCriteria();

    // Обработчик клика для кнопки "Применить критерии"
    if (applyGradingButton) {
        applyGradingButton.addEventListener('click', () => {
            const newCriteria = parseGradingCriteria();

            if (!validateGradingCriteria(newCriteria)) {
                alert('Значения критериев не должны пересекаться.');
                return;
            }

            gradingCriteria = newCriteria;
            localStorage.setItem('gradingCriteria', JSON.stringify(gradingCriteria));
            console.log('Критерии оценок обновлены:', gradingCriteria);

            socket.emit('apply_grading_criteria', newCriteria);
        });
    }

    // Обработчик клика для кнопки "Сканирование"
    if (scanButton) {
        scanButton.addEventListener('click', () => {
            window.location.href = '/';
        });
    }

    // Обработчик клика для кнопки "Создать стоп-кадр"
    if (captureFrameButton) {
        captureFrameButton.addEventListener('click', () => {
            socket.emit('toggle_pause');
        });
    }

    // Обработчик клика для кнопки "Добавить в отчет"
    if (addToReportButton) {
        addToReportButton.addEventListener('click', () => {
            const result = localStorage.getItem('currentResult');
            if (result) {
                socket.emit('add_to_report', { result });
            } else {
                alert('Нет текущего результата для добавления в отчёт.');
            }
        });
    }

    // Инициализация при загрузке страницы
    console.log('Initializing charts...');
    updateCharts();
});