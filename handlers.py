import telebot
from telebot import types
import time
import config
import menu
from database import Database
from crypto import CryptoBot

db = Database()
crypto = CryptoBot()

def register_all_handlers(bot):
    
    # ============ КОМАНДЫ ============
    
    @bot.message_handler(commands=['start'])
    def start_handler(message):
        if message.chat.type != 'private':
            return
        
        chat_id = message.chat.id
        username = message.chat.username or f'user_{chat_id}'
        
        if not db.get_user(chat_id):
            db.add_user(chat_id, username)
        
        bot.send_message(
            chat_id,
            f"👋 Добро пожаловать, @{username}!",
            reply_markup=menu.main_menu
        )
    
    @bot.message_handler(commands=['admin'])
    def admin_handler(message):
        chat_id = message.chat.id
        
        if chat_id not in config.ADMIN_IDS:
            bot.send_message(chat_id, "⛔️ У вас нет прав администратора")
            return
        
        bot.send_message(
            chat_id,
            "👑 Панель администратора",
            reply_markup=menu.admin_menu
        )
    
    # ============ ТЕКСТ ============
    
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
        
        # ===== АДМИН =====
        if chat_id in config.ADMIN_IDS:
            if text == '📊 Статистика':
                users = db.get_all_users()
                bot.send_message(chat_id, f"👥 Пользователей: {len(users)}")
                return
            
            elif text == '📨 Рассылка':
                msg = bot.send_message(chat_id, "📨 Введите текст рассылки:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, process_mailing)
                return
            
            elif text == '💰 Изменить баланс':
                msg = bot.send_message(chat_id, "💰 Введите ID пользователя:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, ask_balance_user)
                return
            
            elif text == '📢 Канал':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"📢 Текущий канал: {settings['channal']}\nОтправьте новый:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_channel)
                return
            
            elif text == '💳 Комиссия':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"💳 Текущая комиссия: {settings['commission']}%\nВведите новую (0-50):", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_commission)
                return
            
            elif text == '📝 Описание':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"📝 Текущее описание:\n{settings['help']}\n\nОтправьте новый текст:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_help)
                return
            
            elif text == '📰 Автопостинг':
                msg = bot.send_message(chat_id, "📰 Отправьте текст поста:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, ask_post_buttons)
                return
            
            elif text == '🔙 Назад':
                bot.send_message(chat_id, "👑 Панель администратора", reply_markup=menu.admin_menu)
                return
        
        # ===== ПОЛЬЗОВАТЕЛЬ =====
        if text == '💬 Помощь':
            settings = db.get_settings()
            bot.send_message(chat_id, settings['help'])
        
        elif text == '🎩 Мой профиль':
            show_profile(chat_id)
        
        elif text == '🤝 Мои сделки':
            show_my_deals(chat_id)
        
        elif text == '🔍 Найти user':
            bot.send_message(chat_id, "👤 Введите никнейм в формате @username")
        
        elif text.startswith('@') and len(text) > 1:
            search_user(chat_id, text[1:])
        
        elif text == '🎁 Пожертвовать':
            bot.send_message(chat_id, "🎁 Пожертвования", reply_markup=menu.donate_menu)
        
        elif text in ['❌ Отмена', '🔙 Назад', 'Вернуться в главное меню']:
            bot.send_message(chat_id, "🏠 Главное меню", reply_markup=menu.main_menu)
    
    # ============ CALLBACK (КНОПКИ) ============
    
    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        chat_id = call.message.chat.id
        data = call.data
        
        print(f"🔔 Callback: {data}")  # ← ВАЖНО ДЛЯ ЛОГОВ
        
        if data == 'deposit':
            msg = bot.send_message(chat_id, "💰 Введите сумму пополнения:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_deposit)
        
        elif data == 'withdraw':
            msg = bot.send_message(chat_id, "💰 Введите сумму вывода:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_withdraw)
        
        elif data == 'donate':
            msg = bot.send_message(chat_id, "🎁 Введите сумму доната:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_donate)
        
        elif data == 'top_donate':
            show_top_donates(chat_id)
        
        elif data == 'how':
            bot.send_message(chat_id, "📖 Как пользоваться ботом...")
        
        elif data.startswith('deal_'):
            user_id = data.split('_')[1]
            msg = bot.send_message(chat_id, f"💰 Введите сумму сделки:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, create_deal, user_id)
        
        elif data.startswith('feed_'):
            user_id = data.split('_')[1]
            show_feedback(chat_id, user_id)
        
        elif data.startswith('sale_end_'):
            sale_id = int(data.split('_')[2])
            complete_sale(chat_id, sale_id)
        
        elif data.startswith('sale_back_'):
            sale_id = int(data.split('_')[2])
            cancel_sale(chat_id, sale_id)
        
        elif data.startswith('dispute_'):
            sale_id = int(data.split('_')[1])
            open_dispute(chat_id, sale_id)
        
        elif data.startswith('check_pay_'):
            invoice_id = data.split('_')[2]
            check_payment(chat_id, invoice_id)
        
        bot.answer_callback_query(call.id)
    
    # ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============
    
    def show_profile(chat_id):
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
        """
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=menu.profile_menu)
    
    def show_my_deals(chat_id):
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
    
    def search_user(chat_id, username):
        user = db.get_user_by_name(username)
        if not user:
            bot.send_message(chat_id, "❌ Пользователь не найден")
            return
        
        feedbacks = db.get_feedback(user['user_id'])
        text = f"""
👤 <b>Профиль</b>

📝 Статус: {user['status']}
💬 Отзывов: {len(feedbacks)}
        """
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton('💰 Сделка', callback_data=f'deal_{user["user_id"]}'),
            types.InlineKeyboardButton('⭐️ Отзывы', callback_data=f'feed_{user["user_id"]}')
        )
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)
    
    def create_deal(message, seller_id):
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
                bot.send_message(seller_id, f"🆕 Сделка #{sale_id}")
        except:
            bot.send_message(chat_id, "❌ Введите число")
    
    def check_payment(chat_id, invoice_id):
        invoice = crypto.check_invoice(invoice_id)
        if not invoice:
            bot.send_message(chat_id, "❌ Счет не найден")
            return
        
        if invoice['status'] == 'paid':
            db.update_invoice_status(invoice_id, 'paid')
            inv_data = db.get_invoice(invoice_id)
            
            if inv_data and inv_data['type'] == 'deal':
                db.complete_sale(inv_data['deal_id'])
                bot.send_message(chat_id, f"✅ Сделка завершена!")
            else:
                db.update_balance(inv_data['user_id'], inv_data['amount'])
                bot.send_message(chat_id, f"✅ Баланс пополнен на {inv_data['amount']} RUB")
        else:
            bot.send_message(chat_id, f"⏳ Статус: {invoice['status']}")
    
    def complete_sale(chat_id, sale_id):
        sale = db.get_sale(sale_id)
        if not sale:
            bot.send_message(chat_id, "❌ Сделка не найдена")
            return
        
        if db.complete_sale(sale_id):
            bot.send_message(chat_id, f"✅ Сделка #{sale_id} завершена!")
            bot.send_message(sale['user_id2'], f"✅ Сделка #{sale_id} завершена!")
    
    def cancel_sale(chat_id, sale_id):
        sale = db.get_sale(sale_id)
        if not sale:
            bot.send_message(chat_id, "❌ Сделка не найдена")
            return
        
        if db.cancel_sale(sale_id):
            bot.send_message(chat_id, f"❌ Сделка #{sale_id} отменена")
            bot.send_message(sale['user_id'], f"❌ Сделка #{sale_id} отменена")
    
    def open_dispute(chat_id, sale_id):
        sale = db.get_sale(sale_id)
        if not sale:
            bot.send_message(chat_id, "❌ Сделка не найдена")
            return
        
        db.create_dispute(sale_id, sale['user_id'], sale['name'], sale['user_id2'], sale['name2'], sale['sum'])
        bot.send_message(chat_id, f"⚖️ Спор #{sale_id} открыт")
        
        for admin in config.ADMIN_IDS:
            bot.send_message(admin, f"⚖️ Новый спор!\nСделка #{sale_id}")
    
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
    
    def process_deposit(message):
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
    
    def process_withdraw(message):
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
                bot.send_message(admin, f"💸 Запрос на вывод\nПользователь: @{user['name']}\nСумма: {amount} RUB")
            
            bot.send_message(chat_id, "📤 Запрос отправлен администратору")
        except:
            bot.send_message(chat_id, "❌ Введите число")
    
    def process_donate(message):
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
    
    # ===== АДМИН ШАГИ =====
    
    def process_mailing(message):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
            return
        
        users = db.get_all_users()
        ok = 0
        for user in users:
            try:
                bot.send_message(user['user_id'], message.text, parse_mode="HTML")
                ok += 1
            except:
                pass
            time.sleep(0.05)
        
        bot.send_message(chat_id, f"✅ Отправлено {ok} из {len(users)}", reply_markup=menu.admin_menu)
    
    def ask_balance_user(message):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
            return
        
        user_id = message.text
        msg = bot.send_message(chat_id, f"💰 Введите новую сумму для {user_id}:", reply_markup=menu.back)
        bot.register_next_step_handler(msg, change_balance, user_id)
    
    def change_balance(message, user_id):
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
            bot.send_message(chat_id, f"✅ Баланс {user_id} = {amount} RUB", reply_markup=menu.admin_menu)
        except:
            bot.send_message(chat_id, "❌ Ошибка!")
    
    def change_channel(message):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
            return
        
        db.update_setting('channal', message.text)
        bot.send_message(chat_id, f"✅ Канал: {message.text}", reply_markup=menu.admin_menu)
    
    def change_commission(message):
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
    
    def change_help(message):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
            return
        
        db.update_setting('help', message.text)
        bot.send_message(chat_id, "✅ Описание обновлено", reply_markup=menu.admin_menu)
    
    def ask_post_buttons(message):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
            return
        
        msg = bot.send_message(chat_id, "отправьте кнопки:", reply_markup=menu.back)
        bot.register_next_step_handler(msg, save_post, message.text)
    
    def save_post(message, text):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
            return
        
        db.update_post(text, message.text)
        bot.send_message(chat_id, "пост сохранен", reply_markup=menu.admin_menu)
    
    print("все обработчики зарегистрированы")