import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional

def stackImages(imgArray: List[List[np.ndarray]], scale: float, labels: List[List[str]] = []) -> np.ndarray:
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]

    def process_image(img: np.ndarray) -> np.ndarray:
        img = cv2.resize(img, (0, 0), None, scale, scale)
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if len(img.shape) == 2 else img

    if rowsAvailable:
        for x in range(rows):
            for y in range(cols):
                imgArray[x][y] = process_image(imgArray[x][y])
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [np.hstack(imgArray[x]) for x in range(rows)]
        ver = np.vstack(hor)
    else:
        imgArray = [process_image(x) for x in imgArray]
        ver = np.hstack(imgArray)

    if labels:
        eachImgWidth = int(ver.shape[1] / cols)
        eachImgHeight = int(ver.shape[0] / rows)
        for d in range(rows):
            for c in range(cols):
                label_width = len(labels[d][c]) * 13 + 27
                cv2.rectangle(ver, 
                            (c * eachImgWidth, eachImgHeight * d),
                            (c * eachImgWidth + label_width, 30 + eachImgHeight * d),
                            (255, 255, 255), 
                            cv2.FILLED)
                cv2.putText(ver, labels[d][c], 
                          (eachImgWidth * c + 10, eachImgHeight * d + 20),
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 0, 255), 2)
    return ver

def reorder(myPoints: np.ndarray) -> np.ndarray:
    myPoints = myPoints.reshape((4, 2))
    myPointsNew = np.zeros((4, 1, 2), np.int32)
    add = myPoints.sum(1)
    diff = np.diff(myPoints, axis=1)
    myPointsNew[0] = myPoints[np.argmin(add)]
    myPointsNew[3] = myPoints[np.argmax(add)]
    myPointsNew[1] = myPoints[np.argmin(diff)]
    myPointsNew[2] = myPoints[np.argmax(diff)]
    return myPointsNew

def find_contours(img: np.ndarray) -> List[np.ndarray]:
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    imgCanny = cv2.Canny(imgBlur, 10, 70)
    contours, _ = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return contours

def rectContour(contours: List[np.ndarray]) -> List[np.ndarray]:
    return sorted(
        [cont for cont in contours 
         if cv2.contourArea(cont) > 50 
         and len(cv2.approxPolyDP(cont, 0.02 * cv2.arcLength(cont, True), True)) == 4],
        key=cv2.contourArea,
        reverse=True
    )

def getCornerPoints(cont: np.ndarray) -> np.ndarray:
    peri = cv2.arcLength(cont, True)
    return cv2.approxPolyDP(cont, 0.02 * peri, True)

def splitBoxes(img: np.ndarray, questions: int, choices: int) -> List[np.ndarray]:
    if img.shape[0] % questions != 0 or img.shape[1] % choices != 0:
        raise ValueError("Изображение не может быть равномерно разделено на указанную сетку.")
    rows = np.vsplit(img, questions)
    return [box for r in rows for box in np.hsplit(r, choices)]

def drawGrid(img: np.ndarray, questions: int = 5, choices: int = 5) -> np.ndarray:
    secW = img.shape[1] // choices
    secH = img.shape[0] // questions
    
    for i in range(questions + 1):
        cv2.line(img, (0, int(secH * i)), (img.shape[1], int(secH * i)), (255, 79, 0), 2)
    
    for i in range(choices + 1):
        cv2.line(img, (int(secW * i), 0), (int(secW * i), img.shape[0]), (255, 79, 0), 2)
    
    return img

def draw_multiple_marks(img: np.ndarray, position: Tuple[int, int], mark_type: str, cell_size: Tuple[int, int]):
    cX, cY = position
    cellW, cellH = cell_size
    mark_size = min(cellW, cellH) // 3
    thickness = max(2, min(cellW, cellH) // 20)
    circle_radius = mark_size + thickness
    
    # Определяем цвета в зависимости от типа отметки
    colors = {
        'correct': {  # Полностью правильный ответ
            'fill': (0, 255, 0),  # Зеленый
            'border': (0, 200, 0),
            'mark': (255, 255, 255)
        },
        'partial': {  # Частично правильный ответ (выбран правильный, но не все)
            'fill': (255, 165, 0),  # Оранжевый
            'border': (200, 130, 0),
            'mark': (255, 255, 255)
        },
        'incorrect': {  # Неправильный ответ
            'fill': (255, 0, 0),  # Красный
            'border': (200, 0, 0),
            'mark': (255, 255, 255)
        },
        'missed': {  # Пропущенный правильный ответ
            'fill': (128, 128, 128),  # Серый
            'border': (100, 100, 100),
            'mark': (255, 255, 255)
        },
        'unselected': {  # Неправильный и невыбранный
            'fill': (240, 240, 240),  # Светло-серый
            'border': (200, 200, 200),
            'mark': (128, 128, 128)
        }
    }
    
    color = colors[mark_type]
    
    # Рисуем круг
    cv2.circle(img, (cX, cY), circle_radius, color['fill'], -1)
    cv2.circle(img, (cX, cY), circle_radius, color['border'], thickness)
    
    # Рисуем отметку в зависимости от типа
    if mark_type in ['correct', 'partial']:
        # Галочка для правильных и частично правильных
        points = np.array([
            [cX - mark_size, cY],
            [cX - mark_size//2, cY + mark_size//2],
            [cX + mark_size, cY - mark_size//2]
        ])
        cv2.polylines(img, [points], isClosed=False, color=(0, 0, 0), thickness=thickness*2)
        cv2.polylines(img, [points], isClosed=False, color=color['mark'], thickness=thickness)
    elif mark_type == 'incorrect':
        # Крестик для неправильных
        cv2.line(img, 
                (cX - mark_size//2, cY - mark_size//2),
                (cX + mark_size//2, cY + mark_size//2),
                (0, 0, 0), thickness*2)
        cv2.line(img,
                (cX - mark_size//2, cY + mark_size//2),
                (cX + mark_size//2, cY - mark_size//2),
                (0, 0, 0), thickness*2)
        cv2.line(img,
                (cX - mark_size//2, cY - mark_size//2),
                (cX + mark_size//2, cY + mark_size//2),
                color['mark'], thickness)
        cv2.line(img,
                (cX - mark_size//2, cY + mark_size//2),
                (cX + mark_size//2, cY - mark_size//2),
                color['mark'], thickness)
    elif mark_type == 'missed':
        # Кружок с точкой для пропущенных правильных
        cv2.circle(img, (cX, cY), mark_size//2, (0, 0, 0), -1)
        cv2.circle(img, (cX, cY), mark_size//2, color['mark'], thickness)

def showMultipleAnswers(img: np.ndarray, selected_answers: List[List[int]], correct_answers: List[List[int]], 
                       questions: int = 5, choices: int = 5) -> None:
    secW = img.shape[1] // choices
    secH = img.shape[0] // questions
    cell_size = (secW, secH)
    
    for x in range(questions):
        selected = set(selected_answers[x])
        correct = set(correct_answers[x])
        
        for y in range(choices):
            pos = ((y * secW) + secW // 2, (x * secH) + secH // 2)
            
            if y in selected:
                if y in correct:
                    # Выбран и правильный
                    if selected == correct:
                        mark_type = 'correct'  # Все ответы правильные
                    else:
                        mark_type = 'partial'  # Частично правильный ответ
                else:
                    mark_type = 'incorrect'  # Выбран, но неправильный
            else:
                if y in correct:
                    mark_type = 'missed'  # Не выбран, но правильный
                else:
                    mark_type = 'unselected'  # Не выбран и неправильный
            
            draw_multiple_marks(img, pos, mark_type, cell_size)

def adjust_image(img: np.ndarray, brightness: float = 0, contrast: float = 1, 
                saturation: float = 1, sharpness: float = 1) -> np.ndarray:
    result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])
    result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
    img = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)

    img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)
    
    b, g, r = cv2.split(img)
    b = cv2.multiply(b, 0.8)
    g = cv2.multiply(g, 1.2)
    r = cv2.multiply(r, 1.2)
    
    img = cv2.merge([b, g, r])
    
    if sharpness != 1:
        blurred = cv2.GaussianBlur(img, (0, 0), 3)
        img = cv2.addWeighted(img, 1 + sharpness, blurred, -sharpness, 0)
    
    return img

def process_multiple_choice(img: np.ndarray, questions: int, choices: int, correct_answers: List[List[int]], 
                          image_size: int, strict_mode: bool = True, overlay_mode: bool = False, 
                          brightness: float = 0, contrast: float = 1, saturation: float = 1, 
                          sharpness: float = 1) -> Tuple:
    try:
        # Предварительная обработка изображения
        img = adjust_image(img, brightness, contrast, saturation, sharpness)
        new_width = choices * (image_size // choices)
        new_height = questions * (image_size // questions)
        img = cv2.resize(img, (new_width, new_height))
        
        # Поиск и обработка контуров
        contours = find_contours(img)
        rectCon = rectContour(contours)
        
        if not rectCon:
            raise ValueError("Не удалось найти достаточное количество контуров.")
            
        biggestPoints = getCornerPoints(rectCon[0])
        if biggestPoints.size == 0:
            raise ValueError("Не удалось определить углы контура.")
            
        biggestPoints = reorder(biggestPoints)
        pts1 = np.float32(biggestPoints)
        pts2 = np.float32([[0, 0], [new_width, 0], [0, new_height], [new_width, new_height]])
        
        # Преобразование перспективы
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        imgWarpColored = cv2.warpPerspective(img, matrix, (new_width, new_height))
        
        # Улучшенная обработка изображения для выделения заштрихованных областей
        imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgWarpGray, (5, 5), 1)
        imgThresh = cv2.threshold(imgBlur, 170, 255, cv2.THRESH_BINARY_INV)[1]
        
        # Морфологические операции для удаления шума и усиления заштрихованных областей
        kernel = np.ones((3, 3), np.uint8)
        imgMorph = cv2.morphologyEx(imgThresh, cv2.MORPH_CLOSE, kernel)
        imgMorph = cv2.morphologyEx(imgMorph, cv2.MORPH_OPEN, kernel)
        
        # Разделение на ячейки и анализ
        boxes = splitBoxes(imgMorph, questions, choices)
        myPixelVal = np.array([[cv2.countNonZero(boxes[i * choices + j]) 
                               for j in range(choices)] for i in range(questions)])
        
        # Улучшенный алгоритм определения заштрихованных ячеек
        selected_answers = []
        for i in range(questions):
            row_values = myPixelVal[i]
            max_val = np.max(row_values)
            if max_val > 0:
                # Адаптивный порог на основе максимального значения в строке
                threshold = max_val * 0.5  # Увеличили порог до 50% от максимума
                row_answers = [j for j, val in enumerate(row_values) if val > threshold]
                
                # Дополнительная проверка для случаев, когда несколько ячеек близки к порогу
                if len(row_answers) > 0:
                    # Если есть явно выделяющиеся ответы, оставляем только их
                    max_in_selected = max(row_values[j] for j in row_answers)
                    row_answers = [j for j in row_answers if row_values[j] > max_in_selected * 0.8]
            else:
                row_answers = []
            
            selected_answers.append(row_answers)
        
        # Проверка правильности ответов с учетом режима оценивания
        correct_count = 0
        correct_questions = []
        incorrect_questions = []
        
        for i in range(questions):
            selected = set(selected_answers[i])
            correct = set(correct_answers[i])
            
            # Проверяем, не выбраны ли все варианты ответов
            if len(selected) == choices:
                # Если выбраны все варианты - вопрос считается неправильным
                question_score = 0.0
                result_info = {
                    "question_number": i + 1,
                    "selected_answers": [x + 1 for x in selected_answers[i]],
                    "correct_answers": [x + 1 for x in correct_answers[i]],
                    "partial_score": 0.0,
                    "correct_selected": 0,
                    "total_correct": len(correct),
                    "incorrect_selected": choices,
                    "all_selected": True  # Флаг, что выбраны все варианты
                }
                incorrect_questions.append(result_info)
                continue

            if len(correct) > 0:
                correct_selected = len(selected & correct)  # Количество правильно выбранных
                incorrect_selected = len(selected - correct)  # Количество неправильно выбранных
                total_correct = len(correct)  # Общее количество правильных ответов
                
                # Вычисляем оценку в зависимости от режима
                if strict_mode:
                    # Строгий режим: все должно быть правильно
                    question_score = 1.0 if selected == correct else 0.0
                else:
                    # Частичный режим: учитываем процент правильных ответов
                    if incorrect_selected == 0:  # Если нет неправильных ответов
                        question_score = correct_selected / total_correct
                    else:
                        # Если есть неправильные ответы, уменьшаем оценку
                        question_score = max(0, (correct_selected - incorrect_selected) / total_correct)
            else:
                question_score = 1 if len(selected) == 0 else 0
            
            correct_count += question_score
            
            if question_score == 1:
                correct_questions.append(i + 1)
            else:
                result_info = {
                    "question_number": i + 1,
                    "selected_answers": [x + 1 for x in selected_answers[i]],
                    "correct_answers": [x + 1 for x in correct_answers[i]],
                    "partial_score": question_score,
                    "correct_selected": len(selected & correct),
                    "total_correct": len(correct),
                    "incorrect_selected": len(selected - correct),
                    "all_selected": False  # Флаг, что выбраны НЕ все варианты
                }
                incorrect_questions.append(result_info)
        
        score = (correct_count / questions) * 100
        
        # Визуализация результатов
        imgFinal = imgWarpColored.copy()
        showMultipleAnswers(imgFinal, selected_answers, correct_answers, questions, choices)
        drawGrid(imgFinal, questions, choices)
        
        if not overlay_mode:
            return imgFinal, correct_count, score, incorrect_questions, correct_questions
            
        invMatrix = cv2.getPerspectiveTransform(pts2, pts1)
        imgInvWarp = cv2.warpPerspective(imgFinal, invMatrix, (img.shape[1], img.shape[0]))
        
        return imgInvWarp, correct_count, score, incorrect_questions, correct_questions
        
    except Exception as e:
        raise ValueError(f"Ошибка обработки изображения: {str(e)}") 