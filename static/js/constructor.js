const omrSheet = document.getElementById('omr-sheet');
const bubblesContainer = document.getElementById('bubbles-container');
const numQuestionsInput = document.getElementById('num-questions');
const numOptionsInput = document.getElementById('num-options');
const omrSettingsForm = document.getElementById('omr-settings');
const borderWidthInput = document.getElementById('border-width');
const bubbleSizeInput = document.getElementById('bubble-size');
const bubbleSpacingInput = document.getElementById('bubble-spacing');
const borderPaddingInput = document.getElementById('border-padding');
const scaleInput = document.getElementById('scale');
const fontSizeInput = document.getElementById('font-size');


const omrTitleHeader = document.getElementById('omr-title-header');
const omrDescriptionHeader = document.getElementById('omr-description-header');


const studentNameLabel = document.getElementById('student-name-label');
const studentNameValue = document.getElementById('student-name-value');
const dateLabel = document.getElementById('date-label');
const dateValue = document.getElementById('date-value');
const subjectLabel = document.getElementById('subject-label');
const subjectValue = document.getElementById('subject-value');
const instructionLabel = document.getElementById('instruction-label');
const instructionValue = document.getElementById('instruction-value');

let isDragging = false;
let startX = 0;
let startY = 0;
let scale = 1;
let offsetX = 0;
let offsetY = 0;
let animationFrameId;

const displayModeSelect = document.getElementById('display-mode');
const columnSpacingControl = document.getElementById('column-spacing-control');
const columnSpacingInput = document.getElementById('column-spacing');
const alignColumnsButton = document.getElementById('align-columns');

let secondContainer = null;
let isTwoColumnsMode = false;

// Функция применения размеров и отступов
function applyBubbleStyles() {
    const bubbleSize = bubbleSizeInput.value;
    const bubbleSpacing = bubbleSpacingInput.value;
    const borderPadding = borderPaddingInput.value;
    const borderWidth = borderWidthInput.value;
    
    // Пересоздаем кружки с новыми размерами
    createBubbles();
}

// Функция генерации OMR-листа
function generateOmrSheet(numQuestions, numOptions) {
    bubblesContainer.innerHTML = '';

    for (let i = 1; i <= numQuestions; i++) {
        const bubbleBlock = document.createElement('div');
        bubbleBlock.className = 'bubble-block';
        bubbleBlock.innerHTML = `<div class="question-number">Вопрос ${i}</div>`;
        const bubblesDiv = document.createElement('div');
        bubblesDiv.className = 'bubbles';

        for (let j = 1; j <= numOptions; j++) {
            const bubble = document.createElement('div');
            bubble.className = 'bubble';
            bubble.textContent = `${i}.${j}`;
            bubble.dataset.question = i;
            bubble.dataset.option = j;
            
            // Добавляем обработчик клика для скрытия кружка
            bubble.addEventListener('click', function() {
                this.style.display = 'none';
            });
            
            bubblesDiv.appendChild(bubble);
        }
        bubbleBlock.appendChild(bubblesDiv);
        bubblesContainer.appendChild(bubbleBlock);
    }
    bubblesContainer.style.height = 'auto';
    bubblesContainer.style.width = 'fit-content';
    applyBubbleStyles();
    const fontSize = parseInt(fontSizeInput.value);
    omrSheet.style.fontSize = `${fontSize}px`;
    omrTitleHeader.style.fontSize = `${fontSize * 1.3}px`;
    omrDescriptionHeader.style.fontSize = `${fontSize}px`;
    studentNameLabel.style.fontSize = `${fontSize}px`;
    studentNameValue.style.fontSize = `${fontSize}px`;
    dateLabel.style.fontSize = `${fontSize}px`;
    dateValue.style.fontSize = `${fontSize}px`;
    subjectLabel.style.fontSize = `${fontSize}px`;
    subjectValue.style.fontSize = `${fontSize}px`;
    instructionLabel.style.fontSize = `${fontSize}px`;
    instructionValue.style.fontSize = `${fontSize}px`;
}

// Обработчик отправки формы
omrSettingsForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const numQuestions = parseInt(numQuestionsInput.value);
    const numOptions = parseInt(numOptionsInput.value);
    const sheetTitle = document.getElementById('sheet-title').value;
    const sheetDescription = document.getElementById('sheet-description').value;
    const studentName = document.getElementById('student-name').value;
    const date = document.getElementById('date').value;
    const subject = document.getElementById('subject').value;
    const instruction = document.getElementById('instruction').value;
    const fontSize = parseInt(fontSizeInput.value);

    if (numQuestions < 1 || numQuestions > 35) {
        alert("Количество вопросов должно быть от 1 до 35.");
        return;
    }
    if (numOptions < 1 || numOptions > 10) {
        alert("Количество вариантов ответов должно быть от 1 до 10.");
        return;
    }
    const borderWidth = parseInt(borderWidthInput.value);
    if (borderWidth < 1 || borderWidth > 10) {
        alert("Толщина рамки должна быть от 1 до 10.");
        return;
    }

    omrTitleHeader.textContent = sheetTitle;
    omrDescriptionHeader.textContent = sheetDescription;
    studentNameValue.textContent = studentName;
    dateValue.textContent = date;
    subjectValue.textContent = subject;
    instructionValue.textContent = instruction;

    generateOmrSheet(numQuestions, numOptions);
    resetTransform();
});

// Функции для сохранения
async function saveAsPDF() {
    document.querySelectorAll('.drag-handle').forEach(handle => {
        handle.style.display = 'none';
    });

    const sheet = document.getElementById('omr-sheet');
    const canvas = await html2canvas(sheet, {
        scale: 2,
        backgroundColor: '#ffffff'
    });

    document.querySelectorAll('.drag-handle').forEach(handle => {
        handle.style.display = '';
    });
    
    const imgData = canvas.toDataURL('image/jpeg', 1.0);
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
    });

    const imgProps = pdf.getImageProperties(imgData);
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
    
    pdf.addImage(imgData, 'JPEG', 0, 0, pdfWidth, pdfHeight);
    pdf.save('omr-form.pdf');
}

async function saveAsImage() {
    document.querySelectorAll('.drag-handle').forEach(handle => {
        handle.style.display = 'none';
    });

    const sheet = document.getElementById('omr-sheet');
    const canvas = await html2canvas(sheet, {
        scale: 2,
        backgroundColor: '#ffffff'
    });

    document.querySelectorAll('.drag-handle').forEach(handle => {
        handle.style.display = '';
    });
    
    const link = document.createElement('a');
    link.download = 'omr-form.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
}

function clearBackgrounds(element) {
    // Временно сохраняем текущие стили фона
    const elements = element.querySelectorAll('*');
    const savedStyles = new Map();
    
    // Сохраняем и очищаем фоны
    elements.forEach(el => {
        savedStyles.set(el, {
            background: el.style.background,
            backgroundColor: el.style.backgroundColor
        });
        el.style.background = 'transparent';
        el.style.backgroundColor = 'transparent';
    });
    
    // Также сохраняем стили самого элемента
    savedStyles.set(element, {
        background: element.style.background,
        backgroundColor: element.style.backgroundColor
    });
    element.style.background = 'transparent';
    element.style.backgroundColor = 'transparent';
    
    return savedStyles;
}

function restoreBackgrounds(savedStyles) {
    savedStyles.forEach((styles, element) => {
        element.style.background = styles.background;
        element.style.backgroundColor = styles.backgroundColor;
    });
}

function saveAsPNG() {
    const omrSheet = document.getElementById('omr-sheet');
    
    // Скрываем элементы перетаскивания
    document.querySelectorAll('.drag-handle').forEach(handle => {
        handle.style.display = 'none';
    });
    
    // Добавляем класс для прозрачного режима
    omrSheet.classList.add('transparent-mode');
    
    // Сохраняем текущие стили
    const savedStyles = new Map();
    const allElements = omrSheet.querySelectorAll('*');
    allElements.forEach(el => {
        savedStyles.set(el, {
            background: el.style.background,
            backgroundColor: el.style.backgroundColor,
            backgroundImage: el.style.backgroundImage,
            boxShadow: el.style.boxShadow
        });
        
        // Очищаем все фоновые стили
        el.style.background = 'none';
        el.style.backgroundColor = 'transparent';
        el.style.backgroundImage = 'none';
        el.style.boxShadow = 'none';
    });
    
    // Используем html2canvas с настройками прозрачности
    html2canvas(omrSheet, {
        backgroundColor: null,
        scale: 2,
        useCORS: true,
        logging: false,
        onclone: function(clonedDoc) {
            const clonedSheet = clonedDoc.getElementById('omr-sheet');
            clonedSheet.classList.add('transparent-mode');
            
            // Очищаем фоны у всех элементов в клоне
            const clonedElements = clonedSheet.querySelectorAll('*');
            clonedElements.forEach(el => {
                el.style.background = 'none';
                el.style.backgroundColor = 'transparent';
                el.style.backgroundImage = 'none';
                el.style.boxShadow = 'none';
            });
        }
    }).then(function(canvas) {
        // Создаем ссылку для скачивания
        const link = document.createElement('a');
        link.download = 'omr_sheet.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
        
        // Восстанавливаем стили
        allElements.forEach(el => {
            const styles = savedStyles.get(el);
            if (styles) {
                el.style.background = styles.background;
                el.style.backgroundColor = styles.backgroundColor;
                el.style.backgroundImage = styles.backgroundImage;
                el.style.boxShadow = styles.boxShadow;
            }
        });
        
        // Удаляем класс прозрачного режима и восстанавливаем элементы перетаскивания
        omrSheet.classList.remove('transparent-mode');
        document.querySelectorAll('.drag-handle').forEach(handle => {
            handle.style.display = '';
        });
    });
}

// Функции для трансформации
function resetTransform() {
    scale = 1;
    offsetX = 0;
    offsetY = 0;
    bubblesContainer.style.transform = `translate(0px, 0px) scale(1)`;
}

function updateTransform() {
    if (!isDragging) return;
    bubblesContainer.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
    animationFrameId = requestAnimationFrame(updateTransform);
}

// Обработчики событий для перетаскивания и масштабирования
bubblesContainer.addEventListener('mousedown', (e) => {
    isDragging = true;
    startX = e.clientX - offsetX;
    startY = e.clientY - offsetY;
    bubblesContainer.style.cursor = 'grabbing';
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
    }
});

bubblesContainer.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    offsetX = e.clientX - startX;
    offsetY = e.clientY - startY;
    updateTransform();
});

bubblesContainer.addEventListener('mouseup', () => {
    isDragging = false;
    bubblesContainer.style.cursor = 'default';
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
});

bubblesContainer.addEventListener('mouseleave', () => {
    isDragging = false;
    bubblesContainer.style.cursor = 'default';
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
});

bubblesContainer.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomSpeed = 0.002;
    scale += e.deltaY * -zoomSpeed;
    scale = Math.max(0.5, Math.min(2, scale));
    bubblesContainer.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
});

// Обработчики событий для элементов управления
scaleInput.addEventListener('input', () => {
    scale = parseFloat(scaleInput.value);
    bubblesContainer.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
});

fontSizeInput.addEventListener('input', () => {
    const fontSize = parseInt(fontSizeInput.value);
    omrSheet.style.fontSize = `${fontSize}px`;
    omrTitleHeader.style.fontSize = `${fontSize * 1.3}px`;
    omrDescriptionHeader.style.fontSize = `${fontSize}px`;
    studentNameLabel.style.fontSize = `${fontSize}px`;
    studentNameValue.style.fontSize = `${fontSize}px`;
    dateLabel.style.fontSize = `${fontSize}px`;
    dateValue.style.fontSize = `${fontSize}px`;
    subjectLabel.style.fontSize = `${fontSize}px`;
    subjectValue.style.fontSize = `${fontSize}px`;
    instructionLabel.style.fontSize = `${fontSize}px`;
    instructionValue.style.fontSize = `${fontSize}px`;
});

// Обработчики для чекбоксов видимости
document.getElementById('show-title').addEventListener('change', function() {
    document.getElementById('omr-title-header').style.display = this.checked ? 'block' : 'none';
});

document.getElementById('show-description').addEventListener('change', function() {
    document.getElementById('omr-description-header').style.display = this.checked ? 'block' : 'none';
});

document.getElementById('show-student-name').addEventListener('change', function() {
    document.getElementById('student-name-row').style.display = this.checked ? 'table-row' : 'none';
});

document.getElementById('show-date').addEventListener('change', function() {
    document.getElementById('date-row').style.display = this.checked ? 'table-row' : 'none';
});

document.getElementById('show-subject').addEventListener('change', function() {
    document.getElementById('subject-row').style.display = this.checked ? 'table-row' : 'none';
});

document.getElementById('show-instruction').addEventListener('change', function() {
    document.getElementById('instruction-row').style.display = this.checked ? 'table-row' : 'none';
});

// Инициализация перетаскиваемых элементов
const draggables = document.querySelectorAll('.draggable');

draggables.forEach(draggable => {
    const dragHandle = draggable.querySelector('.drag-handle');
    let isDragging = false;
    let startX, startY;
    let initialTransform = { x: 0, y: 0 };

    function getCurrentTransform(element) {
        const transform = window.getComputedStyle(element).transform;
        if (transform === 'none') return { x: 0, y: 0 };
        
        const matrix = new DOMMatrixReadOnly(transform);
        return {
            x: matrix.m41,
            y: matrix.m42
        };
    }

    dragHandle.addEventListener('mousedown', startDragging);

    function startDragging(e) {
        e.preventDefault();
        isDragging = true;
        
        const currentTransform = getCurrentTransform(draggable);
        initialTransform = currentTransform;
        
        startX = e.clientX - currentTransform.x;
        startY = e.clientY - currentTransform.y;
        
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', stopDragging);
        
        draggable.classList.add('dragging');
    }

    function drag(e) {
        if (!isDragging) return;
        
        const x = e.clientX - startX;
        const y = e.clientY - startY;
        
        draggable.style.transform = `translate(${x}px, ${y}px)`;
    }

    function stopDragging() {
        isDragging = false;
        draggable.classList.remove('dragging');
        
        document.removeEventListener('mousemove', drag);
        document.removeEventListener('mouseup', stopDragging);
    }
});

// Инициализация при загрузке страницы
const initialNumQuestions = parseInt(numQuestionsInput.value) || 5;
const initialNumOptions = parseInt(numOptionsInput.value) || 5;
const initialFontSize = parseInt(fontSizeInput.value) || 16;
omrSheet.style.fontSize = `${initialFontSize}px`;
createBubbles();

// Добавляем обработчики для кнопок сохранения
document.getElementById('save-pdf').addEventListener('click', saveAsPDF);
document.getElementById('save-image').addEventListener('click', saveAsImage);
document.getElementById('save-png').addEventListener('click', saveAsPNG);

// Обработчики изменения размеров и отступов
bubbleSizeInput.addEventListener('input', applyBubbleStyles);
bubbleSpacingInput.addEventListener('input', applyBubbleStyles);
borderPaddingInput.addEventListener('input', applyBubbleStyles);
borderWidthInput.addEventListener('input', applyBubbleStyles);

// Функция для создания контейнера с вопросами
function createQuestionsContainer() {
    const container = document.createElement('div');
    container.className = 'questions-container';
    container.style.position = 'relative';
    container.style.width = 'fit-content';
    return container;
}

// Функция для создания второго контейнера
function createSecondContainer() {
    if (secondContainer) {
        secondContainer.remove();
    }
    secondContainer = createQuestionsContainer();
    secondContainer.style.marginLeft = `${columnSpacingInput.value}px`;
    bubblesContainer.appendChild(secondContainer);
    return secondContainer;
}

// Функция для распределения вопросов между столбцами
function distributeQuestions() {
    const questions = Array.from(bubblesContainer.querySelectorAll('.question-row'));
    const half = Math.ceil(questions.length / 2);
    
    // Очищаем контейнеры
    bubblesContainer.innerHTML = '';
    if (isTwoColumnsMode) {
        secondContainer = createSecondContainer();
    }
    
    // Распределяем вопросы
    questions.forEach((question, index) => {
        if (isTwoColumnsMode) {
            if (index < half) {
                bubblesContainer.appendChild(question);
            } else {
                secondContainer.appendChild(question);
            }
        } else {
            bubblesContainer.appendChild(question);
        }
    });
}

// Функция для выравнивания столбцов
function alignColumns() {
    if (!isTwoColumnsMode || !secondContainer) return;
    
    const firstContainer = bubblesContainer;
    const firstRect = firstContainer.getBoundingClientRect();
    
    // Выравниваем по горизонтали
    secondContainer.style.top = `${firstRect.top}px`;
    secondContainer.style.left = `${firstRect.right + parseInt(columnSpacingInput.value)}px`;
}

// Обработчик изменения режима отображения
displayModeSelect.addEventListener('change', function() {
    isTwoColumnsMode = this.value === 'double';
    columnSpacingControl.style.display = isTwoColumnsMode ? 'block' : 'none';
    
    if (isTwoColumnsMode) {
        createSecondContainer();
    } else if (secondContainer) {
        secondContainer.remove();
        secondContainer = null;
    }
    
    distributeQuestions();
});

// Обработчик изменения расстояния между столбцами
columnSpacingInput.addEventListener('input', function() {
    if (isTwoColumnsMode && secondContainer) {
        secondContainer.style.marginLeft = `${this.value}px`;
        alignColumns();
    }
});

// Обработчик кнопки выравнивания столбцов
alignColumnsButton.addEventListener('click', alignColumns);

// Модифицируем существующую функцию createBubbles
function createBubbles() {
    const numQuestions = parseInt(numQuestionsInput.value);
    const numOptions = parseInt(numOptionsInput.value);
    
    bubblesContainer.innerHTML = '';
    bubblesContainer.style.border = 'none';
    bubblesContainer.style.padding = '0';
    bubblesContainer.style.display = 'flex';
    bubblesContainer.style.gap = `${columnSpacingInput.value}px`;
    
    // Создаем первый контейнер
    const firstContainer = document.createElement('div');
    firstContainer.className = 'questions-container';
    firstContainer.style.border = `${borderWidthInput.value}px solid #000000`;
    firstContainer.style.padding = `${borderPaddingInput.value}px`;
    firstContainer.style.background = 'transparent';
    bubblesContainer.appendChild(firstContainer);
    
    // Создаем второй контейнер если нужно
    let secondContainer = null;
    if (isTwoColumnsMode) {
        secondContainer = document.createElement('div');
        secondContainer.className = 'questions-container';
        secondContainer.style.border = `${borderWidthInput.value}px solid #000000`;
        secondContainer.style.padding = `${borderPaddingInput.value}px`;
        secondContainer.style.background = 'transparent';
        bubblesContainer.appendChild(secondContainer);
    }
    
    const half = Math.ceil(numQuestions / 2);
    
    for (let i = 0; i < numQuestions; i++) {
        const questionRow = document.createElement('div');
        questionRow.className = 'question-row';
        
        const bubblesWrapper = document.createElement('div');
        bubblesWrapper.className = 'bubbles-wrapper';
        bubblesWrapper.style.display = 'flex';
        bubblesWrapper.style.gap = `${bubbleSpacingInput.value}px`;
        
        for (let j = 0; j < numOptions; j++) {
            const bubble = document.createElement('div');
            bubble.className = 'bubble';
            bubble.style.width = `${bubbleSizeInput.value}px`;
            bubble.style.height = `${bubbleSizeInput.value}px`;
            bubble.style.border = `2px solid #000000`;
            bubble.style.background = '#ffffff';
            bubble.style.display = 'flex';
            bubble.style.alignItems = 'center';
            bubble.style.justifyContent = 'center';
            bubble.style.fontSize = `${parseInt(bubbleSizeInput.value) * 0.4}px`;
            bubble.style.color = '#000000';
            bubble.textContent = `${i + 1}.${j + 1}`;
            
            // Добавляем обработчик клика для скрытия кружка
            bubble.addEventListener('click', function() {
                this.style.display = 'none';
            });
            
            bubblesWrapper.appendChild(bubble);
        }
        
        questionRow.appendChild(bubblesWrapper);
        
        if (isTwoColumnsMode) {
            if (i < half) {
                firstContainer.appendChild(questionRow);
            } else {
                secondContainer.appendChild(questionRow);
            }
        } else {
            firstContainer.appendChild(questionRow);
        }
    }
}

// Обновляем стили для контейнеров
function updateContainerStyles() {
    const containers = bubblesContainer.querySelectorAll('.questions-container');
    containers.forEach(container => {
        container.style.border = `${borderWidthInput.value}px solid #000000`;
        container.style.padding = `${borderPaddingInput.value}px`;
        container.style.background = 'transparent';
    });
}

// Добавляем обработчик для обновления стилей при изменении режима
displayModeSelect.addEventListener('change', function() {
    isTwoColumnsMode = this.value === 'double';
    columnSpacingControl.style.display = isTwoColumnsMode ? 'block' : 'none';
    updateContainerStyles();
    createBubbles();
});

// Обновляем обработчик изменения расстояния между столбцами
columnSpacingInput.addEventListener('input', function() {
    if (isTwoColumnsMode) {
        bubblesContainer.style.gap = `${this.value}px`;
        createBubbles();
    }
});

// Модифицируем обработчик формы
omrSettingsForm.addEventListener('submit', function(e) {
    e.preventDefault();
    createBubbles();
}); 