import cv2
import numpy as np
import base64
from typing import List, Tuple, Dict, Any

class MultipleColumnsProcessor:
    def __init__(self):
        """
        Инициализация процессора для обработки тестов с двумя столбцами.
        """
        pass

    def process_image(self, image: np.ndarray, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка изображения теста с двумя столбцами.
        
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
        try:
            # Получаем параметры из конфигурации
            questions = config['questions']
            choices = config['choices']
            correct_answers = config['correct_answers']
            strict_mode = config.get('strict_mode', False)  # По умолчанию нестрогий режим
            
            # Предварительная обработка изображения для поиска контуров
            processed_image = self._preprocess_image(image)
            
            # Находим и разделяем столбцы, используя оригинальное изображение
            columns, binary_columns = self._detect_columns(image, processed_image)
            if len(columns) != 2:
                raise ValueError("Не удалось обнаружить два столбца на изображении")
            
            # Сохраняем информацию о прямоугольниках для наложения
            column_rects = self._get_column_rects(processed_image)
            if not column_rects or len(column_rects) < 2:
                raise ValueError("Не удалось найти прямоугольники столбцов")
            
            # Определяем количество вопросов для каждого столбца
            questions_first_column = (questions + 1) // 2  # Округление вверх для первого столбца
            questions_second_column = questions - questions_first_column  # Реальное количество вопросов во втором столбце
            
            # Для визуального отображения во втором столбце используем такое же количество строк как в первом
            display_questions_second_column = questions_first_column
            
            # Проверяем, что у нас достаточно правильных ответов
            if len(correct_answers) < questions:
                raise ValueError(f"Недостаточно правильных ответов. Ожидается {questions}, получено {len(correct_answers)}")
            
            # Обрабатываем левый столбец
            left_answers, left_image = self._process_column(
                columns[0],
                binary_columns[0], 
                0,  # начальный номер вопроса
                {
                    'questions': questions_first_column,
                    'display_questions': questions_first_column,  # то же самое для первого столбца
                    'choices': choices,
                    'correct_answers': correct_answers,
                    'strict_mode': strict_mode
                }
            )
            
            # Обрабатываем правый столбец
            right_answers, right_image = self._process_column(
                columns[1],
                binary_columns[1],
                questions_first_column,
                {
                    'questions': questions_second_column,  # реальное количество вопросов для проверки
                    'display_questions': display_questions_second_column,  # количество вопросов для отображения
                    'choices': choices,
                    'correct_answers': correct_answers,
                    'strict_mode': strict_mode
                }
            )
            
            # Объединяем результаты
            all_answers = left_answers + right_answers
            
            # Подсчитываем правильные ответы и формируем статистику
            correct_count, correct_questions, incorrect_questions = self._check_answers(all_answers, correct_answers, strict_mode)
            
            # Приводим столбцы к одинаковому размеру перед объединением
            max_height = max(left_image.shape[0], right_image.shape[0])
            max_width = max(left_image.shape[1], right_image.shape[1])
            
            left_image_resized = cv2.resize(left_image, (max_width, max_height))
            right_image_resized = cv2.resize(right_image, (max_width, max_height))
            
            # Объединяем изображения столбцов
            result_image = np.hstack((left_image_resized, right_image_resized))
            
            # Создаем наложение на оригинальное изображение
            overlay_image = self._create_overlay_image(
                image,
                left_answers + right_answers,
                correct_answers,
                questions_first_column,
                questions_second_column,
                choices,
                column_rects
            )
            
            # Определяем целевую высоту для обоих изображений (увеличиваем размер)
            target_height = 800  # Фиксированная высота для комфортного просмотра
            
            # Масштабируем перспективное изображение
            perspective_aspect_ratio = result_image.shape[1] / result_image.shape[0]
            perspective_target_width = int(target_height * perspective_aspect_ratio)
            result_image_resized = cv2.resize(result_image, (perspective_target_width, target_height))
            
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
            processed_image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Формируем итоговый результат
            return {
                'processed_image': f'data:image/jpeg;base64,{processed_image_base64}',
                'correct_count': correct_count,
                'questions': questions,
                'score': (correct_count / questions) * 100,
                'correct_questions': correct_questions,
                'incorrect_questions': incorrect_questions,
                'strict_mode': strict_mode
            }
            
        except Exception as e:
            print(f"Ошибка обработки изображения: {str(e)}")
            # Возвращаем ошибку в формате, который ожидает фронтенд
            return {
                'error': str(e),
                'processed_image': None,
                'correct_count': 0,
                'questions': 0,
                'score': 0,
                'correct_questions': [],
                'incorrect_questions': [],
                'strict_mode': config.get('strict_mode', False)
            }

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Предварительная обработка изображения.
        
        Args:
            image (np.ndarray): Исходное изображение
            
        Returns:
            np.ndarray: Обработанное изображение
        """
        # Преобразуем в оттенки серого
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Применяем размытие по Гауссу для уменьшения шума
        blurred = cv2.GaussianBlur(gray, (5, 5), 1)
        
        # Применяем глобальную бинаризацию методом Оцу
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Применяем морфологические операции для улучшения результата
        kernel = np.ones((3, 3), np.uint8)
        # Сначала закрываем (чтобы соединить близкие части)
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        # Затем открываем (чтобы убрать мелкий шум)
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
        
        return morph

    def _detect_columns(self, original_image: np.ndarray, binary_image: np.ndarray) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Обнаружение и разделение столбцов на изображении.
        
        Args:
            original_image (np.ndarray): Оригинальное цветное изображение
            binary_image (np.ndarray): Бинаризованное изображение для поиска контуров
            
        Returns:
            Tuple[List[np.ndarray], List[np.ndarray]]: 
                - Список цветных изображений столбцов [левый, правый]
                - Список бинарных изображений столбцов [левый, правый]
        """
        # Находим контуры на бинарном изображении
        contours, _ = cv2.findContours(
            binary_image.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Находим два самых больших контура
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:2]
        if len(contours) < 2:
            raise ValueError("Не удалось найти два контура на изображении")
            
        # Проверяем, что контуры примерно одинакового размера
        area1 = cv2.contourArea(contours[0])
        area2 = cv2.contourArea(contours[1])
        if min(area1, area2) / max(area1, area2) < 0.8:  # допускаем 20% разницу
            raise ValueError("Контуры значительно отличаются по размеру")
            
        # Получаем ограничивающие прямоугольники для контуров
        rects = []
        for contour in contours:
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.array(box, dtype=np.int_)
            rects.append((box, rect))
            
        # Сортируем контуры по x-координате (слева направо)
        rects.sort(key=lambda r: np.min(r[0][:, 0]))
        
        # Получаем перспективное преобразование для каждого контура
        color_columns = []
        binary_columns = []
        for box, rect in rects:
            # Получаем ширину и высоту прямоугольника
            width = int(rect[1][0])
            height = int(rect[1][1])
            
            # Если прямоугольник повернут более чем на 45 градусов,
            # меняем местами ширину и высоту
            if rect[2] < -45:
                width, height = height, width
                
            # Определяем исходные точки
            src_pts = box.astype("float32")
            
            # Сортируем точки для корректного преобразования
            src_pts = self._order_points(src_pts)
            
            # Определяем целевые точки
            dst_pts = np.array([
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1]
            ], dtype="float32")
            
            # Получаем матрицу преобразования
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            
            # Применяем преобразование к оригинальному и бинарному изображениям
            warped_color = cv2.warpPerspective(original_image, M, (width, height))
            warped_binary = cv2.warpPerspective(binary_image, M, (width, height))
            
            color_columns.append(warped_color)
            binary_columns.append(warped_binary)
            
        return color_columns, binary_columns

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        Упорядочивает точки в порядке: верхний левый, верхний правый,
        нижний правый, нижний левый.
        """
        rect = np.zeros((4, 2), dtype="float32")
        
        # Верхняя левая точка будет иметь наименьшую сумму
        # Нижняя правая точка будет иметь наибольшую сумму
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Верхняя правая точка будет иметь наименьшую разность
        # Нижняя левая точка будет иметь наибольшую разность
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect

    def draw_multiple_marks(self, img: np.ndarray, position: Tuple[int, int], mark_type: str, cell_size: Tuple[int, int]):
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

    def showMultipleAnswers(self, img: np.ndarray, selected_answers: List[List[int]], correct_answers: List[List[int]], 
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
                
                self.draw_multiple_marks(img, pos, mark_type, cell_size)

    def _process_column(self, color_column: np.ndarray, binary_column: np.ndarray, 
                       start_question: int, config: Dict[str, Any]) -> Tuple[List[List[int]], np.ndarray]:
        """
        Обработка отдельного столбца с вопросами.
        
        Args:
            color_column (np.ndarray): Цветное изображение столбца
            binary_column (np.ndarray): Бинарное изображение столбца
            start_question (int): Начальный номер вопроса в столбце
            config (Dict[str, Any]): Конфигурация теста
            
        Returns:
            Tuple[List[List[int]], np.ndarray]: Обнаруженные ответы и размеченное изображение
        """
        questions = config['questions']  # реальное количество вопросов для проверки
        display_questions = config['display_questions']  # количество вопросов для отображения
        choices = config['choices']
        correct_answers = config['correct_answers']
        
        # Проверяем, что у нас достаточно правильных ответов для этого столбца
        if start_question + questions > len(correct_answers):
            raise ValueError(f"Недостаточно правильных ответов для вопросов {start_question + 1} - {start_question + questions}")
        
        # Используем цветное изображение как основу для отрисовки результатов
        result_image = color_column.copy()
        
        # Разделяем изображение на ячейки с вопросами, используя display_questions для визуального отображения
        cell_height = binary_column.shape[0] // display_questions
        cell_width = binary_column.shape[1] // choices
        
        # Список для хранения обнаруженных ответов
        detected_answers = []
        
        # Обрабатываем только реальные вопросы
        for q in range(questions):
            # Вырезаем область вопроса
            y_start = q * cell_height
            y_end = (q + 1) * cell_height
            question_area = binary_column[y_start:y_end, :]
            
            # Находим отмеченные ответы в вопросе
            answers = []
            pixel_values = []
            
            # Первый проход - собираем значения пикселей
            for c in range(choices):
                x_start = c * cell_width
                x_end = (c + 1) * cell_width
                margin = 5
                cell = question_area[margin:cell_height-margin, x_start+margin:x_end-margin]
                
                # Вычисляем процент закрашенных пикселей
                total_pixels = cell.size
                black_pixels = cv2.countNonZero(cell)
                pixel_ratio = black_pixels / total_pixels
                pixel_values.append(pixel_ratio)
            
            # Находим максимальное значение
            max_ratio = max(pixel_values) if pixel_values else 0
            
            if max_ratio > 0:  # Если есть хоть какие-то отметки
                # Используем порог 50% от максимального значения для первичного отбора
                threshold = max_ratio * 0.5
                answers = [j for j, val in enumerate(pixel_values) if val > threshold]
                
                if len(answers) > 0:
                    # Применяем второй порог 80% для отфильтровывания слабо отмеченных ответов
                    max_in_selected = max(pixel_values[j] for j in answers)
                    answers = [j for j in answers if pixel_values[j] > max_in_selected * 0.8]
            
            detected_answers.append(answers)
        
        # Получаем правильные ответы для текущего столбца
        column_correct_answers = correct_answers[start_question:start_question + questions]
        
        # Для отображения результатов добавляем пустые ответы, если нужно
        display_detected_answers = detected_answers + [[] for _ in range(display_questions - questions)]
        display_correct_answers = column_correct_answers + [[] for _ in range(display_questions - questions)]
        
        # Отрисовываем результаты используя новую функцию
        self.showMultipleAnswers(result_image, display_detected_answers, display_correct_answers, 
                               display_questions, choices)
        
        # Отрисовываем сетку
        for q in range(display_questions + 1):
            y = q * cell_height
            cv2.line(result_image, (0, y), (binary_column.shape[1], y), (255, 79, 0), 2)
        
        for c in range(choices + 1):
            x = c * cell_width
            cv2.line(result_image, (x, 0), (x, binary_column.shape[0]), (255, 79, 0), 2)
        
        return detected_answers, result_image

    def _check_answers(self, detected_answers: List[List[int]], 
                      correct_answers: List[List[int]], 
                      strict_mode: bool) -> Tuple[float, List[int], List[Dict]]:
        """
        Проверка ответов и подсчет результатов.
        """
        correct_count = 0
        correct_questions = []
        incorrect_questions = []
        choices = 5  # Количество вариантов ответа
        
        for i, (detected, correct) in enumerate(zip(detected_answers, correct_answers)):
            selected = set(detected)
            correct_set = set(correct)
            
            # Проверяем случай, когда отмечено слишком много вариантов
            if len(selected) >= int(choices * 0.8):  # 80% или более вариантов
                incorrect_questions.append({
                    'question_number': i + 1,
                    'message': "❌ Выбрано слишком много вариантов ответа - вопрос не засчитан",
                    'selected_answers': [x + 1 for x in detected],
                    'correct_answers': [x + 1 for x in correct],
                    'partial_score': 0.0,
                    'correct_selected': 0,
                    'total_correct': len(correct_set),
                    'incorrect_selected': len(selected),
                    'all_selected': True
                })
                continue

            if len(correct_set) > 0:
                correct_selected = len(selected & correct_set)  # Количество правильно отмеченных
                incorrect_selected = len(selected - correct_set)  # Количество неправильно отмеченных
                total_correct = len(correct_set)  # Общее количество правильных ответов
                
                if strict_mode:
                    # В строгом режиме ответ считается правильным только при полном совпадении
                    question_score = 1.0 if selected == correct_set else 0.0
                else:
                    # В нестрогом режиме учитываем частично правильные ответы
                    if incorrect_selected == 0:  # Если нет неправильных ответов
                        question_score = correct_selected / total_correct
                    else:
                        # Штраф за неправильные ответы
                        question_score = max(0, (correct_selected - incorrect_selected) / total_correct)
            else:
                # Если правильных ответов нет, то ответ верен только если ничего не выбрано
                question_score = 1 if len(selected) == 0 else 0
                correct_selected = 0
                incorrect_selected = len(selected)
                total_correct = 0

            correct_count += question_score
            
            if question_score == 1:
                correct_questions.append(i + 1)
            else:
                # Формируем сообщение об ошибке
                base_message = f"- выбраны варианты: {', '.join(str(x + 1) for x in sorted(detected))}"
                if correct:
                    base_message += f"\n- правильные варианты: {', '.join(str(x + 1) for x in sorted(correct))}"
                else:
                    base_message += "\n- правильные варианты: нет"
                    
                if question_score > 0:
                    score_percent = int(question_score * 100)
                    message = f"{base_message}\n✓ Частично правильный ответ ({score_percent}%)"
                else:
                    message = base_message
                
                incorrect_questions.append({
                    'question_number': i + 1,
                    'message': message,
                    'selected_answers': [x + 1 for x in detected],
                    'correct_answers': [x + 1 for x in correct],
                    'partial_score': question_score,
                    'correct_selected': correct_selected,
                    'total_correct': total_correct,
                    'incorrect_selected': incorrect_selected,
                    'all_selected': False
                })
        
        return correct_count, correct_questions, incorrect_questions 

    def _create_overlay_image(self, original_image: np.ndarray, detected_answers: List[List[int]], 
                            correct_answers: List[List[int]], questions_first: int, 
                            questions_second: int, choices: int, rects: List[Tuple]) -> np.ndarray:
        """
        Создает изображение с наложенными маркерами на оригинальное изображение.
        """
        try:
            if original_image is None:
                raise ValueError("Оригинальное изображение не может быть None")
                
            if len(rects) < 2:
                raise ValueError("Недостаточно прямоугольников для обработки")
                
            result = original_image.copy()
            
            # Обрабатываем каждый столбец
            for col_idx, (box, rect) in enumerate(rects):
                # Определяем количество вопросов для текущего столбца
                # Для отображения используем одинаковое количество вопросов в обоих столбцах
                display_questions = questions_first  # Всегда используем количество вопросов первого столбца для отображения
                real_questions = questions_first if col_idx == 0 else questions_second  # Реальное количество вопросов для проверки
                start_idx = questions_first if col_idx == 1 else 0
                
                # Получаем размеры ячейки в перспективе
                width = int(rect[1][0])
                height = int(rect[1][1])
                if rect[2] < -45:
                    width, height = height, width
                    
                # Используем display_questions для вычисления размера ячейки
                cell_height = height / display_questions
                cell_width = width / choices
                
                # Получаем матрицу перспективы
                src_pts = self._order_points(box.astype("float32"))
                dst_pts = np.array([
                    [0, 0],
                    [width - 1, 0],
                    [width - 1, height - 1],
                    [0, height - 1]
                ], dtype="float32")
                
                # Для каждого вопроса в столбце обрабатываем только реальные вопросы
                for q in range(real_questions):
                    q_idx = q + start_idx
                    detected = set(detected_answers[q_idx])
                    correct = set(correct_answers[q_idx])
                    
                    # Для каждого варианта ответа
                    for c in range(choices):
                        # Вычисляем координаты центра ячейки в перспективе
                        src_x = (c + 0.5) * cell_width
                        src_y = (q + 0.5) * cell_height
                        
                        # Преобразуем координаты обратно в оригинальное изображение
                        M = cv2.getPerspectiveTransform(dst_pts, src_pts)
                        point = cv2.perspectiveTransform(
                            np.array([[[src_x, src_y]]], dtype=np.float32),
                            M
                        )[0][0]
                        
                        # Определяем тип маркера
                        if c in detected:
                            if c in correct:
                                if detected == correct:
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
                        
                        # Рисуем маркер
                        if mark_type != 'unselected':
                            cell_size = (int(cell_width), int(cell_height))
                            self.draw_multiple_marks(
                                result,
                                (int(point[0]), int(point[1])),
                                mark_type,
                                cell_size
                            )
            
            return result
            
        except Exception as e:
            print(f"Ошибка при создании наложения: {str(e)}")
            # В случае ошибки возвращаем оригинальное изображение без наложений
            return original_image.copy()

    def _get_column_rects(self, binary_image: np.ndarray) -> List[Tuple]:
        """
        Получает информацию о прямоугольниках столбцов.
        """
        contours, _ = cv2.findContours(
            binary_image.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Находим два самых больших контура
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:2]
        
        # Получаем ограничивающие прямоугольники
        rects = []
        for contour in contours:
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.array(box, dtype=np.int_)
            rects.append((box, rect))
            
        # Сортируем по x-координате
        rects.sort(key=lambda r: np.min(r[0][:, 0]))
        
        return rects 