import telebot
from telebot import types
import time
import config
import menu
from database import Database
from crypto import CryptoBot

db = Database()
crypto = CryptoBot()

# ============================================================
# ФУНКЦИЯ ДЛЯ ОТПРАВКИ ЧЕКА ЧЕРЕЗ @send
# ============================================================

def send_check(chat_id, amount, comment=""):
    """Отправка чека через @send бота"""
    try:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            types.InlineKeyboardButton(
                text="💰 Создать чек",
                url=f"https://t.me/send?start={amount}_USDT"
            )
        )
        
        bot.send_message(
            chat_id,
            f"🧾 <b>Чек на {amount} USDT</b>\n\n"
            f"{comment}\n\n"
            f"Нажмите кнопку ниже для создания чека:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки чека: {e}")
        return False

# ============================================================
# РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ
# ============================================================

def register_all_handlers(bot):
    
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
        
        # АДМИН
        if chat_id in config.ADMIN_IDS:
            if text == '📊 Статистика':
                users = db.get_all_users()
                total_balance = sum(u['balance'] for u in users)
                bot.send_message(chat_id, f"📊 Статистика\n\n👥 Пользователей: {len(users)}\n💰 Баланс: {total_balance} USDT")
                return
            
            elif text == '📨 Рассылка':
                msg = bot.send_message(chat_id, "📨 Введите текст рассылки:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, process_mailing)
                return
            
            elif text == '💰 Изменить баланс':
                msg = bot.send_message(chat_id, "💰 Введите @username и сумму через пробел\nПример: @user 100\nДля вычитания: @user -100", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_balance_by_username)
                return
            
            elif text == '📢 Канал':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"📢 Текущий канал: {settings['channal']}\nОтправьте новый:", reply_markup=menu.back)
                bot.register_next_step_handler(msg, change_channel)
                return
            
            elif text == '💳 Комиссия':
                settings = db.get_settings()
                msg = bot.send_message(chat_id, f"💳 Текущая комиссия вывода: {settings['commission']}%\nВведите новую (0-50):", reply_markup=menu.back)
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
        
        # ПОЛЬЗОВАТЕЛЬ
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
            bot.send_message(chat_id, "🎁 Пожертвования USDT", reply_markup=menu.donate_menu)
        
        elif text in ['❌ Отмена', '🔙 Назад', 'Вернуться в главное меню']:
            bot.send_message(chat_id, "🏠 Главное меню", reply_markup=menu.main_menu)
    
    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        chat_id = call.message.chat.id
        data = call.data
        
        print(f"🔔 Callback: {data}")
        
        if data == 'deposit':
            msg = bot.send_message(chat_id, "💰 Введите сумму пополнения (мин 1 USDT):", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_deposit)
        
        elif data == 'withdraw':
            msg = bot.send_message(chat_id, "💸 Введите сумму вывода (мин 1 USDT):", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_withdraw_step1)
        
        elif data == 'donate':
            msg = bot.send_message(chat_id, "🎁 Введите сумму доната (мин 0.1 USDT):", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_donate)
        
        elif data == 'top_donate':
            show_top_donates(chat_id)
        
        elif data == 'how':
            bot.send_message(chat_id, "📖 Как пользоваться ботом...")
        
        elif data.startswith('deal_'):
            user_id = data.split('_')[1]
            msg = bot.send_message(chat_id, f"💰 Введите сумму сделки (мин 1 USDT):", reply_markup=menu.back)
            bot.register_next_step_handler(msg, create_deal, user_id)
        
        elif data.startswith('feed_'):
            user_id = data.split('_')[1]
            show_feedback(chat_id, user_id)
        
        elif data.startswith('confirm_sale_'):
            sale_id = int(data.split('_')[2])
            confirm_sale(chat_id, sale_id)
        
        elif data.startswith('sale_back_'):
            sale_id = int(data.split('_')[2])
            cancel_sale(chat_id, sale_id)
        
        elif data.startswith('dispute_'):
            sale_id = int(data.split('_')[1])
            open_dispute(chat_id, sale_id)
        
        elif data.startswith('check_pay_'):
            invoice_id = data.split('_')[2]
            check_payment(chat_id, invoice_id)
        
        elif data.startswith('withdraw_accept_'):
            parts = data.split('_')
            user_id = int(parts[2])
            amount = int(parts[3])
            admin_withdraw_accept(chat_id, user_id, amount)
        
        elif data.startswith('withdraw_reject_'):
            user_id = int(data.split('_')[2])
            admin_withdraw_reject(chat_id, user_id)
        
        bot.answer_callback_query(call.id)
    
    # ============================================================
    # ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    # ============================================================
    
    def show_profile(chat_id):
        user = db.get_user(chat_id)
        if not user:
            return
        
        feedbacks = db.get_feedback(chat_id)
        text = f"""
🎩 <b>Профиль</b>

👤 @{user['name']}
📝 Статус: {user['status']}
💰 Баланс: {user['balance']} USDT
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
Сумма: {sale['sum']} USDT
Статус: {sale['status']}
            """
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            
            if str(chat_id) == sale['user_id']:
                keyboard.add(
                    types.InlineKeyboardButton('❌ Отменить', callback_data=f'sale_back_{sale["id"]}'),
                    types.InlineKeyboardButton('⚖️ Спор', callback_data=f'dispute_{sale["id"]}')
                )
            elif str(chat_id) == sale['user_id2']:
                keyboard.add(
                    types.InlineKeyboardButton('✅ Подтвердить', callback_data=f'confirm_sale_{sale["id"]}'),
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
    
    # ============================================================
    # 1. ПОПОЛНЕНИЕ
    # ============================================================
    
    def process_deposit(message):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.main_menu)
            return
        
        try:
            amount = int(message.text)
            if amount < 1:
                bot.send_message(chat_id, "❌ Минимальная сумма 1 USDT")
                return
            
            invoice = crypto.create_invoice(amount, 'USDT', f'Пополнение баланса')
            if invoice:
                db.add_invoice(invoice['invoice_id'], chat_id, amount, 'USDT', 0, 'deposit')
                
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(
                    types.InlineKeyboardButton('💳 Оплатить', url=invoice['pay_url']),
                    types.InlineKeyboardButton('✅ Проверить', callback_data=f'check_pay_{invoice["invoice_id"]}')
                )
                
                bot.send_message(
                    chat_id,
                    f"💳 Пополните баланс на {amount} USDT",
                    reply_markup=keyboard
                )
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
            
            if inv_data and inv_data['type'] == 'deposit':
                db.update_balance(inv_data['user_id'], inv_data['amount'])
                bot.send_message(
                    chat_id,
                    f"✅ Баланс пополнен на {inv_data['amount']} USDT"
                )
        else:
            bot.send_message(chat_id, f"⏳ Статус: {invoice['status']}")
    
    # ============================================================
    # 2. ВЫВОД (с комиссией и чеком для админов)
    # ============================================================
    
    def process_withdraw_step1(message):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.main_menu)
            return
        
        try:
            amount = int(message.text)
            if amount < 1:
                bot.send_message(chat_id, "❌ Минимум 1 USDT")
                return
            
            user = db.get_user(chat_id)
            if not user or user['balance'] < amount:
                bot.send_message(chat_id, "❌ Недостаточно средств")
                return
            
            msg = bot.send_message(chat_id, "📤 Введите адрес TON кошелька для вывода:", reply_markup=menu.back)
            bot.register_next_step_handler(msg, process_withdraw_step2, amount)
        except:
            bot.send_message(chat_id, "❌ Введите число")
    
    def process_withdraw_step2(message, amount):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.main_menu)
            return
        
        wallet = message.text.strip()
        
        if not wallet or len(wallet) < 10:
            bot.send_message(chat_id, "❌ Неверный адрес кошелька")
            return
        
        user = db.get_user(chat_id)
        
        # Расчет комиссии вывода
        settings = db.get_settings()
        commission = settings['commission']
        commission_amount = int(amount * commission / 100)
        final_amount = amount - commission_amount
        
        # Списываем полную сумму с баланса
        db.update_balance(chat_id, -amount)
        
        # Отправляем запрос админам с чеком
        for admin in config.ADMIN_IDS:
            send_check(
                admin,
                final_amount,
                f"Вывод для @{user['name']}\n"
                f"Запрошено: {amount} USDT\n"
                f"Комиссия ({commission}%): {commission_amount} USDT\n"
                f"Получит: {final_amount} USDT\n"
                f"Кошелек: {wallet}"
            )
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton('✅ Вывести', callback_data=f'withdraw_accept_{chat_id}_{amount}'),
                types.InlineKeyboardButton('❌ Отклонить', callback_data=f'withdraw_reject_{chat_id}')
            )
            
            bot.send_message(
                admin,
                f"💸 <b>Запрос на вывод</b>\n\n"
                f"👤 Пользователь: @{user['name']}\n"
                f"🆔 ID: {chat_id}\n"
                f"💰 Запрошено: {amount} USDT\n"
                f"💳 Комиссия ({commission}%): {commission_amount} USDT\n"
                f"✅ Получит: {final_amount} USDT\n"
                f"📤 Кошелек: {wallet}",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        
        bot.send_message(
            chat_id,
            f"📤 Заявка на вывод {amount} USDT отправлена администраторам!\n"
            f"📤 Кошелек: {wallet}\n"
            f"💳 Комиссия: {commission_amount} USDT ({commission}%)\n"
            f"✅ Вы получите: {final_amount} USDT"
        )
    
    def admin_withdraw_accept(chat_id, user_id, amount):
        bot.send_message(
            user_id,
            f"✅ Ваш вывод {amount} USDT подтвержден администратором!\n"
            f"Средства будут отправлены на указанный кошелек."
        )
        bot.send_message(chat_id, f"✅ Вывод {amount} USDT для пользователя {user_id} подтвержден")
    
    def admin_withdraw_reject(chat_id, user_id):
        # Возвращаем деньги
        bot.send_message(
            user_id,
            f"❌ Ваш запрос на вывод отклонен администратором.\n"
            f"Средства возвращены на баланс."
        )
        bot.send_message(chat_id, f"❌ Вывод для пользователя {user_id} отклонен")
    
    # ============================================================
    # 3. ДОНАТ (мин 0.1 USDT)
    # ============================================================
    
    def process_donate(message):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.main_menu)
            return
        
        try:
            amount = float(message.text.replace(',', '.'))
            if amount < 0.1:
                bot.send_message(chat_id, "❌ Минимальная сумма 0.1 USDT")
                return
            
            user = db.get_user(chat_id)
            if not user or user['balance'] < amount:
                bot.send_message(chat_id, "❌ Недостаточно средств на балансе")
                return
            
            amount = round(amount, 2)
            
            db.update_balance(chat_id, -amount)
            db.add_donate(chat_id, amount)
            
            bot.send_message(
                chat_id,
                f"🎁 Спасибо за донат {amount} USDT!\n"
                f"💰 Новый баланс: {user['balance'] - amount} USDT",
                reply_markup=menu.main_menu
            )
            
            for admin in config.ADMIN_IDS:
                bot.send_message(
                    admin,
                    f"🎁 <b>Новый донат!</b>\n\n"
                    f"👤 Пользователь: @{user['name']}\n"
                    f"💰 Сумма: {amount} USDT",
                    parse_mode="HTML"
                )
        except ValueError:
            bot.send_message(chat_id, "❌ Введите число (например: 0.1)")
    
    # ============================================================
    # 4. СДЕЛКА (исправлена синтаксическая ошибка)
    # ============================================================
    
    def create_deal(message, seller_id):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.main_menu)
            return
        
        try:
            amount = int(message.text)
            if amount < 1:
                bot.send_message(chat_id, "❌ Минимальная сумма 1 USDT")
                return
            
            user = db.get_user(chat_id)
            seller = db.get_user(seller_id)
            
            if not user or not seller:
                bot.send_message(chat_id, "❌ Ошибка: пользователь не найден")
                return
            
            if user['balance'] < amount:
                bot.send_message(chat_id, "❌ Недостаточно средств на балансе")
                return
            
            sale_id = db.create_sale(chat_id, user['name'], seller_id, seller['name'], amount)
            
            seller_keyboard = types.InlineKeyboardMarkup(row_width=2)
            seller_keyboard.add(
                types.InlineKeyboardButton('✅ Подтвердить получение', callback_data=f'confirm_sale_{sale_id}'),
                types.InlineKeyboardButton('⚖️ Спор', callback_data=f'dispute_{sale_id}')
            )
            
            bot.send_message(
                seller_id,
                f"🆕 <b>Новая сделка!</b>\n\n"
                f"Номер: #{sale_id}\n"
                f"Покупатель: @{user['name']}\n"
                f"Сумма: {amount} USDT\n\n"
                f"После получения товара нажмите 'Подтвердить получение'",
                parse_mode="HTML",
                reply_markup=seller_keyboard
            )
            
            buyer_keyboard = types.InlineKeyboardMarkup(row_width=2)
            buyer_keyboard.add(
                types.InlineKeyboardButton('❌ Отменить сделку', callback_data=f'sale_back_{sale_id}'),
                types.InlineKeyboardButton('⚖️ Спор', callback_data=f'dispute_{sale_id}')
            )
            
            bot.send_message(
                chat_id,
                f"✅ Сделка #{sale_id} создана!\n"
                f"💰 Сумма: {amount} USDT заморожена\n"
                f"📤 Продавец: @{seller['name']}\n\n"
                f"Дождитесь получения товара",
                parse_mode="HTML",
                reply_markup=buyer_keyboard
            )
            
        except ValueError:
            bot.send_message(chat_id, "❌ Введите число")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
    
    # ============================================================
    # 5. ПОДТВЕРЖДЕНИЕ СДЕЛКИ
    # ============================================================
    
    def confirm_sale(chat_id, sale_id):
        sale = db.get_sale(sale_id)
        if not sale:
            bot.send_message(chat_id, "❌ Сделка не найдена")
            return
        
        if str(chat_id) != sale['user_id2']:
            bot.send_message(chat_id, "❌ Только продавец может подтвердить сделку")
            return
        
        if sale['status'] == 'completed':
            bot.send_message(chat_id, "❌ Сделка уже завершена")
            return
        
        if db.complete_sale(sale_id):
            bot.send_message(
                sale['user_id'],
                f"✅ Сделка #{sale_id} завершена!\n"
                f"💰 Продавец получил {sale['sum']} USDT",
                reply_markup=menu.main_menu
            )
            
            bot.send_message(
                chat_id,
                f"✅ Сделка #{sale_id} завершена!\n"
                f"💰 Вы получили {sale['sum']} USDT на баланс",
                reply_markup=menu.main_menu
            )
            
            for admin in config.ADMIN_IDS:
                bot.send_message(
                    admin,
                    f"✅ <b>Сделка #{sale_id} завершена!</b>\n\n"
                    f"👤 Покупатель: @{sale['name']}\n"
                    f"👤 Продавец: @{sale['name2']}\n"
                    f"💰 Сумма: {sale['sum']} USDT",
                    parse_mode="HTML"
                )
    
    # ============================================================
    # 6. ОТМЕНА СДЕЛКИ
    # ============================================================
    
    def cancel_sale(chat_id, sale_id):
        sale = db.get_sale(sale_id)
        if not sale:
            bot.send_message(chat_id, "❌ Сделка не найдена")
            return
        
        if db.cancel_sale(sale_id):
            bot.send_message(
                sale['user_id2'],
                f"❌ Сделка #{sale_id} отменена\n"
                f"💰 Деньги возвращены покупателю",
                reply_markup=menu.main_menu
            )
            
            bot.send_message(
                chat_id,
                f"❌ Сделка #{sale_id} отменена\n"
                f"💰 Деньги возвращены на баланс",
                reply_markup=menu.main_menu
            )
    
    # ============================================================
    # 7. СПОРЫ
    # ============================================================
    
    def open_dispute(chat_id, sale_id):
        sale = db.get_sale(sale_id)
        if not sale:
            bot.send_message(chat_id, "❌ Сделка не найдена")
            return
        
        db.create_dispute(sale_id, sale['user_id'], sale['name'], sale['user_id2'], sale['name2'], sale['sum'])
        
        bot.send_message(chat_id, f"⚖️ Спор по сделке #{sale_id} открыт")
        
        for admin in config.ADMIN_IDS:
            bot.send_message(
                admin,
                f"⚖️ <b>Новый спор!</b>\n\n"
                f"Сделка #{sale_id}\n"
                f"Покупатель: @{sale['name']}\n"
                f"Продавец: @{sale['name2']}\n"
                f"Сумма: {sale['sum']} USDT",
                parse_mode="HTML"
            )
    
    # ============================================================
    # 8. АДМИН ФУНКЦИИ
    # ============================================================
    
    def change_balance_by_username(message):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
            return
        
        try:
            parts = message.text.split()
            if len(parts) != 2:
                bot.send_message(chat_id, "❌ Формат: @username 100 или @username -100")
                return
            
            username = parts[0].replace('@', '')
            amount = int(parts[1])
            
            user = db.get_user_by_name(username)
            if not user:
                bot.send_message(chat_id, f"❌ Пользователь @{username} не найден")
                return
            
            db.update_balance(user['user_id'], amount)
            
            action = "➕ Добавлено" if amount > 0 else "➖ Отнято"
            bot.send_message(
                chat_id,
                f"✅ {action} {abs(amount)} USDT пользователю @{username}\n"
                f"💰 Новый баланс: {user['balance'] + amount} USDT",
                reply_markup=menu.admin_menu
            )
        except:
            bot.send_message(chat_id, "❌ Ошибка! Формат: @username 100", reply_markup=menu.admin_menu)
    
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
                bot.send_message(chat_id, f"✅ Комиссия вывода: {commission}%", reply_markup=menu.admin_menu)
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
        
        msg = bot.send_message(chat_id, "📎 Отправьте кнопки:\n[Текст + ссылка]\nПример: [Канал + https://t.me/channel]", reply_markup=menu.back)
        bot.register_next_step_handler(msg, save_post, message.text)
    
    def save_post(message, text):
        chat_id = message.chat.id
        if message.text == '❌ Отмена':
            bot.send_message(chat_id, "❌ Отменено", reply_markup=menu.admin_menu)
            return
        
        db.update_post(text, message.text)
        bot.send_message(chat_id, "✅ Пост сохранен!", reply_markup=menu.admin_menu)
    
    def show_feedback(chat_id, user_id):
        feedbacks = db.get_feedback(user_id)
        if not feedbacks:
            bot.send_message(chat_id, "📝 Отзывов пока нет")
            return
        
        text = "⭐️ <b>Отзывы:</b>\n\n"
        for fb in feedbacks[:5]:
            text += f"👤 @{fb['name2']}: {fb['text']}\n"
        bot.send_message(chat_id, text, parse_mode="HTML")
    
    def show_top_donates(chat_id):
        donates = db.get_top_donates()
        if not donates:
            bot.send_message(chat_id, "📊 Пока нет донатов")
            return
        
        text = "🏆 <b>Топ донатеров:</b>\n\n"
        for i, donate in enumerate(donates, 1):
            text += f"{i}. {donate['user_id']} - {donate['total']} USDT\n"
        bot.send_message(chat_id, text, parse_mode="HTML")
    
    print("✅ Все обработчики зарегистрированы")