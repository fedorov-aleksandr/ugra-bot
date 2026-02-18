import telebot
from telebot import types
import random
import json
import os
import sys
from datetime import datetime
from colorama import init, Fore, Back, Style

# --- НАСТРОЙКА ЦВЕТОВ И ВЫВОДА ДЛЯ DOCKER ---
# strip=False принудительно оставляет цвета в логах Docker
init(autoreset=True, strip=False)
# Отключаем буферизацию Python, чтобы логи шли в реальном времени
os.environ['PYTHONUNBUFFERED'] = '1'

# --- КОНФИГУРАЦИЯ ---
TG_TOKEN = os.getenv('TG_TOKEN')
if not TG_TOKEN:
    print("Ошибка: не задан токен в переменной окружения TG_TOKEN")
    sys.exit(1)
bot = telebot.TeleBot(TG_TOKEN)

# --- ФУНКЦИИ ЛОГИРОВАНИЯ ---

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_user_info(user):
    username = f"@{user.username}" if user.username else "NoUsername"
    return f"ID:{user.id} | {username} | {user.first_name}"

def log_user_action(user, action):
    """Белый текст на Розовом фоне для действий пользователя"""
    print(f"{Fore.WHITE}{Back.MAGENTA}[{get_time()}] ПОЛЬЗОВАТЕЛЬ [{get_user_info(user)}] >>> {action}{Style.RESET_ALL}", flush=True)

def log_bot_reply(user, reply_text):
    """Белый текст на Синем фоне для ответов бота"""
    short_text = (reply_text[:100] + '...') if len(reply_text) > 100 else reply_text
    print(f"{Fore.WHITE}{Back.BLUE}[{get_time()}] БОТ ОТВЕТИЛ [{get_user_info(user)}] <<< {short_text}{Style.RESET_ALL}", flush=True)

def log_system(text):
    """Зеленый текст для системных событий"""
    print(f"{Fore.GREEN}[{get_time()}] СИСТЕМА: {text}{Style.RESET_ALL}", flush=True)

def log_error(text):
    """Красный текст для ошибок"""
    print(f"{Fore.RED}[{get_time()}] ОШИБКА: {text}{Style.RESET_ALL}", flush=True)

# --- ЗАГРУЗКА ДАННЫХ ---

def load_data(file_name):
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                log_system(f"Файл {file_name} загружен успешно.")
                return data
        except Exception as e:
            log_error(f"Ошибка чтения {file_name}: {e}")
            return None
    log_error(f"Файл {file_name} не найден!")
    return None

cities_db = load_data('cities.json')
history_db = load_data('history.json')
dictionary_list = load_data('dictionary.json')
eco_list = load_data('eco.json')

# --- КЛАВИАТУРЫ ---

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📍 Интересные места", "⛽️ История нефти")
    markup.add("🦊 Учим хантыйский", "🌲 Эко-советы")
    return markup

# --- ОБРАБОТЧИКИ CALLBACK (КНОПКИ ПОД СООБЩЕНИЯМИ) ---

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    log_user_action(call.from_user, f"КНОПКА: {call.data}")
    try:
        # 1. Хантыйский язык
        if call.data == 'khanty_next' and dictionary_list:
            word = random.choice(dictionary_list)
            text = f"🦊 <b>Слово:</b> {word['word']}\n📖 <b>Перевод:</b> {word['translate']}\n\n💡 <i>{word['fact']}</i>"
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 Еще слово", callback_data='khanty_next'))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
            log_bot_reply(call.from_user, f"Обновлено слово: {word['word']}")

        # 2. Эко-советы
        elif call.data == 'eco_next' and eco_list:
            tip = random.choice(eco_list)
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 Еще совет", callback_data='eco_next'))
            bot.edit_message_text(f"<b>{tip['title']}</b>\n\n{tip['text']}", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
            log_bot_reply(call.from_user, f"Обновлен эко-совет: {tip['title']}")

        # 3. Назад в меню истории
        elif call.data == 'back_to_history':
            if history_db:
                markup = types.InlineKeyboardMarkup()
                for key, ev in history_db.items():
                    markup.add(types.InlineKeyboardButton(ev['btn_name'], callback_data=key))
                
                # Если было фото, удаляем и шлем заново меню
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except: pass
                
                bot.send_message(call.message.chat.id, "🕰 <b>История нефти: Выбери эпоху</b>", parse_mode='HTML', reply_markup=markup)
                log_bot_reply(call.from_user, "Возврат в меню истории")

        # 4. Просмотр конкретного события истории (работает с любыми ключами: event_2016 и т.д.)
        elif history_db and call.data in history_db:
            event = history_db[call.data]
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Назад", callback_data='back_to_history'))
            
            if 'image' in event and event['image']:
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                    bot.send_photo(call.message.chat.id, event['image'], caption=event['text'], parse_mode='HTML', reply_markup=markup)
                except:
                    bot.send_message(call.message.chat.id, event['text'], parse_mode='HTML', reply_markup=markup)
            else:
                bot.edit_message_text(event['text'], call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
            
            log_bot_reply(call.from_user, f"Показана история: {event.get('btn_name')}")

    except Exception as e:
        log_error(f"Ошибка в callback: {e}")

# --- ОБРАБОТЧИКИ ТЕКСТА ---

@bot.message_handler(commands=['start'])
def start_command(message):
    log_user_action(message.from_user, "Команда /start")
    welcome = (
        f"Привет, <b>{message.from_user.first_name}</b>! 👋\n\n"
        "Я твой цифровой гид по <b>Югре</b>.\n"
        "Используй меню ниже, чтобы начать путешествие! 👇"
    )
    bot.send_message(message.chat.id, welcome, parse_mode='HTML', reply_markup=main_menu())
    log_bot_reply(message.from_user, "Приветствие отправлено")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    log_user_action(message.from_user, f"Текст: {message.text}")
    
    # Главное меню
    if message.text == "📍 Интересные места":
        cities_list = ", ".join([key.capitalize() for key in cities_db.keys()]) if cities_db else "Нет данных"
        bot.send_message(message.chat.id, f"🏙 <b>Введите название города, чтобы узнать о нем:</b>\n\nДоступно: {cities_list}", parse_mode='HTML')
        log_bot_reply(message.from_user, "Запрос города")

    elif message.text == "⛽️ История нефти":
        if history_db:
            markup = types.InlineKeyboardMarkup()
            for key, event in history_db.items():
                markup.add(types.InlineKeyboardButton(event['btn_name'], callback_data=key))
            bot.send_message(message.chat.id, "🕰 <b>История нефти: Выбери эпоху</b>", parse_mode='HTML', reply_markup=markup)
            log_bot_reply(message.from_user, "Меню истории")

    elif message.text == "🦊 Учим хантыйский":
        if dictionary_list:
            word = random.choice(dictionary_list)
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 Еще слово", callback_data='khanty_next'))
            bot.send_message(message.chat.id, f"🦊 <b>{word['word']}</b> — {word['translate']}\n\n<i>{word['fact']}</i>", parse_mode='HTML', reply_markup=markup)
            log_bot_reply(message.from_user, f"Слово: {word['word']}")

    elif message.text == "🌲 Эко-советы":
        if eco_list:
            tip = random.choice(eco_list)
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 Еще совет", callback_data='eco_next'))
            bot.send_message(message.chat.id, f"<b>{tip['title']}</b>\n\n{tip['text']}", parse_mode='HTML', reply_markup=markup)
            log_bot_reply(message.from_user, f"Совет: {tip['title']}")

    # Обработка ввода города
    else:
        user_input = message.text.lower().replace(" ", "").replace("-", "")
        found_city = None
        if cities_db:
            for key in cities_db:
                if key.lower().replace(" ", "").replace("-", "") == user_input:
                    found_city = cities_db[key]
                    break
        
        if found_city:
            markup = types.InlineKeyboardMarkup()
            if 'maps_url' in found_city:
                markup.add(types.InlineKeyboardButton("🗺 На карте", url=found_city['maps_url']))
            
            if 'image' in found_city:
                try:
                    bot.send_photo(message.chat.id, found_city['image'], caption=f"📍 <b>{message.text}</b>", parse_mode='HTML')
                except: pass
            
            bot.send_message(message.chat.id, found_city['text'], parse_mode='HTML', reply_markup=markup)
            log_bot_reply(message.from_user, f"Инфо о городе: {message.text}")
        else:
            bot.send_message(message.chat.id, "Я пока не знаю об этом. Попробуй выбрать пункт из меню! 👇")
            log_bot_reply(message.from_user, "Неизвестная команда/город")

# --- ЗАПУСК ---
if __name__ == "__main__":
    log_system("Инициализация систем...")
    print(f"{Fore.CYAN}================================================={Style.RESET_ALL}")
    print(f"{Fore.CYAN}   UGRA GUIDE BOT ЗАПУЩЕН И СМОТРИТ В ЛОГИ       {Style.RESET_ALL}")
    print(f"{Fore.CYAN}================================================={Style.RESET_ALL}")
    
    try:
        bot.polling(non_stop=True)
    except Exception as e:
        log_error(f"КРИТИЧЕСКИЙ СБОЙ: {e}")
