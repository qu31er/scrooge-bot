import telebot
from telebot import types
import time
import threading
import config
from database import Database
from crypto import CryptoBot
from functions import autoposting

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")
db = Database()
crypto = CryptoBot()

print("бот запускается")
print(f"бот: @{bot.get_me().username}")
print(f"админы: {config.ADMIN_IDS}")

# ============ ИМПОРТ МЕНЮ ============
from menu import main_menu, admin_menu, profile_menu, donate_menu, back, update_name

# ============ ОБРАБОТЧИКИ ============

@bot.message_handler(commands=['start'])
def start_handler(message):
    print(f"📩 Получен /start от {message.chat.id}")
    
    if message.chat.type != 'private':
        return
    
    chat_id = message.chat.id
    username = message.chat.username or f'user_{chat_id}'
    
    user = db.get_user(chat_id)
    if not user:
        db.add_user(chat_id, username)
        print(f"✅ Новый пользователь: {username}")
    
    bot.send_message(
        chat_id,
        f"👋 Добро пожаловать, @{username}!\n\n"
        "🤖 <b>Scrooge Garant Bot</b>\n"
        "Безопасные сделки с криптовалютой",
        parse_mode="HTML",
        reply_markup=main_menu
    )

@bot.message_handler(commands=['admin'])
def admin_handler(message):
    chat_id = message.chat.id
    
    if chat_id not in config.ADMIN_IDS:
        bot.send_message(chat_id, "⛔️ У вас нет прав администратора")
        return
    
    bot.send_message(
        chat_id,
        "👑 <b>Панель администратора</b>",
        parse_mode="HTML",
        reply_markup=admin_menu
    )

@bot.message_handler(content_types=['text'])
def text_handler(message):
    chat_id = message.chat.id
    text = message.text
    
    if message.chat.type != 'private':
        return
    
    print(f"📩 Получен текст: {text} от {chat_id}")
    
    user = db.get_user(chat_id)
    if not user:
        username = message.chat.username or f'user_{chat_id}'
        db.add_user(chat_id, username)
        user = db.get_user(chat_id)
    
    # ===== АДМИН-КОМАНДЫ =====
    if chat_id in config.ADMIN_IDS:
        if text == '📊 Статистика':
            show_statistics(chat_id)
            return
        elif text == '🔙 Назад':
            bot.send_message(chat_id, "👑 Панель администратора", reply_markup=admin_menu)
            return
    
    # ===== ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ =====
    if text == '💬 Помощь':
        settings = db.get_settings()
        bot.send_message(chat_id, settings['help'], reply_markup=update_name)
    elif text == '🎩 Мой профиль':
        show_profile(chat_id)
    elif text == '🤝 Мои сделки':
        show_my_deals(chat_id)
    elif text == '🔍 Найти user':
        bot.send_message(chat_id, "👤 Введите никнейм в формате @username")
    elif text == '🎁 Пожертвовать':
        bot.send_message(chat_id, "🎁 Пожертвования", reply_markup=donate_menu)
    elif text in ['❌ Отмена', '🔙 Назад', 'Вернуться в главное меню']:
        bot.send_message(chat_id, "🏠 Главное меню", reply_markup=main_menu)
    elif text.startswith('@') and len(text) > 1:
        search_user(chat_id, text[1:])
    else:
        bot.send_message(chat_id, "❓ Используйте кнопки меню")

# ============ CALLBACK ============

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data
    
    print(f"📩 Получен callback: {data} от {chat_id}")
    
    if data == 'deposit':
        bot.send_message(chat_id, "💰 Пополнение баланса")
    elif data == 'withdraw':
        bot.send_message(chat_id, "💸 Вывод средств")
    elif data == 'donate':
        bot.send_message(chat_id, "🎁 Спасибо за донат!")
    elif data == 'top_donate':
        show_top_donates(chat_id)
    elif data == 'how':
        bot.send_message(chat_id, "📖 Как пользоваться ботом...")
    elif data.startswith('deal_'):
        user_id = data.split('_')[1]
        bot.send_message(chat_id, f"💰 Сделка с пользователем {user_id}")
    elif data.startswith('feed_'):
        user_id = data.split('_')[1]
        show_feedback(chat_id, user_id)
    
    bot.answer_callback_query(call.id)

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============

def show_statistics(chat_id):
    users = db.get_all_users()
    total_balance = sum(u['balance'] for u in users)
    text = f"📊 Статистика\n\n👥 Пользователей: {len(users)}\n💰 Баланс: {total_balance} RUB"
    bot.send_message(chat_id, text)

def show_profile(chat_id):
    user = db.get_user(chat_id)
    if not user:
        return
    
    feedbacks = db.get_feedback(chat_id)
    text = f"🎩 Профиль\n\n👤 @{user['name']}\n💰 Баланс: {user['balance']} RUB\n💬 Отзывов: {len(feedbacks)}"
    bot.send_message(chat_id, text, reply_markup=profile_menu)

def show_my_deals(chat_id):
    sales = db.get_user_sales(chat_id)
    if not sales:
        bot.send_message(chat_id, "❌ Нет активных сделок", reply_markup=main_menu)
        return
    
    for sale in sales:
        text = f"🤝 Сделка #{sale['id']}\nСумма: {sale['sum']} RUB"
        bot.send_message(chat_id, text)

def search_user(chat_id, username):
    user = db.get_user_by_name(username)
    if not user:
        bot.send_message(chat_id, "❌ Пользователь не найден")
        return
    
    bot.send_message(chat_id, f"👤 @{user['name']}\nСтатус: {user['status']}")

def show_feedback(chat_id, user_id):
    feedbacks = db.get_feedback(user_id)
    if not feedbacks:
        bot.send_message(chat_id, "📝 Отзывов пока нет")
        return
    
    text = "⭐️ Отзывы:\n\n"
    for fb in feedbacks[:5]:
        text += f"👤 @{fb['name2']}: {fb['text']}\n"
    bot.send_message(chat_id, text)

def show_top_donates(chat_id):
    donates = db.get_top_donates()
    if not donates:
        bot.send_message(chat_id, "📊 Пока нет донатов")
        return
    
    text = "🏆 Топ донатеров:\n\n"
    for i, donate in enumerate(donates, 1):
        text += f"{i}. {donate['user_id']} - {donate['total']} RUB\n"
    bot.send_message(chat_id, text)

# ============ ЗАПУСК ============

if __name__ == '__main__':
    #автопостинг
    thread = threading.Thread(target=autoposting, args=(bot, db), daemon=True)
    thread.start()
    print("автопостинг запущен")
    
   
    bot.remove_webhook()
    print("вебхук удален")
    
    # ЗАПУСКАЕМ POLLING
    print("бот запущен")
    bot.polling(none_stop=True, interval=1, timeout=20)