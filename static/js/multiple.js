document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    
    // Получаем все необходимые элементы DOM
    const elements = {
        uploadZone: document.getElementById('upload-zone'),
        fileInput: document.getElementById('file-input'),
        previewGrid: document.getElementById('preview-grid'),
        startProcessing: document.getElementById('start-processing'),
        resultsList: document.getElementById('results-list'),
        resetButton: document.getElementById('reset-all'),
        questionsInput: document.getElementById('questions'),
        choicesInput: document.getElementById('choices'),
        strictModeCheckbox: document.getElementById('strict-mode'),
        displayModeSelect: document.getElementById('display-mode'),
        correctAnswersGrid: document.getElementById('correct-answers-grid'),
        saveCriteriaButton: document.getElementById('save-criteria'),
        loadCriteriaButton: document.getElementById('load-criteria'),
        criteriaFileInput: document.getElementById('criteria-file-input')
    };

    // Проверяем наличие всех необходимых элементов
    for (const [key, element] of Object.entries(elements)) {
        if (!element) {
            console.error(`Element not found: ${key}`);
            return; // Прерываем выполнение если отсутствует важный элемент
        }
    }
    
    let uploadedFiles = [];
    let processingInProgress = false;
    let isTwoColumnsMode = elements.displayModeSelect.value === 'double';

    const modalOverlay = document.createElement('div');
    modalOverlay.className = 'modal-overlay';
    modalOverlay.innerHTML = `
        <div class="modal-content">
            <button class="modal-close"><i class="fas fa-times"></i></button>
            <img src="" alt="Enlarged Result">
        </div>
    `;
    document.body.appendChild(modalOverlay);

    const modalClose = modalOverlay.querySelector('.modal-close');
    const modalImage = modalOverlay.querySelector('img');

    modalClose.addEventListener('click', () => {
        modalOverlay.classList.remove('active');
    });

    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
            modalOverlay.classList.remove('active');
        }
    });

    function resetAll() {
        uploadedFiles = [];
        elements.previewGrid.innerHTML = '';
        elements.resultsList.innerHTML = '';
        elements.startProcessing.disabled = true;
        elements.fileInput.value = '';
        processingInProgress = false;
        createAnswersGrid();
    }

    elements.resetButton.addEventListener('click', resetAll);

    function createAnswersGrid() {
        const questions = parseInt(elements.questionsInput.value) || 5;
        const choices = parseInt(elements.choicesInput.value) || 5;
        const grid = elements.correctAnswersGrid;
        
        grid.innerHTML = '';
        grid.style.display = 'flex';
        grid.style.gap = '20px';
        grid.style.justifyContent = 'center';
        
        // Создаем контейнеры для столбцов
        const firstContainer = document.createElement('div');
        firstContainer.className = 'answers-column';
        grid.appendChild(firstContainer);
        
        let secondContainer = null;
        if (isTwoColumnsMode) {
            secondContainer = document.createElement('div');
            secondContainer.className = 'answers-column';
            grid.appendChild(secondContainer);
        }
        
        const half = Math.ceil(questions / 2);
        
        for (let i = 0; i < questions; i++) {
            const questionDiv = document.createElement('div');
            questionDiv.className = 'question-answers';
            
            const questionNumber = document.createElement('div');
            questionNumber.className = 'question-number';
            questionNumber.textContent = `Вопрос ${i + 1}`;
            questionDiv.appendChild(questionNumber);
            
            const answersRow = document.createElement('div');
            answersRow.className = 'answers-row';
            
            for (let j = 0; j < choices; j++) {
                const label = document.createElement('label');
                label.className = 'answer-option';
                label.innerHTML = `
                    <input type="checkbox" name="question_${i}" value="${j}">
                    <span class="answer-text">${j + 1}</span>
                `;
                answersRow.appendChild(label);
            }
            
            questionDiv.appendChild(answersRow);
            
            if (isTwoColumnsMode) {
                if (i < half) {
                    firstContainer.appendChild(questionDiv);
                } else {
                    secondContainer.appendChild(questionDiv);
                }
            } else {
                firstContainer.appendChild(questionDiv);
            }
        }
    }

    // Обработчики событий
    elements.displayModeSelect.addEventListener('change', function() {
        isTwoColumnsMode = this.value === 'double';
        createAnswersGrid();
    });

    elements.questionsInput.addEventListener('input', createAnswersGrid);
    elements.choicesInput.addEventListener('input', createAnswersGrid);

    // Создаем сетку при загрузке страницы
    createAnswersGrid();

    function handleFiles(files) {
        if (processingInProgress) return;

        const imageFiles = Array.from(files).filter(file => 
            file.type.startsWith('image/'));

        imageFiles.forEach(file => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const imageId = `image-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                uploadedFiles.push({
                    id: imageId,
                    file: file,
                    data: e.target.result
                });

                const previewItem = document.createElement('div');
                previewItem.className = 'preview-item';
                previewItem.id = imageId;
                previewItem.innerHTML = `
                    <img src="${e.target.result}" alt="Preview">
                    <button class="remove-button" data-id="${imageId}">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                elements.previewGrid.appendChild(previewItem);

                elements.startProcessing.disabled = uploadedFiles.length === 0;
            };

            reader.readAsDataURL(file);
        });
    }

    elements.uploadZone.addEventListener('click', () => {
        if (!processingInProgress) {
            elements.fileInput.click();
        }
    });

    elements.fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    elements.uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!processingInProgress) {
            elements.uploadZone.classList.add('drag-over');
        }
    });

    elements.uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        elements.uploadZone.classList.remove('drag-over');
    });

    elements.uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        elements.uploadZone.classList.remove('drag-over');
        if (!processingInProgress) {
            handleFiles(e.dataTransfer.files);
        }
    });

    elements.previewGrid.addEventListener('click', (e) => {
        if (e.target.closest('.remove-button') && !processingInProgress) {
            const id = e.target.closest('.remove-button').dataset.id;
            const element = document.getElementById(id);
            element.remove();
            uploadedFiles = uploadedFiles.filter(file => file.id !== id);
            elements.startProcessing.disabled = uploadedFiles.length === 0;
        }
    });

    elements.startProcessing.addEventListener('click', () => {
        if (processingInProgress) return;

        const questions = parseInt(elements.questionsInput.value) || 5;
        const choices = parseInt(elements.choicesInput.value) || 5;
        const strictMode = elements.strictModeCheckbox.checked;
        const displayMode = elements.displayModeSelect.value;
        
        // Собираем правильные ответы
        const correctAnswers = [];
        for (let i = 0; i < questions; i++) {
            const answers = Array.from(document.querySelectorAll(`input[name="question_${i}"]:checked`))
                .map(input => parseInt(input.value));
            if (answers.length === 0) {
                alert(`Выберите хотя бы один правильный ответ для вопроса ${i + 1}`);
                return;
            }
            correctAnswers.push(answers);
        }

        processingInProgress = true;
        elements.startProcessing.disabled = true;
        elements.resultsList.innerHTML = '';

        uploadedFiles.forEach(file => {
            socket.emit('process_multiple', {
                image: file.data,
                id: file.id,
                questions: questions,
                choices: choices,
                correctAnswers: correctAnswers,
                strictMode: strictMode,
                displayMode: displayMode
            });
        });
    });

    socket.on('multiple_result', (data) => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';
        
        const scoreText = data.strict_mode ? 
            `${data.correct_count}/${data.questions} (${data.score.toFixed(1)}%)` :
            `${data.correct_count.toFixed(2)}/${data.questions} (${data.score.toFixed(1)}%)`;
        
        resultItem.innerHTML = `
            <div class="result-image-container">
                <img src="${data.processed_image}" alt="Result">
                <div class="zoom-hint">Нажмите для увеличения</div>
            </div>
            <div class="result-info">
                <div class="result-score">${scoreText}</div>
                <div><strong>Правильные вопросы:</strong> ${data.correct_questions.join(', ')}</div>
                <div class="incorrect-questions">
                    <strong>Неправильные вопросы:</strong>
                    <ul>
                        ${data.incorrect_questions.map(q => `
                            <li>
                                Вопрос ${q.question_number}:
                                ${q.all_selected ? 
                                    '<div class="warning-message">❌ Выбраны все варианты ответов - вопрос не засчитан</div>' :
                                    `<br>- выбраны варианты: ${q.selected_answers.join(', ')}<br>- правильные варианты: ${q.correct_answers.join(', ')}`
                                }
                            </li>
                        `).join('')}
                    </ul>
                </div>
                <button class="send-to-report-button" data-result='${JSON.stringify({
                    correct_count: Math.round(data.correct_count),
                    total_questions: data.questions,
                    score: data.score,
                    correct_questions: data.correct_questions,
                    incorrect_questions: data.incorrect_questions.map(q => ({
                        question_number: q.question_number,
                        selected_answer: q.selected_answers[0],
                        correct_answer: q.correct_answers[0]
                    }))
                })}'>
                    <i class="fas fa-file-export"></i> Отправить в отчёт
                </button>
            </div>
        `;

        const imgContainer = resultItem.querySelector('.result-image-container');
        imgContainer.addEventListener('click', () => {
            modalImage.src = data.processed_image;
            modalOverlay.classList.add('active');
        });

        const sendToReportButton = resultItem.querySelector('.send-to-report-button');
        sendToReportButton.addEventListener('click', (e) => {
            const resultData = JSON.parse(e.target.dataset.result);
            socket.emit('add_to_report', resultData);
            sendToReportButton.disabled = true;
            sendToReportButton.innerHTML = '<i class="fas fa-check"></i> Отправлено';
            sendToReportButton.classList.add('sent');
        });

        elements.resultsList.appendChild(resultItem);
        
        if (elements.resultsList.children.length === uploadedFiles.length) {
            processingInProgress = false;
            elements.startProcessing.disabled = false;
        }
    });

    socket.on('report_added', (response) => {
        if (response.success) {
            console.log('Результат успешно добавлен в отчёт');
        } else {
            console.error('Ошибка при добавлении в отчёт:', response.message);
            const button = document.querySelector(`[data-result='${JSON.stringify(response.data)}']`);
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-file-export"></i> Отправить в отчёт';
                button.classList.remove('sent');
            }
        }
    });

    socket.on('error', (data) => {
        alert(data.message);
        processingInProgress = false;
        elements.startProcessing.disabled = false;
    });

    // Функция для получения текущих критериев
    function getCurrentCriteria() {
        const questions = parseInt(elements.questionsInput.value);
        const choices = parseInt(elements.choicesInput.value);
        const displayMode = elements.displayModeSelect.value;
        const strictMode = elements.strictModeCheckbox.checked;
        
        // Получаем правильные ответы из сетки
        const correctAnswers = [];
        const checkboxes = elements.correctAnswersGrid.querySelectorAll('input[type="checkbox"]');
        
        for (let q = 0; q < questions; q++) {
            const answers = [];
            for (let c = 0; c < choices; c++) {
                const checkbox = checkboxes[q * choices + c];
                if (checkbox && checkbox.checked) {
                    answers.push(parseInt(checkbox.value));
                }
            }
            correctAnswers.push(answers);
        }
        
        return {
            questions,
            choices,
            displayMode,
            strictMode,
            correctAnswers
        };
    }

    // Функция для установки критериев
    function setCriteria(criteria) {
        elements.questionsInput.value = criteria.questions;
        elements.choicesInput.value = criteria.choices;
        elements.displayModeSelect.value = criteria.displayMode;
        elements.strictModeCheckbox.checked = criteria.strictMode;
        
        // Пересоздаем сетку с новыми параметрами
        createAnswersGrid();
        
        // Устанавливаем правильные ответы
        const checkboxes = elements.correctAnswersGrid.querySelectorAll('input[type="checkbox"]');
        criteria.correctAnswers.forEach((answers, questionIndex) => {
            answers.forEach(answer => {
                const checkbox = checkboxes[questionIndex * criteria.choices + answer];
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
        });
    }

    // Обработчик сохранения критериев
    elements.saveCriteriaButton.addEventListener('click', () => {
        const criteria = getCurrentCriteria();
        const jsonString = JSON.stringify(criteria, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'test_criteria.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Обработчик загрузки критериев
    elements.loadCriteriaButton.addEventListener('click', () => {
        elements.criteriaFileInput.value = ''; // Сбрасываем значение перед открытием диалога
        elements.criteriaFileInput.click();
    });

    elements.criteriaFileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                try {
                    const criteria = JSON.parse(event.target.result);
                    setCriteria(criteria);
                } catch (error) {
                    alert('Ошибка при чтении файла критериев. Убедитесь, что файл имеет правильный формат.');
                }
            };
            reader.readAsText(file);
            // Сбрасываем значение после загрузки
            e.target.value = '';
        }
    });
}); 