# Указываем базовый образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения в контейнер
COPY . .

# Указываем переменные окружения для Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Открываем порт для приложения Flask
EXPOSE 8080

# Команда для запуска приложения
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
