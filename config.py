import os

# токен бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

# токен кошелька
CRYPTO_TOKEN = os.environ.get('CRYPTO_TOKEN')
if not CRYPTO_TOKEN:
    raise ValueError("CRYPTO_TOKEN не найден в переменных окружения!")

#айди админов
admin_ids_str = os.environ.get('ADMIN_IDS', '')
if not admin_ids_str:
    raise ValueError("ADMIN_IDS не найден в переменных окружения!")
ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]

# настройки по умолчанию
COMMISSION = int(os.environ.get('COMMISSION', 5))
CHANNEL = os.environ.get('CHANNEL', '@your_channel')
HELP_TEXT = os.environ.get('HELP_TEXT', 'Бот для безопасных сделок с криптовалютой')

# Настройки Railway
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')

print("конфиг загружен")
print(f"админы: {ADMIN_IDS}")
print(f"комиссия: {COMMISSION}%")