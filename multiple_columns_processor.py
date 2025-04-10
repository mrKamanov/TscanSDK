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
            strict_mode = config.get('strict_mode', False)
            
            # Увеличиваем разрешение входного изображения
            height, width = image.shape[:2]
            target_height = 3600  # Увеличиваем целевую высоту для лучшего качества
            scale_factor = target_height / height
            target_width = int(width * scale_factor)
            
            # Проверяем, не слишком ли большое получится изображение
            max_width = 4800  # Увеличиваем максимальную ширину
            if target_width > max_width:
                scale_factor = max_width / width
                target_height = int(height * scale_factor)
                target_width = max_width
            
            # Используем INTER_CUBIC для лучшего качества при увеличении
            image = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
            
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
            questions_first_column = (questions + 1) // 2
            questions_second_column = questions - questions_first_column
            
            # Для визуального отображения во втором столбце используем такое же количество строк как в первом
            display_questions_second_column = questions_first_column
            
            # Проверяем, что у нас достаточно правильных ответов
            if len(correct_answers) < questions:
                raise ValueError(f"Недостаточно правильных ответов. Ожидается {questions}, получено {len(correct_answers)}")
            
            # Обрабатываем левый столбец
            left_answers, _ = self._process_column(
                columns[0],
                binary_columns[0], 
                0,
                {
                    'questions': questions_first_column,
                    'display_questions': questions_first_column,
                    'choices': choices,
                    'correct_answers': correct_answers,
                    'strict_mode': strict_mode
                }
            )
            
            # Обрабатываем правый столбец
            right_answers, _ = self._process_column(
                columns[1],
                binary_columns[1],
                questions_first_column,
                {
                    'questions': questions_second_column,
                    'display_questions': display_questions_second_column,
                    'choices': choices,
                    'correct_answers': correct_answers,
                    'strict_mode': strict_mode
                }
            )
            
            # Объединяем результаты
            all_answers = left_answers + right_answers
            
            # Подсчитываем правильные ответы и формируем статистику
            correct_count, correct_questions, incorrect_questions = self._check_answers(all_answers, correct_answers, strict_mode)
            
            # Создаем наложение на оригинальное изображение
            overlay_image = self._create_overlay_image(
                image,
                all_answers,
                correct_answers,
                questions_first_column,
                questions_second_column,
                choices,
                column_rects
            )
            
            # Отрисовываем сетку на финальном изображении
            for rect, start_q, num_q in zip(column_rects, [0, questions_first_column], 
                                          [questions_first_column, questions_second_column]):
                box, _ = rect
                # Получаем точки прямоугольника
                pts = self._order_points(box)
                
                # Вычисляем размеры ячеек
                width = int(np.linalg.norm(pts[1] - pts[0]))
                height = int(np.linalg.norm(pts[3] - pts[0]))
                cell_width = width // choices
                cell_height = height // questions_first_column
                
                # Рисуем горизонтальные линии
                for i in range(questions_first_column + 1):
                    y_ratio = i / questions_first_column
                    pt1 = pts[0] * (1 - y_ratio) + pts[3] * y_ratio
                    pt2 = pts[1] * (1 - y_ratio) + pts[2] * y_ratio
                    pt1 = tuple(map(int, pt1))
                    pt2 = tuple(map(int, pt2))
                    cv2.line(overlay_image, pt1, pt2, (0, 0, 255), 2)
                    
                    # Добавляем номера вопросов
                    if i < questions_first_column:
                        question_num = start_q + i + 1
                        text_pos = (int(pt1[0]) - 30, int(pt1[1] + cell_height//2))
                        # Белый фон для текста
                        text_size = cv2.getTextSize(str(question_num), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                        cv2.rectangle(overlay_image,
                                    (text_pos[0], text_pos[1] - text_size[1] - 5),
                                    (text_pos[0] + text_size[0] + 10, text_pos[1] + 5),
                                    (255, 255, 255), -1)
                        cv2.putText(overlay_image, str(question_num), text_pos,
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Рисуем вертикальные линии
                for i in range(choices + 1):
                    x_ratio = i / choices
                    pt1 = pts[0] * (1 - x_ratio) + pts[1] * x_ratio
                    pt2 = pts[3] * (1 - x_ratio) + pts[2] * x_ratio
                    pt1 = tuple(map(int, pt1))
                    pt2 = tuple(map(int, pt2))
                    cv2.line(overlay_image, pt1, pt2, (255, 0, 0), 2)
                    
                    # Добавляем номера вариантов ответов
                    if i < choices:
                        text_pos = (int(pt1[0] + cell_width//2), int(pt1[1]) - 10)
                        # Белый фон для текста
                        text_size = cv2.getTextSize(str(i+1), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                        cv2.rectangle(overlay_image,
                                    (text_pos[0] - text_size[0]//2 - 5, text_pos[1] - text_size[1] - 5),
                                    (text_pos[0] + text_size[0]//2 + 5, text_pos[1] + 5),
                                    (255, 255, 255), -1)
                        cv2.putText(overlay_image, str(i+1), text_pos,
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Масштабируем финальное изображение для отображения
            target_height = 1200
            aspect_ratio = overlay_image.shape[1] / overlay_image.shape[0]
            target_width = int(target_height * aspect_ratio)
            
            # Проверяем, не слишком ли широкое получилось изображение
            max_width = 2000
            if target_width > max_width:
                scale_factor = max_width / target_width
                target_height = int(target_height * scale_factor)
                target_width = max_width
            
            final_image = cv2.resize(overlay_image, (target_width, target_height))
            
            # Конвертируем результат в base64
            _, buffer = cv2.imencode('.jpg', final_image)
            processed_image_base64 = base64.b64encode(buffer).decode('utf-8')
            
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
        Предварительная обработка изображения для улучшения качества распознавания.
        
        Args:
            image (np.ndarray): Исходное изображение
            
        Returns:
            np.ndarray: Обработанное изображение
        """
        try:
            # Преобразуем в оттенки серого
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Применяем адаптивное размытие по Гауссу
            kernel_size = max(3, min(gray.shape) // 300)  # Уменьшаем делитель для более точного размытия
            if kernel_size % 2 == 0:
                kernel_size += 1
            blurred = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
            
            # Применяем адаптивную пороговую обработку
            binary = cv2.adaptiveThreshold(
                blurred,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                11,
                2
            )
            
            # Применяем морфологические операции для удаления шума
            kernel = np.ones((2, 2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return binary
            
        except Exception as e:
            print(f"Ошибка при предварительной обработке изображения: {str(e)}")
            return image

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
        
        # Увеличиваем размер маркеров
        mark_size = min(cellW, cellH) // 2  # Было // 3, делаем больше
        thickness = max(3, min(cellW, cellH) // 15)  # Увеличиваем толщину линий
        circle_radius = mark_size + thickness
        
        colors = {
            'correct': {  
                'fill': (0, 255, 0),  # Зеленый
                'border': (0, 200, 0),
                'mark': (255, 255, 255)
            },
            'partial': {  
                'fill': (255, 165, 0),  # Оранжевый
                'border': (200, 130, 0),
                'mark': (255, 255, 255)
            },
            'incorrect': {  
                'fill': (0, 0, 255),  # Меняем на синий для лучшей видимости
                'border': (0, 0, 200),
                'mark': (255, 255, 255)
            },
            'missed': {  
                'fill': (255, 0, 0),  # Красный для пропущенных
                'border': (200, 0, 0),
                'mark': (255, 255, 255)
            }
        }
        
        if mark_type == 'unselected':
            return
        
        color = colors[mark_type]
        
        # Рисуем круг с более толстой обводкой
        cv2.circle(img, (cX, cY), circle_radius + 2, color['border'], -1)  # Внешняя обводка
        cv2.circle(img, (cX, cY), circle_radius, color['fill'], -1)  # Заливка
        
        if mark_type in ['correct', 'partial']:
            # Увеличенная галочка
            points = np.array([
                [cX - mark_size, cY],
                [cX - mark_size//3, cY + mark_size//2],
                [cX + mark_size, cY - mark_size//2]
            ])
            cv2.polylines(img, [points], isClosed=False, color=(0, 0, 0), thickness=thickness*2)
            cv2.polylines(img, [points], isClosed=False, color=color['mark'], thickness=thickness)
        elif mark_type == 'incorrect':
            # Увеличенный крестик
            offset = mark_size // 2
            cv2.line(img, 
                    (cX - offset, cY - offset),
                    (cX + offset, cY + offset),
                    (0, 0, 0), thickness*2)
            cv2.line(img,
                    (cX - offset, cY + offset),
                    (cX + offset, cY - offset),
                    (0, 0, 0), thickness*2)
            cv2.line(img,
                    (cX - offset, cY - offset),
                    (cX + offset, cY + offset),
                    color['mark'], thickness)
            cv2.line(img,
                    (cX - offset, cY + offset),
                    (cX + offset, cY - offset),
                    color['mark'], thickness)
        elif mark_type == 'missed':
            # Увеличенный кружок для пропущенных
            inner_radius = mark_size//2
            cv2.circle(img, (cX, cY), inner_radius + 2, (0, 0, 0), -1)
            cv2.circle(img, (cX, cY), inner_radius, color['mark'], thickness)

    def showMultipleAnswers(self, img: np.ndarray, selected_answers: List[List[int]], correct_answers: List[List[int]], 
                           questions: int = 5, choices: int = 5) -> None:
        # Находим контур области с ответами
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        if not contours:
            return
        
        # Находим самый большой контур
        biggest_contour = max(contours, key=cv2.contourArea)
        
        # Получаем угловые точки
        peri = cv2.arcLength(biggest_contour, True)
        pts = cv2.approxPolyDP(biggest_contour, 0.02 * peri, True)
        pts = self._order_points(pts.reshape(4, 2))
        
        # Вычисляем размеры с учетом перспективы
        width = int(np.linalg.norm(pts[1] - pts[0]))
        height = int(np.linalg.norm(pts[3] - pts[0]))
        
        # Вычисляем размеры ячеек
        cell_width = width // choices
        cell_height = height // questions
        
        # Определяем масштаб для маркеров (50% от размера ячейки)
        marker_scale = 0.5
        cell_size = (int(cell_width * marker_scale), int(cell_height * marker_scale))
        
        for q in range(questions):
            selected = set(selected_answers[q])
            correct = set(correct_answers[q])
            
            for c in range(choices):
                # Вычисляем позицию с учетом перспективы
                x_ratio = (c + 0.5) / choices
                y_ratio = (q + 0.5) / questions
                
                # Интерполируем точки для получения позиции центра ячейки
                top_point = pts[0] * (1 - x_ratio) + pts[1] * x_ratio
                bottom_point = pts[3] * (1 - x_ratio) + pts[2] * x_ratio
                center_point = top_point * (1 - y_ratio) + bottom_point * y_ratio
                
                pos = (int(center_point[0]), int(center_point[1]))
                
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
                
                self.draw_multiple_marks(img, pos, mark_type, cell_size)

    def _process_column(self, color_column: np.ndarray, binary_column: np.ndarray, 
                       start_question: int, config: Dict[str, Any]) -> Tuple[List[List[int]], np.ndarray]:
        try:
            questions = config['questions']
            display_questions = config['display_questions']
            choices = config['choices']
            correct_answers = config['correct_answers']
            
            # Используем цветное изображение как основу для отрисовки результатов
            result_image = color_column.copy()
            
            # Преобразуем цветное изображение в оттенки серого
            gray_column = cv2.cvtColor(color_column, cv2.COLOR_BGR2GRAY)
            
            # Применяем адаптивную бинаризацию для лучшего выделения отметок
            thresh = cv2.adaptiveThreshold(
                gray_column,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                21,  # Размер окна для адаптивной бинаризации
                5    # Константа вычитания
            )
            
            # Применяем морфологические операции для уменьшения шума
            kernel = np.ones((2, 2), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Простое разделение на ячейки
            height, width = gray_column.shape[:2]
            cell_height = height // display_questions
            cell_width = width // choices
            
            # Обработка ответов
            detected_answers = []
            
            for q in range(questions):
                y_start = q * cell_height
                y_end = (q + 1) * cell_height
                question_area = thresh[y_start:y_end, :]
                
                answers = []
                cell_areas = []
                
                for c in range(choices):
                    x_start = c * cell_width
                    x_end = (c + 1) * cell_width
                    
                    # Определяем область ячейки с отступами
                    margin_x = int(cell_width * 0.2)   # Увеличиваем отступ
                    margin_y = int(cell_height * 0.2)  # Увеличиваем отступ
                    
                    cell = question_area[margin_y:cell_height-margin_y, 
                                      x_start+margin_x:x_end-margin_x]
                    
                    if cell.size == 0:
                        cell_areas.append(0)
                        continue
                    
                    # Находим все связные компоненты в ячейке
                    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cell, 8, cv2.CV_32S)
                    
                    if num_labels > 1:
                        # Фильтруем компоненты по размеру
                        areas = stats[1:, cv2.CC_STAT_AREA]  # Исключаем фон
                        if len(areas) > 0:
                            # Находим самую большую компоненту
                            max_area = max(areas)
                            # Проверяем соотношение размера компоненты к размеру ячейки
                            cell_area = cell.shape[0] * cell.shape[1]
                            area_ratio = max_area / cell_area
                            
                            if 0.1 < area_ratio < 0.9:  # Допустимый диапазон размеров отметки
                                cell_areas.append(max_area)
                            else:
                                cell_areas.append(0)
                        else:
                            cell_areas.append(0)
                    else:
                        cell_areas.append(0)
                
                # Находим максимальную площадь
                max_area = max(cell_areas) if cell_areas else 0
                
                if max_area > 50:  # Уменьшаем минимальный размер для отметки
                    # Находим все отметки, которые достаточно близки к максимальной площади
                    threshold = max_area * 0.4  # Уменьшаем порог для определения отметки
                    potential_answers = [j for j, area in enumerate(cell_areas) if area > threshold]
                    
                    if len(potential_answers) > 0:
                        # Если есть несколько отметок, проверяем их относительный размер
                        if len(potential_answers) > 1:
                            max_size = max(cell_areas[j] for j in potential_answers)
                            # Оставляем только те отметки, которые достаточно близки к максимальной
                            answers = [j for j in potential_answers if cell_areas[j] > max_size * 0.6]  # Уменьшаем порог
                        else:
                            answers = potential_answers
                
                detected_answers.append(answers)
            
            column_correct_answers = correct_answers[start_question:start_question + questions]
            display_detected_answers = detected_answers + [[] for _ in range(display_questions - questions)]
            display_correct_answers = column_correct_answers + [[] for _ in range(display_questions - questions)]
            
            # Отрисовываем маркеры
            self.showMultipleAnswers(result_image, display_detected_answers, display_correct_answers, 
                                   display_questions, choices)
            
            return detected_answers, result_image
            
        except Exception as e:
            print(f"Ошибка при обработке столбца: {str(e)}")
            return [[] for _ in range(questions)], color_column.copy()

    def _check_answers(self, detected_answers: List[List[int]], correct_answers: List[List[int]], strict_mode: bool) -> Tuple[int, List[int], List[Dict]]:
        """
        Проверяет ответы и подсчитывает статистику.
        
        Args:
            detected_answers: Обнаруженные ответы
            correct_answers: Правильные ответы
            strict_mode: Строгий режим проверки
            
        Returns:
            Tuple[int, List[int], List[Dict]]: (количество правильных ответов, 
                                               список номеров правильно отвеченных вопросов,
                                               список с деталями неправильных ответов)
        """
        try:
            correct_count = 0
            correct_questions = []
            incorrect_questions = []
            choices = 5  # Количество вариантов ответа
            
            for i, (detected, correct) in enumerate(zip(detected_answers, correct_answers)):
                selected_set = set(detected)
                correct_set = set(correct)
                
                # Проверяем случай, когда отмечено слишком много вариантов
                # Но только если отмеченные ответы не совпадают с правильными
                if selected_set != correct_set and len(detected) >= int(choices * 0.8):
                    incorrect_info = {
                        'question_number': i + 1,
                        'selected_answers': [x + 1 for x in sorted(detected)],
                        'correct_answers': [x + 1 for x in sorted(correct)],
                        'partial_score': 0.0,
                        'message': f'<div class="warning-message">❌ Выбраны все варианты ответов - вопрос не засчитан</div>',
                        'all_selected': True
                    }
                    incorrect_questions.append(incorrect_info)
                    continue

                # Проверяем случай, когда выбрано слишком много ответов относительно правильного количества
                if len(detected) > len(correct) * 2:  # Если выбрано более чем в 2 раза больше ответов
                    incorrect_info = {
                        'question_number': i + 1,
                        'selected_answers': [x + 1 for x in sorted(detected)],
                        'correct_answers': [x + 1 for x in sorted(correct)],
                        'partial_score': 0.0,
                        'message': f'<div class="warning-message">❌ Выбрано слишком много вариантов ответов ({len(detected)} при {len(correct)} правильных) - вопрос не засчитан</div>',
                        'all_selected': True
                    }
                    incorrect_questions.append(incorrect_info)
                    continue

                # Подсчитываем количество правильных ответов
                correct_selected = len(selected_set & correct_set)  # Пересечение множеств
                total_correct = len(correct_set)
                
                if strict_mode:
                    # В строгом режиме любая ошибка обнуляет балл за вопрос
                    if len(selected_set - correct_set) == 0 and correct_selected == total_correct:
                        question_score = 1.0
                    else:
                        question_score = 0.0
                else:
                    # В нестрогом режиме балл = количество правильных ответов / общее количество правильных ответов
                    question_score = correct_selected / total_correct if total_correct > 0 else 1.0
                
                # Обновляем статистику
                correct_count += question_score
                
                if question_score == 1.0:
                    correct_questions.append(i + 1)
                else:
                    # Формируем сообщение об ошибке
                    base_message = f"Выбранные варианты: {', '.join(str(x + 1) for x in sorted(detected))}"
                    if correct:
                        base_message += f"\nПравильные варианты: {', '.join(str(x + 1) for x in sorted(correct))}"
                    else:
                        base_message += "\nПравильные варианты: нет"
                    
                    if question_score > 0:
                        score_percent = int(question_score * 100)
                        message = f"{base_message}\n✓ Частично правильный ответ ({score_percent}%)"
                    else:
                        message = base_message
                    
                    incorrect_info = {
                        'question_number': i + 1,
                        'selected_answers': [x + 1 for x in sorted(detected)],
                        'correct_answers': [x + 1 for x in sorted(correct)],
                        'partial_score': question_score,
                        'message': message,
                        'all_selected': False
                    }
                    incorrect_questions.append(incorrect_info)
            
            return int(round(correct_count)), correct_questions, incorrect_questions
            
        except Exception as e:
            print(f"Ошибка при проверке ответов: {str(e)}")
            return 0, [], [{'question_number': 0, 'selected_answers': [], 'correct_answers': [], 
                          'partial_score': 0.0, 'message': f"Ошибка при проверке: {str(e)}"}]

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