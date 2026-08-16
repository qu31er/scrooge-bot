import telebot
from telebot import types
import time
import config
import menu
from database import Database
from crypto import CryptoBot

def register_all_handlers(bot, db, crypto):
    """Регистрация всех обработчиков"""
    
    # ============ ТЕКСТОВЫЕ СООБЩЕНИЯ ============
    
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
                return
            elif text == '📨 Рассылка':
                msg = bot.send_message(chat_id, "📨 Введите текст рассылки:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, process_mailing, bot, db)
                return
            elif text == '💰 Изменить баланс':
                msg = bot.send_message(chat_id, "💰 Введите ID пользователя:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, ask_balance_amount, db)
                return
            elif text == '📢 Канал':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"📢 Текущий канал: {settings['channal']}\nОтправьте новый:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_channel, db)
                return
            elif text == '💳 Комиссия':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"💳 Текущая комиссия: {settings['commission']}%\nВведите новую (0-50):", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_commission, db)
                return
            elif text == '📝 Описание':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"📝 Текущее описание:\n{settings['help']}\n\nОтправьте новый текст:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_help, db)
                return
            elif text == '📰 Автопостинг':
                msg = bot.send_message(chat_id, "📰 Отправьте текст поста:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, ask_post_buttons, db)
                return
            elif text == '🔙 Назад':
                bot.send_message(chat_id, "👑 Панель администратора", reply_markup=menu.admin_menu)
                return
        
        # ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ
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
        elif text == '🏦 Вывод средств':
            msg = bot.send_message(chat_id, "💸 Введите ID пользователя и сумму через пробел:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, admin_withdraw, db)
    
    # ============ CALLBACK ОБРАБОТЧИКИ ============
    
    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        chat_id = call.message.chat.id
        data = call.data
        
        # Пополнение баланса
        if data == 'deposit':
            msg = bot.send_message(chat_id, "💰 Введите сумму пополнения (минимум 10 RUB):", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_deposit, bot, crypto, db)
        
        # Вывод средств
        elif data == 'withdraw':
            msg = bot.send_message(chat_id, "💰 Введите сумму вывода:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_withdraw, bot, crypto, db)
        
        # Донат
        elif data == 'donate':
            msg = bot.send_message(chat_id, "🎁 Введите сумму доната (минимум 5 RUB):", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_donate, bot, crypto, db)
        
        # Топ донатов
        elif data == 'top_donate':
            show_top_donates(chat_id, db)
        
        # Как пользоваться
        elif data == 'how':
            bot.send_message(
                chat_id,
                "📖 <b>Как пользоваться ботом:</b>\n\n"
                "1️⃣ Найти продавца через 🔍 Найти user\n"
                "2️⃣ Нажать 💰 Сделка и ввести сумму\n"
                "3️⃣ Оплатить счет через @CryptoBot\n"
                "4️⃣ После оплаты продавец получает товар\n"
                "5️⃣ Завершить сделку или открыть спор\n\n"
                "⚡️ Все сделки безопасны!",
                parse_mode="HTML"
            )
        
        # Сделка с пользователем
        elif data.startswith('deal_'):
            user_id = data.split('_')[1]
            msg = bot.send_message(chat_id, f"💰 Введите сумму сделки (минимум 10 RUB):", reply_markup=menu.back)
            bot.register_next_step_handler(msg, create_deal, user_id, bot, db, crypto)
        
        # Отзывы о пользователе
        elif data.startswith('feed_'):
            user_id = data.split('_')[1]
            show_feedback(chat_id, user_id, db)
        
        # Завершить сделку
        elif data.startswith('sale_end_'):
            sale_id = int(data.split('_')[2])
            complete_sale(chat_id, sale_id, bot, db)
        
        # Отменить сделку
        elif data.startswith('sale_back_'):
            sale_id = int(data.split('_')[2])
            cancel_sale(chat_id, sale_id, bot, db)
        
        # Открыть спор
        elif data.startswith('dispute_'):
            sale_id = int(data.split('_')[1])
            open_dispute(chat_id, sale_id, bot, db)
        
        # Проверка оплаты
        elif data.startswith('check_pay_'):
            invoice_id = data.split('_')[2]
            check_payment(chat_id, invoice_id, bot, crypto, db)
        
        # Вывод средств (админ)
        elif data.startswith('withdraw_accept_'):
            parts = data.split('_')
            user_id = int(parts[2])
            amount = int(parts[3])
            admin_withdraw_accept(chat_id, user_id, amount, bot, db, crypto)
        
        elif data.startswith('withdraw_reject_'):
            user_id = int(data.split('_')[2])
            admin_withdraw_reject(chat_id, user_id, bot, db)
        
        bot.answer_callback_query(call.id)
    
    print("✅ Все обработчики зарегистрированы")

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============

def show_statistics(chat_id, db):
    users = db.get_all_users()
    total_balance = sum(u['balance'] for u in users)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        sales = cursor.execute('SELECT COUNT(*), SUM(sum) FROM sale WHERE id != 0').fetchone()
        disputes = cursor.execute('SELECT COUNT(*) FROM dispute').fetchone()
        donates = cursor.execute('SELECT COUNT(*), SUM(sum) FROM donate').fetchone()
    
    text = f"""
📊 <b>Статистика</b>

👥 Пользователей: {len(users)}
💰 Общий баланс: {total_balance} RUB

🤝 Сделок: {sales[0] or 0}
💳 На сумму: {sales[1] or 0} RUB

⚖️ Споров: {disputes[0] or 0}
🎁 Донатов: {donates[0] or 0}
    """
    bot.send_message(chat_id, text, parse_mode="HTML")

def process_mailing(message, bot, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    users = db.get_all_users()
    success = 0
    fail = 0
    
    for user in users:
        try:
            bot.send_message(user['user_id'], message.text, parse_mode="HTML")
            success += 1
        except:
            fail += 1
        time.sleep(0.05)
    
    bot.send_message(
        chat_id,
        f"✅ Рассылка завершена!\n📤 Отправлено: {success}\n📥 Не доставлено: {fail}",
        reply_markup=menu.admin_menu
    )

def ask_balance_amount(message, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    user_id = message.text
    msg = bot.send_message(chat_id, f"💰 Введите новую сумму для пользователя {user_id}:", reply_markup=menu.back)
    bot.register_next_step_handler(msg, change_balance, user_id, db)

def change_balance(message, user_id, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    try:
        amount = int(message.text)
        if not db.get_user(user_id):
            bot.send_message(chat_id, f"❌ Пользователь {user_id} не найден")
            return
        
        db.set_balance(user_id, amount)
        bot.send_message(
            chat_id,
            f"✅ Баланс пользователя {user_id} установлен на {amount} RUB",
            reply_markup=menu.admin_menu
        )
    except:
        bot.send_message(chat_id, "❌ Ошибка! Введите число")

def change_channel(message, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    db.update_setting('channal', message.text)
    bot.send_message(chat_id, f"✅ Канал обновлен: {message.text}", reply_markup=menu.admin_menu)

def change_commission(message, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
        return
    
    try:
        commission = int(message.text)
        if 0 <= commission <= 50:
            db.update_setting('commission', commission)
            bot.send_message(chat_id, f"✅ Комиссия обновлена до {commission}%", reply_markup=menu.admin_menu)
        else:
            bot.send_message(chat_id, "❌ Введите число от 0 до 50")
    except:
        bot.send_message(chat_id, "❌ Ошибка! Введите число")

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
    
    msg = bot.send_message(
        chat_id,
        "📎 Отправьте кнопки в формате:\n[Текст + ссылка]\n\nПример:\n[Канал + https://t.me/channel]",
        reply_markup=menu.back
    )
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
    text = f"""
🎩 <b>Профиль</b>

👤 @{user['name']}
📝 Статус: {user['status']}
💰 Баланс: {user['balance']} RUB
💬 Отзывов: {len(feedbacks)}

🤝 Продаж: {user['sell']} шт.
🛒 Покупок: {user['buy']} шт.
    """
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=menu.profile_menu)

def show_my_deals(chat_id, bot, db):
    sales = db.get_user_sales(chat_id)
    if not sales:
        bot.send_message(chat_id, "❌ Нет активных сделок", reply_markup=menu.main_menu)
        return
    
    for sale in sales:
        text = f"""
🤝 <b>Сделка #{sale['id']}</b>

От: @{sale['name']}
Для: @{sale['name2']}
Сумма: {sale['sum']} RUB
        """
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
        
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)

def search_user(chat_id, username, bot, db):
    user = db.get_user_by_name(username)
    if not user:
        bot.send_message(chat_id, "❌ Пользователь не найден")
        return
    
    if user['user_id'] == str(chat_id):
        bot.send_message(chat_id, "ℹ️ Это ваш профиль")
        return
    
    feedbacks = db.get_feedback(user['user_id'])
    text = f"""
👤 <b>Профиль</b>

📝 Статус: {user['status']}
💬 Отзывов: {len(feedbacks)}

🤝 Продаж: {user['sell']} шт.
🛒 Покупок: {user['buy']} шт.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton('💰 Сделка', callback_data=f'deal_{user["user_id"]}'),
        types.InlineKeyboardButton('⭐️ Отзывы', callback_data=f'feed_{user["user_id"]}')
    )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)

def create_deal(message, seller_id, bot, db, crypto):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Сделка отменена", reply_markup=menu.main_menu)
        return
    
    try:
        amount = int(message.text)
        if amount < 10:
            bot.send_message(chat_id, "❌ Минимальная сумма 10 RUB")
            return
        
        user = db.get_user(chat_id)
        seller = db.get_user(seller_id)
        if not user or not seller:
            bot.send_message(chat_id, "❌ Ошибка: пользователь не найден")
            return
        
        if user['balance'] < amount:
            bot.send_message(chat_id, "❌ Недостаточно средств на балансе")
            return
        
        # Создаем сделку
        sale_id = db.create_sale(chat_id, user['name'], seller_id, seller['name'], amount)
        
        # Создаем инвойс в Crypto Bot
        invoice = crypto.create_invoice(amount, 'USDT', f'Сделка #{sale_id}')
        if invoice:
            db.add_invoice(invoice['invoice_id'], chat_id, amount, 'USDT', sale_id, 'deal')
            
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                types.InlineKeyboardButton('💳 Оплатить', url=invoice['pay_url']),
                types.InlineKeyboardButton('✅ Проверить оплату', callback_data=f'check_pay_{invoice["invoice_id"]}')
            )
            
            bot.send_message(
                chat_id,
                f"💳 Оплатите {amount} RUB через @CryptoBot",
                reply_markup=keyboard
            )
            
            bot.send_message(
                seller_id,
                f"🆕 <b>Новая сделка!</b>\n\nНомер: #{sale_id}\nПокупатель: @{user['name']}\nСумма: {amount} RUB",
                parse_mode="HTML"
            )
        else:
            bot.send_message(chat_id, "❌ Ошибка создания счета")
    except ValueError:
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
            # Завершаем сделку
            db.complete_sale(inv_data['deal_id'])
            bot.send_message(chat_id, f"✅ Сделка #{inv_data['deal_id']} завершена!")
        else:
            # Пополняем баланс
            db.update_balance(inv_data['user_id'], inv_data['amount'])
            bot.send_message(chat_id, f"✅ Баланс пополнен на {inv_data['amount']} RUB")
    else:
        bot.send_message(chat_id, f"⏳ Счет еще не оплачен. Статус: {invoice['status']}")

def complete_sale(chat_id, sale_id, bot, db):
    sale = db.get_sale(sale_id)
    if not sale:
        bot.send_message(chat_id, "❌ Сделка не найдена")
        return
    
    if db.complete_sale(sale_id):
        bot.send_message(chat_id, f"✅ Сделка #{sale_id} завершена!")
        bot.send_message(
            sale['user_id2'],
            f"✅ Сделка #{sale_id} завершена!\nСумма: {sale['sum']} RUB"
        )

def cancel_sale(chat_id, sale_id, bot, db):
    sale = db.get_sale(sale_id)
    if not sale:
        bot.send_message(chat_id, "❌ Сделка не найдена")
        return
    
    if db.cancel_sale(sale_id):
        bot.send_message(chat_id, f"❌ Сделка #{sale_id} отменена")
        bot.send_message(
            sale['user_id'],
            f"❌ Сделка #{sale_id} отменена. Деньги возвращены"
        )

def open_dispute(chat_id, sale_id, bot, db):
    sale = db.get_sale(sale_id)
    if not sale:
        bot.send_message(chat_id, "❌ Сделка не найдена")
        return
    
    db.create_dispute(sale_id, sale['user_id'], sale['name'], sale['user_id2'], sale['name2'], sale['sum'])
    
    bot.send_message(chat_id, f"⚖️ Спор по сделке #{sale_id} открыт")
    
    for admin in config.ADMIN_IDS:
        bot.send_message(
            admin,
            f"⚖️ <b>Новый спор!</b>\n\nСделка #{sale_id}\nПокупатель: @{sale['name']}\nПродавец: @{sale['name2']}\nСумма: {sale['sum']} RUB",
            parse_mode="HTML"
        )

def show_feedback(chat_id, user_id, db):
    feedbacks = db.get_feedback(user_id)
    if not feedbacks:
        bot.send_message(chat_id, "📝 Отзывов пока нет")
        return
    
    text = "⭐️ <b>Отзывы:</b>\n\n"
    for fb in feedbacks[:5]:
        text += f"👤 @{fb['name2']}: {fb['text']}\n"
    
    bot.send_message(chat_id, text, parse_mode="HTML")

def show_top_donates(chat_id, db):
    donates = db.get_top_donates()
    if not donates:
        bot.send_message(chat_id, "📊 Пока нет донатов")
        return
    
    text = "🏆 <b>Топ донатеров:</b>\n\n"
    for i, donate in enumerate(donates, 1):
        text += f"{i}. {donate['user_id']} - {donate['total']} RUB\n"
    
    bot.send_message(chat_id, text, parse_mode="HTML")

def process_deposit(message, bot, crypto, db):
    chat_id = message.chat.id
    if message.text == '❌ Отмена':
        bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.main_menu)
        return
    
    try:
        amount = int(message.text)
        if amount < 10:
            bot.send_message(chat_id, "❌ Минимальная сумма 10 RUB")
            return
        
        invoice = crypto.create_invoice(amount, 'USDT', 'Пополнение баланса')
        if invoice:
            db.add_invoice(invoice['invoice_id'], chat_id, amount, 'USDT', 0, 'deposit')
            
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                types.InlineKeyboardButton('💳 Оплатить', url=invoice['pay_url']),
                types.InlineKeyboardButton('✅ Проверить оп