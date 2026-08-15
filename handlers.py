import telebot
from telebot import types
import time
import config
import menu
from database import Database
from crypto import CryptoBot

def register_all_handlers(bot, db, crypto):
    """регистрация всех обработчиков"""
    
    #ТЕКСТОВЫЕ
    
    @bot.message_handler(content_types=['text'])
    def text_handler(message):
        chat_id = message.chat.id
        text = message.text
        
        if message.chat.type != 'private':
            return
        
        user = db.get_user(chat_id)
        if not user:
            username = message.chat.username or f'user_{chat_id}'
            db.add_user(chat_id, username)
            user = db.get_user(chat_id)
        
        # АДМИН-КОМАНДЫ
        if chat_id in config.ADMIN_IDS:
            if text == '📊 Статистика':
                show_statistics(chat_id, db)
            elif text == '📨 Рассылка':
                msg = bot.send_message(chat_id, "📨 Введите текст рассылки:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, process_mailing, bot, db)
            elif text == '💰 Изменить баланс':
                msg = bot.send_message(chat_id, "💰 Введите ID и сумму через пробел:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_balance, db)
            elif text == '📢 Канал':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"📢 Текущий канал: {settings['channal']}\nОтправьте новый:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_channel, db)
            elif text == '💳 Комиссия':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"💳 Текущая комиссия: {settings['commission']}%\nВведите новую (0-50):", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_commission, db)
            elif text == '📝 Описание':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"📝 Текущее описание:\n{settings['help']}\n\nОтправьте новый текст:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_help, db)
            elif text == '📰 Автопостинг':
                msg = bot.send_message(chat_id, "📰 Отправьте текст поста:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, ask_post_buttons, db)
            elif text == '🔙 Назад':
                bot.send_message(chat_id, "👑 Панель администратора", reply_markup=menu.admin_menu)
        
        #ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ
        if text == '💬 Помощь':
            settings = db.get_settings()
            bot.send_message(chat_id, settings['help'], reply_markup=menu.update_name)
        elif text == '🎩 Мой профиль':
            show_profile(chat_id, db)
        elif text == '🤝 Мои сделки':
            show_my_deals(chat_id, bot, db)
        elif text == '🔍 Найти user':
            bot.send_message(chat_id, "👤 Введите никнейм в формате @username")
        elif text.startswith('@') and len(text) > 1:
            search_user(chat_id, text[1:], bot, db)
        elif text == '🎁 Пожертвовать':
            bot.send_message(chat_id, "🎁 Пожертвования", reply_markup=menu.donate_menu)
        elif text in ['❌ Отмена', '🔙 Назад', 'Вернуться в главное меню']:
            bot.send_message(chat_id, "🏠 Главное меню", reply_markup=menu.main_menu)
  
    #CALLBACК
    
    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        chat_id = call.message.chat.id
        data = call.data
        
        if data == 'deposit':
            msg = bot.send_message(chat_id, "💰 Введите сумму пополнения:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_deposit, bot, crypto, db)
        
        elif data == 'withdraw':
            msg = bot.send_message(chat_id, "💰 Введите сумму вывода:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_withdraw, bot, crypto, db)
        
        elif data == 'donate':
            msg = bot.send_message(chat_id, "🎁 Введите сумму доната:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_donate, bot, crypto, db)
        
        elif data == 'top_donate':
            show_top_donates(chat_id, db)
        
        elif data == 'how':
            bot.send_message(chat_id, "📖 Как пользоваться:\n1. Найти пользователя\n2. Начать сделку\n3. Оплатить через Crypto Bot\n4. Завершить сделку")
        
        elif data.startswith('deal_'):
            user_id = data.split('_')[1]
            msg = bot.send_message(chat_id, "💰 Введите сумму сделки:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, create_deal, user_id, bot, db, crypto)
        
        elif data.startswith('feed_'):
            user_id = data.split('_')[1]
            show_feedback(chat_id, user_id, db)
        
        elif data.startswith('sale_end_'):
            sale_id = int(data.split('_')[2])
            complete_sale(chat_id, sale_id, bot, db)
        
        elif data.startswith('sale_back_'):
            sale_id = int(data.split('_')[2])
            cancel_sale(chat_id, sale_id, bot, db)
        
        elif data.startswith('dispute_'):
            sale_id = int(data.split('_')[1])
            open_dispute(chat_id, sale_id, bot, db)
        
        elif data.startswith('check_pay_'):
            invoice_id = data.split('_')[2]
            check_payment(chat_id, invoice_id, bot, crypto, db)
        
        bot.answer_callback_query(call.id)
    
    print("все обработчики зарегистрированы")

# вспом. функции

def show_statistics(chat_id, db):
    users = db.get_all_users()
    total_balance = sum(u['balance'] for u in users)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        sales = cursor.execute('SELECT COUNT(*), SUM(sum) FROM sale WHERE id != 0').fetchone()
        disputes = cursor.execute('SELECT COUNT(*) FROM dispute').fetchone()
        donates = cursor.execute('SELECT COUNT(*), SUM(sum) FROM donate').fetchone()
    
    text = f"📊 Статистика\n\n👥 Пользователей: {len(users)}\n💰 Баланс: {total_balance} RUB\n🤝 Сделок: {sales[0] or 0}\n💳 На сумму: {sales[1] or 0} RUB\n⚖️ Споров: {disputes[0] or 0}\n🎁 Донатов: {donates[0] or 0}"
    bot.send_message(chat_id, text)

def process_mailing(message, bot, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    users = db.get_all_users()
    success, fail = 0, 0
    
    for user in users:
        try:
            bot.send_message(user['user_id'], message.text, parse_mode="HTML")
            success += 1
        except:
            fail += 1
        time.sleep(0.05)
    
    bot.send_message(chat_id, f"✅ Рассылка: {success} отправлено, {fail} не доставлено", reply_markup=menu.admin_menu)

def change_balance(message, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(chat_id, "❌ Формат: ID Сумма")
            return
        
        user_id, amount = int(parts[0]), int(parts[1])
        if not db.get_user(user_id):
            bot.send_message(chat_id, f"❌ Пользователь {user_id} не найден")
            return
        
        db.set_balance(user_id, amount)
        bot.send_message(chat_id, f"✅ Баланс {user_id} = {amount} RUB", reply_markup=menu.admin_menu)
    except:
        bot.send_message(chat_id, "❌ Ошибка!")

def change_channel(message, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    db.update_setting('channal', message.text)
    bot.send_message(chat_id, f"✅ Канал: {message.text}", reply_markup=menu.admin_menu)

def change_commission(message, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    try:
        commission = int(message.text)
        if 0 <= commission <= 50:
            db.update_setting('commission', commission)
            bot.send_message(chat_id, f"✅ Комиссия: {commission}%", reply_markup=menu.admin_menu)
        else:
            bot.send_message(chat_id, "❌ От 0 до 50")
    except:
        bot.send_message(chat_id, "❌ Введите число")

def change_help(message, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    db.update_setting('help', message.text)
    bot.send_message(chat_id, "✅ Описание обновлено", reply_markup=menu.admin_menu)

def ask_post_buttons(message, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    msg = bot.send_message(chat_id, "📎 Отправьте кнопки:\n[Текст + ссылка]\nПример: [Канал + https://t.me/channel]", reply_markup=menu.back)
    bot.register_next_step_handler(msg, save_post, message.text, db)

def save_post(message, text, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    db.update_post(text, message.text)
    bot.send_message(chat_id, "✅ Пост сохранен!", reply_markup=menu.admin_menu)

def show_profile(chat_id, db):
    user = db.get_user(chat_id)
    if not user:
        return
    
    feedbacks = db.get_feedback(chat_id)
    text = f"🎩 Профиль\n\n👤 @{user['name']}\n📝 Статус: {user['status']}\n💰 Баланс: {user['balance']} RUB\n💬 Отзывов: {len(feedbacks)}\n🤝 Продаж: {user['sell']} шт.\n🛒 Покупок: {user['buy']} шт."
    bot.send_message(chat_id, text, reply_markup=menu.profile_menu)

def show_my_deals(chat_id, bot, db):
    sales = db.get_user_sales(chat_id)
    if not sales:
        bot.send_message(chat_id, "❌ Нет активных сделок", reply_markup=menu.main_menu)
        return
    
    for sale in sales:
        text = f"🤝 Сделка #{sale['id']}\nОт @{sale['name']}\nДля @{sale['name2']}\nСумма: {sale['sum']} RUB"
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        if str(chat_id) == sale['user_id']:
            keyboard.add(
                types.InlineKeyboardButton('✅ Завершить', callback_data=f'sale_end_{sale["id"]}'),
                types.InlineKeyboardButton('⚖️ Спор', callback_data=f'dispute_{sale["id"]}')
            )
        elif str(chat_id) == sale['user_id2']:
            keyboard.add(
                types.InlineKeyboardButton('❌ Отменить', callback_data=f'sale_back_{sale["id"]}'),
                types.InlineKeyboardButton('⚖️ Спор', callback_data=f'dispute_{sale["id"]}')
            )
        
        bot.send_message(chat_id, text, reply_markup=keyboard)

def search_user(chat_id, username, bot, db):
    user = db.get_user_by_name(username)
    if not user:
        bot.send_message(chat_id, "❌ Пользователь не найден")
        return
    
    if user['user_id'] == str(chat_id):
        bot.send_message(chat_id, "ℹ️ Это вы")
        return
    
    feedbacks = db.get_feedback(user['user_id'])
    text = f"👤 @{user['name']}\n📝 Статус: {user['status']}\n💬 Отзывов: {len(feedbacks)}"
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton('💰 Сделка', callback_data=f'deal_{user["user_id"]}'),
        types.InlineKeyboardButton('⭐️ Отзывы', callback_data=f'feed_{user["user_id"]}')
    )
    bot.send_message(chat_id, text, reply_markup=keyboard)

def create_deal(message, seller_id, bot, db, crypto):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.main_menu)
        return
    
    try:
        amount = int(message.text)
        if amount < 10:
            bot.send_message(chat_id, "❌ Минимум 10 RUB")
            return
        
        user = db.get_user(chat_id)
        seller = db.get_user(seller_id)
        if not user or not seller:
            bot.send_message(chat_id, "❌ Ошибка")
            return
        
        if user['balance'] < amount:
            bot.send_message(chat_id, "❌ Недостаточно средств")
            return
        
        sale_id = db.create_sale(chat_id, user['name'], seller_id, seller['name'], amount)
        
        invoice = crypto.create_invoice(amount, 'USDT', f'Сделка #{sale_id}')
        if invoice:
            db.add_invoice(invoice['invoice_id'], chat_id, amount, 'USDT', sale_id, 'deal')
            
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                types.InlineKeyboardButton('💳 Оплатить', url=invoice['pay_url']),
                types.InlineKeyboardButton('✅ Проверить', callback_data=f'check_pay_{invoice["invoice_id"]}')
            )
            
            bot.send_message(chat_id, f"💳 Оплатите {amount} RUB", reply_markup=keyboard)
            bot.send_message(seller_id, f"🆕 Сделка #{sale_id}\nПокупатель: @{user['name']}\nСумма: {amount} RUB")
    except:
        bot.send_message(chat_id, "❌ Введите число")

def check_payment(chat_id, invoice_id, bot, crypto, db):
    invoice = crypto.check_invoice(invoice_id)
    if not invoice:
        bot.send_message(chat_id, "❌ Счет не найден")
        return
    
    if invoice['status'] == 'paid':
        db.update_invoice_status(invoice_id, 'paid')
        inv_data = db.get_invoice(invoice_id)
        
        if inv_data and inv_data['type'] == 'deal':
            db.complete_sale(inv_data['deal_id'])
            bot.send_message(chat_id, f"✅ Сделка #{inv_data['deal_id']} завершена!")
        else:
            db.update_balance(inv_data['user_id'], inv_data['amount'])
            bot.send_message(chat_id, f"✅ Баланс пополнен на {inv_data['amount']} RUB")
    else:
        bot.send_message(chat_id, f"⏳ Статус: {invoice['status']}")

def complete_sale(chat_id, sale_id, bot, db):
    sale = db.get_sale(sale_id)
    if not sale:
        bot.send_message(chat_id, "❌ Сделка не найдена")
        return
    
    if db.complete_sale(sale_id):
        bot.send_message(chat_id, f"✅ Сделка #{sale_id} завершена!")
        bot.send_message(sale['user_id2'], f"✅ Сделка #{sale_id} завершена!\nСумма: {sale['sum']} RUB")

def cancel_sale(chat_id, sale_id, bot, db):
    sale = db.get_sale(sale_id)
    if not sale:
        bot.send_message(chat_id, "❌ Сделка не найдена")
        return
    
    if db.cancel_sale(sale_id):
        bot.send_message(chat_id, f"❌ Сделка #{sale_id} отменена")
        bot.send_message(sale['user_id'], f"❌ Сделка #{sale_id} отменена")

def open_dispute(chat_id, sale_id, bot, db):
    sale = db.get_sale(sale_id)
    if not sale:
        bot.send_message(chat_id, "❌ Сделка не найдена")
        return
    
    db.create_dispute(sale_id, sale['user_id'], sale['name'], sale['user_id2'], sale['name2'], sale['sum'])
    bot.send_message(chat_id, f"⚖️ Спор #{sale_id} открыт")
    
    for admin in config.ADMIN_IDS:
        bot.send_message(admin, f"⚖️ Новый спор!\nСделка #{sale_id}\nПокупатель: @{sale['name']}\nПродавец: @{sale['name2']}\nСумма: {sale['sum']} RUB")

def show_feedback(chat_id, user_id, db):
    feedbacks = db.get_feedback(user_id)
    if not feedbacks:
        bot.send_message(chat_id, "📝 Отзывов пока нет")
        return
    
    text = "⭐️ Отзывы:\n\n"
    for fb in feedbacks[:5]:
        text += f"👤 @{fb['name2']}: {fb['text']}\n"
    
    bot.send_message(chat_id, text)

def show_top_donates(chat_id, db):
    donates = db.get_top_donates()
    if not donates:
        bot.send_message(chat_id, "📊 Пока нет донатов")
        return
    
    text = "🏆 Топ донатеров:\n\n"
    for i, donate in enumerate(donates, 1):
        text += f"{i}. {donate['user_id']} - {donate['total']} RUB\n"
    
    bot.send_message(chat_id, text)

def process_deposit(message, bot, crypto, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.main_menu)
        return
    
    try:
        amount = int(message.text)
        if amount < 10:
            bot.send_message(chat_id, "❌ Минимум 10 RUB")
            return
        
        invoice = crypto.create_invoice(amount, 'USDT', 'Пополнение баланса')
        if invoice:
            db.add_invoice(invoice['invoice_id'], chat_id, amount, 'USDT', 0, 'deposit')
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                types.InlineKeyboardButton('💳 Оплатить', url=invoice['pay_url']),
                types.InlineKeyboardButton('✅ Проверить', callback_data=f'check_pay_{invoice["invoice_id"]}')
            )
            bot.send_message(chat_id, f"💳 Пополните на {amount} RUB", reply_markup=keyboard)
    except:
        bot.send_message(chat_id, "❌ Введите число")

def process_withdraw(message, bot, crypto, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.main_menu)
        return
    
    try:
        amount = int(message.text)
        user = db.get_user(chat_id)
        
        if not user or user['balance'] < amount:
            bot.send_message(chat_id, "❌ Недостаточно средств")
            return
        
        for admin in config.ADMIN_IDS:
            bot.send_message(admin, f"💸 Запрос на вывод\nПользователь: @{user['name']}\nID: {chat_id}\nСумма: {amount} RUB")
        
        bot.send_message(chat_id, "📤 Запрос отправлен администратору")
    except:
        bot.send_message(chat_id, "❌ Введите число")

def process_donate(message, bot, crypto, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.main_menu)
        return
    
    try:
        amount = int(message.text)
        if amount < 5:
            bot.send_message(chat_id, "❌ Минимум 5 RUB")
            return
        
        invoice = crypto.create_invoice(amount, 'USDT', 'Донат')
        if invoice:
            db.add_invoice(invoice['invoice_id'], chat_id, amount, 'USDT', 0, 'donate')
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                types.InlineKeyboardButton('💳 Оплатить', url=invoice['pay_url']),
                types.InlineKeyboardButton('✅ Проверить', callback_data=f'check_pay_{invoice["invoice_id"]}')
            )
            bot.send_message(chat_id, f"🎁 Спасибо за донат {amount} RUB!", reply_markup=keyboard)
    except:
        bot.send_message(chat_id, "❌ Введите число")