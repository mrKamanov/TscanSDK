document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const previewGrid = document.getElementById('preview-grid');
    const startProcessing = document.getElementById('start-processing');
    const resultsList = document.getElementById('results-list');
    const resetButton = document.getElementById('reset-all');
    const questionsInput = document.getElementById('questions');
    const choicesInput = document.getElementById('choices');
    const strictModeCheckbox = document.getElementById('strict-mode');
    
    let uploadedFiles = [];
    let processingInProgress = false;

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
        previewGrid.innerHTML = '';
        resultsList.innerHTML = '';
        startProcessing.disabled = true;
        fileInput.value = '';
        processingInProgress = false;
        createAnswersGrid();
    }

    resetButton.addEventListener('click', resetAll);

    function createAnswersGrid() {
        const questions = parseInt(questionsInput.value) || 5;
        const choices = parseInt(choicesInput.value) || 5;
        const grid = document.getElementById('correct-answers-grid');
        
        grid.innerHTML = '';
        
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
            grid.appendChild(questionDiv);
        }
    }

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
                previewGrid.appendChild(previewItem);

                startProcessing.disabled = uploadedFiles.length === 0;
            };

            reader.readAsDataURL(file);
        });
    }

    uploadZone.addEventListener('click', () => {
        if (!processingInProgress) {
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!processingInProgress) {
            uploadZone.classList.add('drag-over');
        }
    });

    uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.remove('drag-over');
        if (!processingInProgress) {
            handleFiles(e.dataTransfer.files);
        }
    });

    previewGrid.addEventListener('click', (e) => {
        if (e.target.closest('.remove-button') && !processingInProgress) {
            const id = e.target.closest('.remove-button').dataset.id;
            const element = document.getElementById(id);
            element.remove();
            uploadedFiles = uploadedFiles.filter(file => file.id !== id);
            startProcessing.disabled = uploadedFiles.length === 0;
        }
    });

    startProcessing.addEventListener('click', () => {
        if (processingInProgress) return;

        const questions = parseInt(questionsInput.value) || 5;
        const choices = parseInt(choicesInput.value) || 5;
        const strictMode = strictModeCheckbox.checked;
        
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
        startProcessing.disabled = true;
        resultsList.innerHTML = '';

        uploadedFiles.forEach(file => {
            socket.emit('process_multiple', {
                image: file.data,
                id: file.id,
                questions: questions,
                choices: choices,
                correctAnswers: correctAnswers,
                strictMode: strictMode
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

        resultsList.appendChild(resultItem);
        
        if (resultsList.children.length === uploadedFiles.length) {
            processingInProgress = false;
            startProcessing.disabled = false;
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
        startProcessing.disabled = false;
    });

    // Обработчики изменения количества вопросов и вариантов ответов
    questionsInput.addEventListener('change', createAnswersGrid);
    choicesInput.addEventListener('change', createAnswersGrid);

    // Инициализация сетки ответов при загрузке страницы
    createAnswersGrid();
}); 