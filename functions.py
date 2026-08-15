import time
from datetime import datetime
import telebot
from telebot import types

def autoposting(bot, db):
    """Автопостинг в канал"""
    print("aвтопостинг запущен")
    
    while True:
        current_time = datetime.now().strftime("%H-%M")
        post_times = ["10-00", "14-00", "18-00", "22-00", "02-00", "06-00"]
        
        if current_time in post_times:
            try:
                settings = db.get_settings()
                post = db.get_post()
                
                if post and settings['channal']:
                    keyboard = create_keyboard(post['buttons'])
                    
                    try:
                        bot.send_message(
                            chat_id=settings['channal'],
                            text=post['text'],
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                        print(f"📰 Пост опубликован в {current_time}")
                    except Exception as e:
                        print(f"Ошибка публикации: {e}")
                    
                    time.sleep(7200)
            except Exception as e:
                print(f"Ошибка автопостинга: {e}")
        
        time.sleep(60)

def create_keyboard(buttons_text):
    """Создание клавиатуры из текста"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    if not buttons_text:
        return keyboard
    
    lines = buttons_text.split('\n')
    
    for line in lines:
        if not line.strip():
            continue
        
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            line = line[1:-1]
        
        buttons = line.split('][')
        row_buttons = []
        
        for btn in buttons:
            btn = btn.strip()
            if ' + ' in btn:
                text, url = btn.split(' + ', 1)
                row_buttons.append(
                    types.InlineKeyboardButton(
                        text=text.strip(),
                        url=url.strip()
                    )
                )
        
        if row_buttons:
            keyboard.row(*row_buttons)
    
    return keyboard