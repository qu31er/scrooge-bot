import telebot
from telebot import types
import time
import threading
import sys
import os
from flask import Flask, request

import config
from database import Database
from crypto import CryptoBot
from handlers import register_all_handlers
from functions import autoposting

#иниц.
bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")
db = Database()
crypto = CryptoBot()

app = Flask(__name__)

print("Бот запускается...")
print(f"Бот: @{bot.get_me().username}")
print(f"Админы: {config.ADMIN_IDS}")

#обработчики
register_all_handlers(bot, db, crypto)

#хилтчек
@app.route('/health', methods=['GET'])
def health():
    return 'OK', 200

#webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    if config.WEBHOOK_URL:
        update = types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Webhook disabled', 404

#запуск фоновых задач
def start_background():
    thread = threading.Thread(target=autoposting, args=(bot, db), daemon=True)
    thread.start()
    print("фоновые задачи запущены")

#flask в отдельном потоке
def run_flask():
    app.run(host='0.0.0.0', port=config.PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    # фоновые задачи
    start_background()
    
    #flask
    if config.WEBHOOK_URL:
        #вебхук
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{config.WEBHOOK_URL}/webhook")
        print(f"вебхук установлен: {config.WEBHOOK_URL}/webhook")
        
        # Запускаем Flask (он сам заблокирует поток)
        run_flask()
    else:
        #polling
        print("polling")
        
        # Запускаем Flask в отдельном потоке
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        #flask
        time.sleep(2)
        
        #polling
        print("рolling запущен")
        bot.polling(none_stop=True, interval=1)