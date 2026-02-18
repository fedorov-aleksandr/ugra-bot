FROM python:3.12-slim

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app

# Создаём папку для логов (если нужно)
RUN mkdir -p /app/logs

# Делаем скрипт запуска исполняемым
RUN chmod +x /app/start.sh

# Отключаем буферизацию вывода Python
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["/app/start.sh"]
