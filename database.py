from telebot import types

main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add('🔍 Найти user', '🤝 Мои сделки')
main_menu.add('🎩 Мой профиль', '🎁 Пожертвовать')
main_menu.add('💬 Помощь')

admin_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
admin_menu.add('📊 Статистика', '📨 Рассылка')
admin_menu.add('💰 Изменить баланс', '📢 Канал')
admin_menu.add('💳 Комиссия', '📝 Описание')
admin_menu.add('📰 Автопостинг')
admin_menu.row('🔙 Назад')

profile_menu = types.InlineKeyboardMarkup(row_width=2)
profile_menu.add(
    types.InlineKeyboardButton('💰 Пополнить', callback_data='deposit'),
    types.InlineKeyboardButton('💸 Вывести', callback_data='withdraw')
)

donate_menu = types.InlineKeyboardMarkup(row_width=1)
donate_menu.add(
    types.InlineKeyboardButton('🎁 Пожертвовать', callback_data='donate'),
    types.InlineKeyboardButton('🏆 Топ донатов', callback_data='top_donate')
)

back = types.ReplyKeyboardMarkup(resize_keyboard=True)
back.add('❌ Отмена')

update_name = types.InlineKeyboardMarkup(row_width=2)
update_name.add(
    types.InlineKeyboardButton('❓ Как пользоваться?', callback_data='how'),
    types.InlineKeyboardButton('👨‍💻 Поддержка', url='https://t.me/your_support')
)