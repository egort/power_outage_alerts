import requests
from bs4 import BeautifulSoup
import telegram  # pip install python-telegram-bot
from telegram.ext import Application, CommandHandler
import time
import schedule  # pip install schedule
import os  # Для чтения ENV
import asyncio  # Для async отправки
import threading  # Для запуска расписания в отдельном потоке
from datetime import datetime, timedelta  # Для расчёта дат

# Настройки Telegram бота из ENV
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN и CHAT_ID должны быть заданы в переменных окружения!")

# Базовый URL для региона Novi Sad (включая Subotica)
BASE_URL = 'https://elektrodistribucija.rs/planirana-iskljucenja-srbija/'

# Дни для проверки (0 - сегодня, 1 - завтра, etc.)
DAYS = ['0', '1', '2', '3']

# Улица для поиска (case-insensitive) для автоматических уведомлений
TARGET_STREET = 'Proleterskih brigada'

# Заголовки для обхода 403 (имитируем браузер)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

# Функция для отправки сообщения в Telegram (с async)
def send_telegram_message(message, chat_id=CHAT_ID):
    async def async_send():
        bot = telegram.Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=message)
    
    try:
        asyncio.run(async_send())
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {str(e)}")  # Лог в консоль (видно в docker logs)

# Функция для форматирования улиц с переносами после запятых и точек с запятой
def format_streets(streets):
    # Заменяем '; ' и ', ' на ';\n' и ',\n' для переносов
    formatted = streets.replace('; ', ';\n').replace(', ', ',\n')
    return formatted

# Функция для парсинга отключений (возвращает список всех записей)
def parse_outages():
    try:
        all_records = []
        current_date = datetime.now().date()
        for day in DAYS:
            day_int = int(day)
            day_date = current_date + timedelta(days=day_int)
            day_info = f"{day_date.day:02d}.{day_date.month:02d}.{day_date.year} ({'сегодня' if day_int == 0 else 'завтра' if day_int == 1 else f'через {day} дня'})"
            
            day_url = f"{BASE_URL}NoviSad_Dan_{day}_Iskljucenja.htm"
            response = requests.get(day_url, headers=HEADERS)
            response.encoding = 'utf-8'
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            tables = soup.find_all('table')
            if len(tables) >= 2:
                table = tables[1]
                rows = table.find_all('tr')[1:]
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        branch = cells[0].get_text().strip()
                        municipality = cells[1].get_text().strip()
                        time_info = cells[2].get_text().strip()
                        streets = cells[3].get_text().strip()  # Сохраняем оригинал для вывода
                        
                        record = {
                            'day_info': day_info,
                            'branch': branch,
                            'municipality': municipality,
                            'time_info': time_info,
                            'streets': streets,
                            'streets_lower': streets.lower()  # Для поиска
                        }
                        all_records.append(record)
        
        return all_records
    
    except Exception as e:
        print(f"Ошибка в парсере: {str(e)}")
        return []

# Функция для автоматической проверки (уведомления по TARGET_STREET)
def check_outages(debug=False):
    all_records = parse_outages()
    updates = []
    debug_info = [] if debug else None
    
    if debug:
        for day in DAYS:
            day_records = [r for r in all_records if f"через {day} дня" in r['day_info'] or (day == '0' and 'сегодня' in r['day_info']) or (day == '1' and 'завтра' in r['day_info'])]
            debug_info.append(f"Для дня {day}: Найдено {len(day_records)} записей.")
            if day_records:
                example = day_records[0]
                streets_formatted = format_streets(example['streets'])
                debug_info.append(f"Пример первой записи: {example['day_info']} - {example['branch']}, {example['municipality']}: {example['time_info']} - Улицы: {streets_formatted}")
            else:
                debug_info.append("Нет записей для этого дня.")
    
    for record in all_records:
        if TARGET_STREET.lower() in record['streets_lower']:
            updates.append(record)
    
    if debug and debug_info:
        send_telegram_message("Отладочная информация при запуске:\n" + "\n".join(debug_info))
    
    if updates:
        # Отправляем только если есть обновления
        for update in updates:
            streets_formatted = format_streets(update['streets'])
            message = f"```\n{update['day_info']}\n{update['time_info']}\n{streets_formatted}\n```"
            send_telegram_message(message)
    # else: Не отправляем "Нет новых", чтобы не спамить

# Хендлер для /all (все объявления)
async def all_command(update, context):
    all_records = parse_outages()
    if all_records:
        for record in all_records:
            streets_formatted = format_streets(record['streets'])
            message = f"```\n{record['day_info']}\n{record['time_info']}\n{streets_formatted}\n```"
            await update.message.reply_text(message, parse_mode='MarkdownV2')
    else:
        await update.message.reply_text("Нет объявлений на проверенные дни.")

# Хендлер для /su (все по Суботице)
async def su_command(update, context):
    all_records = parse_outages()
    su_records = [r for r in all_records if 'суботица' in r['municipality'].lower()]
    if su_records:
        for record in su_records:
            streets_formatted = format_streets(record['streets'])
            message = f"```\n{record['day_info']}\n{record['time_info']}\n{streets_formatted}\n```"
            await update.message.reply_text(message, parse_mode='MarkdownV2')
    else:
        await update.message.reply_text("Нет объявлений по Суботице на проверенные дни.")

# Функция для запуска расписания в отдельном потоке
def run_scheduler():
    schedule.every(4).hours.do(check_outages)
    while True:
        schedule.run_pending()
        time.sleep(60)

# Запуск
if __name__ == '__main__':
    # Настройка бота для команд
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем хендлеры (async)
    application.add_handler(CommandHandler('all', all_command))
    application.add_handler(CommandHandler('su', su_command))
    
    # Запуск polling в основном потоке
    application.run_polling()
    
    # Запуск расписания в отдельном потоке
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Начальное сообщение и проверка
    send_telegram_message("Парсер запущен и мониторит отключения.")
    check_outages(debug=True)
