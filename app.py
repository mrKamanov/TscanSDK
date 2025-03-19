from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import cv2
import base64
import threading
from video_processing import process_video_frame
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

# Значения по умолчанию
questions = 1
choices = 1
correct_answers = [1]
image_size = 700
report_list = []
last_grading = []
last_incorrect_questions = []
grading_criteria = {
    5: [90, 100],
    4: [70, 89],
    3: [50, 69],
    2: [0, 49]
}
# Значения по умолчанию для параметров обработки изображения
brightness = 0
contrast = 1
saturation = 1
sharpness = 1

cap = None
is_paused = False
original_paused_frame = None
paused_frame = None
paused_result = None
overlay_mode = False  # Переменная для режима отображения
camera_thread = None

def start_camera():
    global cap, camera_thread
    try:
        if cap is None:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Добавляем CAP_DSHOW для Windows
            if not cap.isOpened():
                print("Ошибка: Камера не найдена")
                return False
            
            # Базовые настройки камеры
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Настройки цвета и качества
            cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)
            cap.set(cv2.CAP_PROP_CONTRAST, 128)
            cap.set(cv2.CAP_PROP_SATURATION, 128)
            cap.set(cv2.CAP_PROP_AUTO_WB, 1)
            
            # Запускаем поток для чтения кадров
            camera_thread = threading.Thread(target=process_camera_frames)
            camera_thread.daemon = True
            camera_thread.start()
            
            return True
    except Exception as e:
        print(f"Ошибка при инициализации камеры: {str(e)}")
        if cap is not None:
            cap.release()
            cap = None
        return False
    return False

def process_camera_frames():
    global cap, is_paused, original_paused_frame, paused_frame
    while cap is not None and cap.isOpened():
        try:
            if not is_paused:
                ret, frame = cap.read()
                if not ret:
                    print("Ошибка чтения кадра")
                    continue
                
                # Обработка кадра
                processed_frame, correct_count, score, incorrect_questions, grading = process_video_frame(
                    frame, questions, choices, correct_answers, image_size,
                    overlay_mode, brightness, contrast, saturation, sharpness
                )
                
                # Конвертация в JPEG
                _, buffer = cv2.imencode('.jpg', processed_frame)
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Отправка кадра клиенту
                socketio.emit('frame', {
                    'image': image_base64,
                    'result': f"{correct_count}/{questions} ({score:.1f}%)"
                })
                
        except Exception as e:
            print(f"Ошибка обработки кадра: {str(e)}")
            continue

# Главная страница (меню)
@app.route('/')
def main():
    return render_template('main.html')

# Страница сканирования в реальном времени
@app.route('/scan')
def scan():
    return render_template('scan.html', questions=questions, choices=choices)

# Страница пакетной обработки
@app.route('/batch')
def batch():
    return render_template('batch_scan.html', questions=questions, choices=choices)

# Страница отчетов
@app.route('/reports')
def reports():
    return render_template('reports.html', report_list=report_list, questions=questions)

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/constructor')
def constructor():
    return render_template('constructor.html')

@socketio.on('start_camera')
def handle_start_camera():
    success = start_camera()
    if success:
        emit('camera_status', {'status': 'success', 'message': 'Камера успешно запущена'})
    else:
        emit('camera_status', {'status': 'error', 'message': 'Ошибка при запуске камеры'})

@socketio.on('stop_camera')
def handle_stop_camera():
    global cap
    if cap is not None:
        cap.release()
        cap = None
        emit('camera_status', {'status': 'success', 'message': 'Камера остановлена'})

@socketio.on('toggle_pause')
def handle_toggle_pause():
    global is_paused, original_paused_frame, paused_frame, paused_result, last_grading, last_incorrect_questions
    is_paused = not is_paused
    if is_paused:
        success, frame = cap.read()
        if success:
            original_paused_frame = frame  # Сохраняем оригинальный кадр
            result, correct_answers_count, score, incorrect_questions, grading = process_video_frame(
                frame, questions, choices, correct_answers, image_size, overlay_mode
            )
            global last_grading, last_incorrect_questions
            last_grading = [int(g) for g in grading]  # Преобразуем grading в список стандартных целых чисел
            last_incorrect_questions = incorrect_questions  # Сохраняем список неправильных ответов
            paused_frame = result
            paused_result = f"{correct_answers_count}/{questions}, {score:.2f}%"
            imgRGB = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            ret, buffer = cv2.imencode('.jpg', imgRGB)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            socketio.emit('frame', {'image': frame_base64, 'result': paused_result})
    else:
        original_paused_frame = None
        paused_frame = None
        paused_result = None

@socketio.on('toggle_overlay_mode')
def handle_toggle_overlay_mode(data):
    global overlay_mode
    overlay_mode = data
    print(f"Режим наложения изменен: {overlay_mode}")

@socketio.on('apply_settings')
def handle_apply_settings(data):
    global questions, choices
    try:
        new_questions = int(data.get('questions', 0))
        new_choices = int(data.get('choices', 0))

        # Проверяем, что значения больше или равны 1
        if new_questions < 1 or new_choices < 1:
            emit('error', {'message': 'Количество вопросов и вариантов ответов должно быть не менее 1.'})
            return

        # Применяем новые настройки
        questions = new_questions
        choices = new_choices
        correct_answers = [0] * questions  # Обновляем список правильных ответов
        emit('settings_applied', {'message': 'Настройки применены'})
    except ValueError as e:
        emit('error', {'message': 'Неверный формат данных. Убедитесь, что введены числа.'})

@socketio.on('update_correct_answers')
def handle_update_correct_answers(data):
    global correct_answers, last_grading, last_incorrect_questions
    try:
        correct_answers = [int(data[f'question_{i}']) for i in range(questions)]
        if is_paused and original_paused_frame is not None:
            result, correct_answers_count, score, incorrect_questions, grading = process_video_frame(
                original_paused_frame,
                questions,
                choices,
                correct_answers,
                image_size,
                overlay_mode
            )
            last_grading = [int(g) for g in grading]  # Обновляем результаты проверки
            last_incorrect_questions = incorrect_questions  # Обновляем список неправильных ответов
            imgRGB = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            ret, buffer = cv2.imencode('.jpg', imgRGB)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            paused_result = f"{correct_answers_count}/{questions}, {score:.2f}%"
            socketio.emit('frame', {'image': frame_base64, 'result': paused_result})
        emit('answers_updated', {'message': 'Правильные ответы обновлены'})
    except ValueError as e:
        emit('error', {'message': str(e)})

@socketio.on('add_to_report')
def handle_add_to_report(data):
    try:
        report = {}
        
        # Проверяем, откуда пришли данные (из пакетной обработки или сканирования)
        if isinstance(data, dict) and 'result' in data:
            # Данные из режима сканирования
            result_str = data['result']
            correct_count = int(result_str.split('/')[0])
            total_questions = int(result_str.split('/')[1].split(',')[0])
            score = float(result_str.split(',')[1].strip('%'))
            
            report = {
                'work_number': len(report_list) + 1,
                'correct_answers_count': correct_count,
                'incorrect_answers_count': total_questions - correct_count,
                'score_percentage': score,
                'correct_questions': [i + 1 for i, g in enumerate(last_grading) if g == 1],
                'incorrect_questions': last_incorrect_questions,
                'incorrect_question_numbers': [q['question_number'] for q in last_incorrect_questions]
            }
        else:
            # Данные из пакетной обработки
            report = {
                'work_number': len(report_list) + 1,
                'correct_answers_count': data['correct_count'],
                'incorrect_answers_count': data['total_questions'] - data['correct_count'],
                'score_percentage': data['score'],
                'correct_questions': data['correct_questions'],
                'incorrect_questions': data['incorrect_questions'],
                'incorrect_question_numbers': [q['question_number'] for q in data['incorrect_questions']]
            }
        
        # Определяем оценку
        score = report['score_percentage']
        if score >= 90:
            report['grade'] = 5
        elif score >= 70:
            report['grade'] = 4
        elif score >= 50:
            report['grade'] = 3
        else:
            report['grade'] = 2
            
        # Добавляем отчет в список
        report_list.append(report)
        
        # Отправляем подтверждение
        emit('report_added', {'success': True})
        
    except Exception as e:
        print(f"Ошибка при добавлении в отчёт: {str(e)}")
        emit('report_added', {
            'success': False,
            'message': str(e),
            'data': data
        })

def check_score_in_ranges(score, ranges):
    for i in range(len(ranges) - 1):
        if ranges[i][0] <= score < ranges[i + 1][0]:
            return True
    return False

@socketio.on('reset_reports')
def handle_reset_reports():
    global report_list
    report_list = []
    socketio.emit('reset_reports')

@socketio.on('apply_grading_criteria')
def handle_apply_grading_criteria(data):
    global grading_criteria
    try:
        new_criteria = parse_grading_criteria(data)
        if validate_grading_criteria(new_criteria):
            grading_criteria = new_criteria
            emit('criteria_applied', {'message': 'Критерии оценок применены'})
            reevaluate_reports()  # Пересчитываем оценки для существующих работ
        else:
            emit('error', {'message': 'Значения критериев не должны пересекаться.'})
    except ValueError as e:
        emit('error', {'message': str(e)})

def parse_grading_criteria(data):
    return {
        5: list(map(int, data.get('grade_5', '90-100').split('-'))),
        4: list(map(int, data.get('grade_4', '70-89').split('-'))),
        3: list(map(int, data.get('grade_3', '50-69').split('-'))),
        2: list(map(int, data.get('grade_2', '0-49').split('-')))
    }

def validate_grading_criteria(criteria):
    ranges = list(criteria.values())
    for i in range(len(ranges) - 1):
        if ranges[i][1] >= ranges[i + 1][0]:
            return False
    return True

def reevaluate_reports():
    for report in report_list:
        score_percentage = report['score_percentage']
        grade = 0
        if score_percentage >= grading_criteria[5][0] and score_percentage <= grading_criteria[5][1]:
            grade = 5
        elif score_percentage >= grading_criteria[4][0] and score_percentage <= grading_criteria[4][1]:
            grade = 4
        elif score_percentage >= grading_criteria[3][0] and score_percentage <= grading_criteria[3][1]:
            grade = 3
        elif score_percentage >= grading_criteria[2][0] and score_percentage <= grading_criteria[2][1]:
            grade = 2

        report['grade'] = grade
        socketio.emit('report_grade_updated', {'work_number': report['work_number'], 'grade': grade})

@socketio.on('update_camera_settings')
def handle_update_camera_settings(data):
    global brightness, contrast, saturation, sharpness
    try:
        brightness = int(data.get('brightness', 0))
        contrast = float(data.get('contrast', 1))
        saturation = float(data.get('saturation', 1))
        sharpness = float(data.get('sharpness', 1))

        print(f"Параметры камеры обновлены: {brightness}, {contrast}, {saturation}, {sharpness}")
    except ValueError as e:
        emit('error', {'message': str(e)})

@socketio.on('process_batch_image')
def handle_batch_image(data):
    try:
        # Декодируем base64 изображение
        image_data = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Обработка изображения с включенным режимом наложения
        result_img, correct_count, score, incorrect_questions, grading = process_video_frame(
            img, data['questions'], data['choices'], data['correctAnswers'],
            image_size=800, overlay_mode=True  # Включаем режим наложения
        )

        # Конвертируем результат обратно в base64
        _, buffer = cv2.imencode('.jpg', result_img)
        result_image_base64 = base64.b64encode(buffer).decode('utf-8')

        # Определяем правильные вопросы на основе grading
        correct_questions = [i + 1 for i, grade in enumerate(grading) if grade == 1]

        # Конвертируем результаты в JSON-сериализуемые типы
        response = {
            'id': data['id'],
            'correct_count': int(correct_count),
            'questions': int(data['questions']),
            'score': float(score),
            'correct_questions': [int(x) for x in correct_questions],
            'incorrect_questions': [
                {
                    'question_number': int(q['question_number']),
                    'selected_answer': int(q['selected_answer']),
                    'correct_answer': int(q['correct_answer'])
                }
                for q in incorrect_questions
            ],
            'processed_image': f'data:image/jpeg;base64,{result_image_base64}'  # Добавляем обработанное изображение
        }

        emit('batch_result', response)
    except Exception as e:
        print(f"Ошибка обработки изображения: {str(e)}")
        emit('error', {'message': f'Ошибка обработки изображения: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)