import cv2
import numpy as np
import base64
from typing import List, Tuple, Dict, Optional, Any

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
    
    colors = {
        'correct': {  
            'fill': (0, 255, 0),  
            'border': (0, 200, 0),
            'mark': (255, 255, 255)
        },
        'partial': {  
            'fill': (255, 165, 0),  
            'border': (200, 130, 0),
            'mark': (255, 255, 255)
        },
        'incorrect': {  
            'fill': (255, 0, 0),  
            'border': (200, 0, 0),
            'mark': (255, 255, 255)
        },
        'missed': {  
            'fill': (128, 128, 128),  
            'border': (100, 100, 100),
            'mark': (255, 255, 255)
        }
    }
    
    if mark_type == 'unselected':
        return
        
    color = colors[mark_type]
    
    cv2.circle(img, (cX, cY), circle_radius, color['fill'], -1)
    cv2.circle(img, (cX, cY), circle_radius, color['border'], thickness)
    
    if mark_type in ['correct', 'partial']:
        points = np.array([
            [cX - mark_size, cY],
            [cX - mark_size//2, cY + mark_size//2],
            [cX + mark_size, cY - mark_size//2]
        ])
        cv2.polylines(img, [points], isClosed=False, color=(0, 0, 0), thickness=thickness*2)
        cv2.polylines(img, [points], isClosed=False, color=color['mark'], thickness=thickness)
    elif mark_type == 'incorrect':
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
        cv2.circle(img, (cX, cY), mark_size//2, (0, 0, 0), -1)
        cv2.circle(img, (cX, cY), mark_size//2, color['mark'], thickness)

def showMultipleAnswers(img: np.ndarray, selected_answers: List[List[int]], correct_answers: List[List[int]], 
                       questions: int = 5, choices: int = 5) -> None:
    secW = img.shape[1] // choices
    secH = img.shape[0] // questions
    
    # Определяем масштаб для маркеров (50% от размера ячейки)
    marker_scale = 0.5
    cell_size = (int(secW * marker_scale), int(secH * marker_scale))
    
    for x in range(questions):
        selected = set(selected_answers[x])
        correct = set(correct_answers[x])
        
        for y in range(choices):
            pos = ((y * secW) + secW // 2, (x * secH) + secH // 2)
            
            if y in selected:
                if y in correct:
                    if selected == correct:
                        mark_type = 'correct'  
                    else:
                        mark_type = 'partial'  
                else:
                    mark_type = 'incorrect'  
            else:
                if y in correct:
                    mark_type = 'missed'  
                else:
                    mark_type = 'unselected'  
            
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
        img = adjust_image(img, brightness, contrast, saturation, sharpness)
        new_width = choices * (image_size // choices)
        new_height = questions * (image_size // questions)
        img = cv2.resize(img, (new_width, new_height))
        
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
        
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        imgWarpColored = cv2.warpPerspective(img, matrix, (new_width, new_height))
        
        imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgWarpGray, (5, 5), 1)
        imgThresh = cv2.threshold(imgBlur, 170, 255, cv2.THRESH_BINARY_INV)[1]
        
        kernel = np.ones((3, 3), np.uint8)
        imgMorph = cv2.morphologyEx(imgThresh, cv2.MORPH_CLOSE, kernel)
        imgMorph = cv2.morphologyEx(imgMorph, cv2.MORPH_OPEN, kernel)
        
        boxes = splitBoxes(imgMorph, questions, choices)
        myPixelVal = np.array([[cv2.countNonZero(boxes[i * choices + j]) 
                               for j in range(choices)] for i in range(questions)])
        
        
        selected_answers = []
        for i in range(questions):
            row_values = myPixelVal[i]
            max_val = np.max(row_values)
            if max_val > 0:
                threshold = max_val * 0.5  
                row_answers = [j for j, val in enumerate(row_values) if val > threshold]
                
                if len(row_answers) > 0:
                    max_in_selected = max(row_values[j] for j in row_answers)
                    row_answers = [j for j in row_answers if row_values[j] > max_in_selected * 0.8]
            else:
                row_answers = []
            
            selected_answers.append(row_answers)
        
        correct_count = 0
        correct_questions = []
        incorrect_questions = []
        
        for i in range(questions):
            selected = set(selected_answers[i])
            correct = set(correct_answers[i])
            
            if len(selected) == choices:
                question_score = 0.0
                result_info = {
                    "question_number": i + 1,
                    "selected_answers": [x + 1 for x in selected_answers[i]],
                    "correct_answers": [x + 1 for x in correct_answers[i]],
                    "partial_score": 0.0,
                    "correct_selected": 0,
                    "total_correct": len(correct),
                    "incorrect_selected": choices,
                    "all_selected": True 
                }
                incorrect_questions.append(result_info)
                continue

            if len(correct) > 0:
                correct_selected = len(selected & correct)  
                incorrect_selected = len(selected - correct)  
                total_correct = len(correct)  
                
                if strict_mode:
                    question_score = 1.0 if selected == correct else 0.0
                else:
                    if incorrect_selected == 0:  
                        question_score = correct_selected / total_correct
                    else:
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
                    "all_selected": False  
                }
                incorrect_questions.append(result_info)
        
        score = (correct_count / questions) * 100
        
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

class MultipleProcessor:
    def __init__(self):
        """
        Инициализация процессора для обработки тестов с одним столбцом.
        """
        pass

    def process_image(self, image: np.ndarray, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка изображения теста с одним столбцом.
        
        Args:
            image (np.ndarray): Входное изображение в формате OpenCV
            config (Dict[str, Any]): Конфигурация теста
                {
                    'questions': int - количество вопросов,
                    'choices': int - количество вариантов ответа,
                    'correct_answers': List[List[int]] - правильные ответы,
                    'strict_mode': bool - строгий режим проверки
                }
        
        Returns:
            Dict[str, Any]: Результаты обработки
                {
                    'processed_image': str - обработанное изображение в формате base64,
                    'correct_count': float - количество правильных ответов,
                    'questions': int - общее количество вопросов,
                    'score': float - процент правильных ответов,
                    'correct_questions': List[int] - номера правильных вопросов,
                    'incorrect_questions': List[Dict] - детали неправильных ответов
                }
        """
        # Получаем параметры
        questions = config['questions']
        choices = config['choices']
        correct_answers = config['correct_answers']
        strict_mode = config['strict_mode']
        image_size = 800

        try:
            # Обрабатываем изображение существующей функцией
            result_img, correct_count, score, incorrect_questions, correct_questions = process_multiple_choice(
                image, questions, choices, correct_answers, image_size, strict_mode=strict_mode
            )

            # Создаем наложение на оригинальное изображение
            overlay_image = self._create_overlay_image(
                image,
                result_img,  # Передаем перспективное изображение для получения матрицы трансформации
                questions,
                choices,
                correct_answers,
                incorrect_questions
            )

            # Определяем целевую высоту для обоих изображений
            target_height = 800  # Фиксированная высота для комфортного просмотра
            
            # Масштабируем перспективное изображение
            perspective_aspect_ratio = result_img.shape[1] / result_img.shape[0]
            perspective_target_width = int(target_height * perspective_aspect_ratio)
            result_image_resized = cv2.resize(result_img, (perspective_target_width, target_height))
            
            # Масштабируем оригинальное изображение
            overlay_aspect_ratio = overlay_image.shape[1] / overlay_image.shape[0]
            overlay_target_width = int(target_height * overlay_aspect_ratio)
            overlay_image_resized = cv2.resize(overlay_image, (overlay_target_width, target_height))
            
            # Объединяем изображения
            final_image = np.hstack((result_image_resized, overlay_image_resized))
            
            # Проверяем, не слишком ли широкое получилось изображение
            max_width = 2000  # Максимальная допустимая ширина
            if final_image.shape[1] > max_width:
                # Если изображение слишком широкое, уменьшаем его, сохраняя пропорции
                scale_factor = max_width / final_image.shape[1]
                new_height = int(final_image.shape[0] * scale_factor)
                final_image = cv2.resize(final_image, (max_width, new_height))

            # Конвертируем результат в base64
            _, buffer = cv2.imencode('.jpg', final_image)
            processed_image = base64.b64encode(buffer).decode('utf-8')

            # Формируем результат в нужном формате
            return {
                'processed_image': f'data:image/jpeg;base64,{processed_image}',
                'correct_count': correct_count,
                'questions': questions,
                'score': score,
                'correct_questions': correct_questions,
                'incorrect_questions': incorrect_questions,
                'strict_mode': strict_mode
            }
        except Exception as e:
            print(f"Ошибка обработки изображения: {str(e)}")
            return {
                'error': str(e),
                'processed_image': None,
                'correct_count': 0,
                'questions': 0,
                'score': 0,
                'correct_questions': [],
                'incorrect_questions': [],
                'strict_mode': strict_mode
            }

    def _create_overlay_image(self, original_image: np.ndarray, perspective_image: np.ndarray,
                            questions: int, choices: int, correct_answers: List[List[int]],
                            incorrect_questions: List[Dict]) -> np.ndarray:
        """
        Создает изображение с наложенными маркерами на оригинальное изображение.
        """
        try:
            # Находим контур области с ответами на оригинальном изображении
            gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 1)
            canny = cv2.Canny(blurred, 10, 70)
            contours = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
            
            # Находим самый большой прямоугольный контур
            rect_contours = [cnt for cnt in contours 
                           if len(cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)) == 4]
            if not rect_contours:
                raise ValueError("Не удалось найти область с ответами")
            
            biggest_contour = max(rect_contours, key=cv2.contourArea)
            
            # Получаем угловые точки
            peri = cv2.arcLength(biggest_contour, True)
            corners = cv2.approxPolyDP(biggest_contour, 0.02 * peri, True)
            corners = reorder(corners)
            
            # Получаем размеры перспективного изображения
            width = perspective_image.shape[1]
            height = perspective_image.shape[0]
            
            # Создаем матрицы трансформации
            pts1 = np.float32(corners)
            pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
            matrix = cv2.getPerspectiveTransform(pts2, pts1)
            
            # Создаем копию оригинального изображения для наложения маркеров
            result = original_image.copy()
            
            # Вычисляем размеры ячеек в перспективном изображении
            cell_width = width / choices
            cell_height = height / questions
            
            # Создаем тестовые точки для определения размера ячейки на оригинальном изображении
            test_points = np.array([
                [[0, 0]],  # Верхний левый угол первой ячейки
                [[cell_width, cell_height]]  # Нижний правый угол первой ячейки
            ], dtype=np.float32)
            
            # Преобразуем тестовые точки в координаты оригинального изображения
            transformed_points = cv2.perspectiveTransform(test_points, matrix)
            
            # Вычисляем реальный размер ячейки на оригинальном изображении
            real_width = abs(transformed_points[1][0][0] - transformed_points[0][0][0])
            real_height = abs(transformed_points[1][0][1] - transformed_points[0][0][1])
            
            # Определяем масштаб для маркеров (50% от размера ячейки)
            marker_scale = 0.5
            scaled_cell_size = (int(real_width * marker_scale), int(real_height * marker_scale))
            
            # Создаем словарь ответов для быстрого доступа
            incorrect_dict = {q['question_number']: q for q in incorrect_questions}
            
            # Для каждого вопроса
            for q in range(questions):
                q_num = q + 1
                
                # Определяем правильные ответы для этого вопроса
                correct = set(correct_answers[q])
                
                # Если вопрос в списке неправильных, получаем выбранные ответы
                if q_num in incorrect_dict:
                    selected = set(x - 1 for x in incorrect_dict[q_num]['selected_answers'])
                    partial_score = incorrect_dict[q_num]['partial_score']
                else:
                    selected = correct
                    partial_score = 1.0
                
                # Для каждого варианта ответа
                for c in range(choices):
                    # Вычисляем координаты центра ячейки в перспективе
                    src_x = (c + 0.5) * cell_width
                    src_y = (q + 0.5) * cell_height
                    
                    # Преобразуем координаты обратно в оригинальное изображение
                    point = cv2.perspectiveTransform(
                        np.array([[[src_x, src_y]]], dtype=np.float32),
                        matrix
                    )[0][0]
                    
                    # Определяем тип маркера
                    if c in selected:
                        if c in correct:
                            if selected == correct:
                                mark_type = 'correct'
                            else:
                                mark_type = 'partial'
                        else:
                            mark_type = 'incorrect'
                    else:
                        if c in correct:
                            mark_type = 'missed'
                        else:
                            mark_type = 'unselected'
                    
                    # Рисуем маркер с масштабированным размером
                    if mark_type != 'unselected':
                        draw_multiple_marks(
                            result,
                            (int(point[0]), int(point[1])),
                            mark_type,
                            scaled_cell_size  # Используем масштабированный размер
                        )
            
            return result
            
        except Exception as e:
            print(f"Ошибка при создании наложения: {str(e)}")
            return original_image.copy() 