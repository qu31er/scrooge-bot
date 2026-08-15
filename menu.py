from telebot import types

#меню
main_menu = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
main_menu.add(
    '🔍 Найти user',
    '🤝 Мои сделки',
    '🎩 Мой профиль',
    '🎁 Пожертвовать',
    '💬 Помощь'
)

#админка
admin_menu = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
admin_menu.add(
    '📊 Статистика',
    '📨 Рассылка',
    '💰 Изменить баланс',
    '📢 Канал',
    '💳 Комиссия',
    '📝 Описание',
    '📰 Автопостинг'
)
admin_menu.row('🔙 Назад')

#профиль
profile_menu = types.InlineKeyboardMarkup(row_width=2)
profile_menu.add(
    types.InlineKeyboardButton('💰 Пополнить', callback_data='deposit'),
    types.InlineKeyboardButton('💸 Вывести', callback_data='withdraw')
)

#донаты
donate_menu = types.InlineKeyboardMarkup(row_width=1)
donate_menu.add(
    types.InlineKeyboardButton('🎁 Пожертвовать', callback_data='donate'),
    types.InlineKeyboardButton('🏆 Топ донатов', callback_data='top_donate')
)

#назад
back = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
back.add('❌ Отмена')

#помощь
update_name = types.InlineKeyboardMarkup(row_width=2)
update_name.add(
    types.InlineKeyboardButton('❓ Как пользоваться?', callback_data='how'),
    types.InlineKeyboardButton('👨‍💻 Поддержка', url='https://t.me/your_support')
)