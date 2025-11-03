# Используем базовый образ Python 3.12 (slim для минимального размера)
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем скрипт в контейнер
COPY parser.py .

# Устанавливаем зависимости
RUN pip install --no-cache-dir requests beautifulsoup4 python-telegram-bot schedule

# Определяем переменные окружения (вы передадите их при запуске)
ENV BOT_TOKEN=""
ENV CHAT_ID=""

# Команда для запуска скрипта
CMD ["python", "parser.py"]