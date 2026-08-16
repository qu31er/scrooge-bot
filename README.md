# Scrooge Garant Bot

**Оригинальный репозиторий:** https://github.com/qu31er/Scrooge-bot
**Telegram канал:** https://t.me/killer2017official
**Автор:** @killer2017official
**Версия:** 1.0.0
**Статус:** ✅ Активен

---

## 📋 Описание

Бот для безопасных сделок с криптовалютой через Telegram Crypto Bot. Позволяет пользователям совершать гарантированные сделки с USDT, пополнять баланс, выводить средства, оставлять отзывы и получать поддержку. Администраторы могут управлять пользователями, настраивать комиссию, делать рассылки и просматривать статистику.

---

## ✨ Возможности

🔐 Безопасные сделки между пользователями с гарантом
💰 Прием платежей через Crypto Bot (USDT)
💳 Пополнение баланса с автоматическим учетом комиссии
💸 Вывод средств на TON кошелек
👑 Админ-панель с управлением балансом по юзернейму
📨 Рассылки пользователям
📰 Автопостинг в канал
⭐️ Система отзывов и споров
📊 Статистика пользователей и транзакций
🎁 Донаты и топ донатеров

---

## 🛠 Технологии

Python 3.10+
pyTelegramBotAPI
Flask (для Webhook на Railway)
SQLite3
Crypto Bot API
Railway (хостинг)

---

## 📦 Установка

Клонирование репозитория:
git clone https://github.com/qu31er/Scrooge-bot.git
cd Scrooge-bot

Создание виртуального окружения:
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

Установка зависимостей:
pip install -r requirements.txt

Инициализация базы данных:
python init_db.py

Запуск бота:
python main.py

---

## ⚙️ Переменные окружения

Обязательные:
BOT_TOKEN=7929405594:AAHNS9y-6jVunV_Bb7D-9qN7E-6JjVunV_Bb7D
CRYPTO_TOKEN=123456:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789,987654321

Опциональные:
COMMISSION=5
CHANNEL=@your_channel
HELP_TEXT=Бот для безопасных сделок с криптовалютой
WEBHOOK_URL=https://ваш-проект.railway.app

---

## 🚀 Деплой на Railway

1. Создайте репозиторий на GitHub и загрузите проект
2. На Railway выберите "Deploy from GitHub repo"
3. Добавьте переменные окружения
4. Нажмите Deploy

---

## 📁 Структура проекта

Scrooge-bot/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── database.py          # Работа с БД
├── crypto.py            # Интеграция с Crypto Bot
├── handlers.py          # Обработчики команд
├── functions.py         # Вспомогательные функции
├── menu.py              # Клавиатуры
├── init_db.py           # Инициализация БД
├── requirements.txt     # Зависимости
├── Procfile             # Запуск на Railway
├── railway.json         # Настройки Railway
├── .gitignore           # Игнорируемые файлы
└── README.md            # Документация

---

## 📱 Команды

/start - Запуск бота и главное меню
/admin - Панель администратора

Кнопки в главном меню:
🔍 Найти user - Поиск пользователя по @username
🤝 Мои сделки - Просмотр активных сделок
🎩 Мой профиль - Баланс, статус, отзывы
🎁 Пожертвовать - Поддержка проекта
💬 Помощь - Информация о боте

Кнопки в профиле:
💰 Пополнить - Пополнение баланса (мин 1 USDT)
💸 Вывести - Запрос на вывод (мин 1 USDT)

Админ-панель:
📊 Статистика - Общая статистика бота
📨 Рассылка - Массовая рассылка
💰 Изменить баланс - Прибавить/отнять USDT по @username
📢 Канал - Настройка канала для автопостинга
💳 Комиссия - Изменение комиссии (0-50%)
📝 Описание - Текст помощи
📰 Автопостинг - Настройка поста
🔙 Назад - Выход из админ-панели

---

## 📄 Лицензия

MIT License

Copyright (c) 2024 Scrooge Garant Bot

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

---

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку (git checkout -b feature/AmazingFeature)
3. Закоммитьте изменения (git commit -m 'Add some AmazingFeature')
4. Запушьте (git push origin feature/AmazingFeature)
5. Откройте Pull Request

---

## ⭐️ Поддержка

Если проект вам полезен, поставьте звезду ⭐️ на GitHub и подпишитесь на Telegram канал: https://t.me/killer2017official