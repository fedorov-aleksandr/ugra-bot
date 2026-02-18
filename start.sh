#!/bin/sh
set -e

# Бесконечный цикл перезапуска бота
while true; do
    echo "$(date): Запуск бота..."
    python main.py
    EXIT_CODE=$?
    echo "$(date): Бот завершился с кодом $EXIT_CODE. Перезапуск через 5 секунд..."
    sleep 5
done
