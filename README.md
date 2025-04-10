# 📝 Сканер тестов

<div align="center">

![image](https://github.com/user-attachments/assets/f6701c19-31a4-40c9-849a-707fd62ba488)

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8.0-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![Flask](https://img.shields.io/badge/Flask-2.0.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-4.0.1-010101?style=for-the-badge&logo=socket.io&logoColor=white)](https://socket.io/)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)

### 🔍 Современное решение для автоматизированной проверки тестов на основе компьютерного зрения

[🚀 Демо](#-демонстрация) • [📦 Установка](#-быстрый-старт) • [📖 Документация](#-документация) • [🤝 Вклад](#-участие-в-разработке)

</div>

---

## 🔗 Полезные ресурсы

- [Специальный шрифт для бланков](https://github.com/mrKamanov/TscanSDK/blob/master/assets/OMRBubbles.ttf)
- [Образец бланка для тестов](https://github.com/mrKamanov/TscanSDK/blob/master/assets/%D0%9E%D0%B1%D1%80%D0%B0%D0%B7%D0%B5%D1%86%20%D0%B1%D0%BB%D0%B0%D0%BD%D0%BA%D0%B0.docx)
- [Репозиторий проекта](https://github.com/mrKamanov/TscanSDK)

---

## ✨ Возможности

✅ **Точное распознавание** – коррекция перспективы и адаптивная обработка изображений  
⚡ **Высокая производительность** – пакетное сканирование и работа в реальном времени  
📊 **Продвинутая аналитика** – визуализация данных и экспорт отчетов  
🎨 **Современный интерфейс** – адаптивный дизайн и темная тема  

---

## 🔬 Как это работает?

### 🛠️ Алгоритм обработки

1. **Предобработка** – устранение шумов, нормализация яркости и контраста  
2. **Обнаружение бланка** – коррекция перспективных искажений  
3. **Распознавание ответов** – сегментация и анализ заполненных ячеек  
4. **Анализ результатов** – сопоставление с эталоном и формирование отчета  

### 🏗️ Используемые технологии

- **Backend:** Python, OpenCV, NumPy, Flask
- **Frontend:** HTML5, CSS3, JavaScript, Socket.IO, Chart.js
- **Хранение данных:** JSON, Excel, Base64

```mermaid
graph TD;
  A[Веб-интерфейс] --> B[Flask сервер];
  B --> C[Обработка изображений];
  C --> D[OpenCV];
  C --> E[NumPy];
  B --> F[Генерация отчетов];
  F --> G[JSON];
  F --> H[Excel];
  B --> I[Socket.IO];
  I --> J[Передача данных в реальном времени];
```

---

## 📸 Интерфейс

| 🔍 Распознавание | 📦 Пакетная обработка | 📊 Аналитика |
|---|---|---|
| ![image](https://github.com/user-attachments/assets/d8d636ce-e6c3-46ff-b4c6-a43eef648a07) | ![image](https://github.com/user-attachments/assets/79d8ee3b-c6f0-4f90-be2c-f346cce06185) | ![image](https://github.com/user-attachments/assets/ac3e511d-751a-402d-9a79-febc3a56f8a3) |

| 📝 Множественный выбор | 🛠️ Конструктор OMR листов | 📑 Инструкции |
|---|---|---|
| ![image](https://github.com/user-attachments/assets/6e148e4b-ea0a-429c-bc39-f332d7f472ba) | ![image](https://github.com/user-attachments/assets/f8d78b98-ad39-4d9b-a9cc-3fe77a78c63d) | ![image](https://github.com/user-attachments/assets/7fdf9a7d-3634-4354-8732-81edd0423d40) |

| 📱 Мобильная версия 1 | 📱 Мобильная версия 2 | 📱 Мобильная версия 3 |
|---|---|---|
| ![image](https://github.com/user-attachments/assets/d02caef8-dd9c-4761-93c5-eead1ebbcaa7) | ![image](https://github.com/user-attachments/assets/3bb7b585-83d2-4543-be0b-62fc2690ddf1) | ![image](https://github.com/user-attachments/assets/41f0100e-cbf6-41a6-845a-30cefacb41c5) |

---

## 🚀 Быстрый старт

### 🛠️ Требования
- Python 3.8+
- pip
- Веб-камера (для сканирования в реальном времени)

### 📥 Установка

```bash
git clone https://github.com/mrKamanov/TscanSDK.git
cd TscanSDK
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python app.py
```

---

## 📖 Документация

### 🎥 Работа с камерой
- 🟢 **Включить** – запуск видеопотока
- 🔴 **Выключить** – остановка записи
- ⏸️ **Стоп-кадр** – фиксация изображения
- ➕ **Сохранить** – добавление результата в отчет

### 📦 Пакетная обработка
1. 📤 Загрузите изображения (drag & drop или выбор файлов)
2. ⚙️ Настройте параметры теста
3. ▶️ Запустите распознавание
4. 📋 Проверьте результаты
5. 💾 Экспортируйте отчет

---

## 🤝 Участие в разработке

Мы приветствуем вклад в развитие проекта!

1. 🍴 Форкните репозиторий
2. 🔧 Создайте ветку для новой функции
3. 📝 Внесите изменения
4. 🔍 Протестируйте
5. 📫 Создайте Pull Request

---
### Сделано с ❤️ для образования

## 👥 Контакты

📧 **mr.kamanov@yandex.ru**

<div align="center">

### 🚀 Поддержите проект! ⭐

[![Follow](https://img.shields.io/github/followers/mrKamanov?label=Follow&style=social)](https://github.com/mrKamanov)
[![Stars](https://img.shields.io/github/stars/mrKamanov/TscanSDK?style=social)](https://github.com/mrKamanov/TscanSDK)

</div>

