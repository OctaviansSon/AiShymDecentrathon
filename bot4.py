# -*- coding: utf-8 -*-
import os
import sqlite3
import google.generativeai as genai
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
import asyncio

# токен не трогать
bot = Bot(token='7902578807:AAGLO2gRKdhZuov5PfyY8ttxyaUCW-VCxfI')
dp = Dispatcher(bot)

#  коонект к бд
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        weight REAL,
        height REAL,
        birth_year INTEGER,
        language TEXT DEFAULT 'Русский'
    )
''')
conn.commit()

# не трогать
genai.configure(api_key='AIzaSyDDMZ55RyEfWOngbg_N61gbhoOHq8_gQZ0')
generation_config = {
    "temperature": 2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-002",
    generation_config=generation_config,
)

# Словари для хранения языков пользователей и их состояния
user_states = {}


def is_user_registered(user_id):
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None

def get_user_language(user_id):
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 'Русский'

# Отправка сообщений в зависимости от языка
async def send_message_with_language(user_id, message_dict, reply_markup=None):
    user_language = get_user_language(user_id)
    message = message_dict.get(user_language, message_dict['English'])
    await bot.send_message(user_id, message, reply_markup=reply_markup)

# Команда /start
@dp.message_handler(commands=['start'])
async def start_bot(message: types.Message):
    user_id = message.from_user.id
    if is_user_registered(user_id):
        await send_message_with_language(user_id, {
            'Русский': "Добро пожаловать! Вы уже зарегистрированы.",
            'English': "Welcome! You are already registered.",
            'Kazakh': "Қош келдіңіздер! Сіз қазірдің өзінде тіркелдіңіз."
        })
        await send_main_menu(user_id)
    else:
        await send_message_with_language(user_id, {
            'Русский': "Добро пожаловать! Пожалуйста, выберите язык.",
            'English': "Welcome! Please choose your language.",
            'Kazakh': "Қош келдіңіздер! Тілді таңдаңыз."
        }, reply_markup=language_menu()) 

# Клавиатура для выбора языка
def language_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Русский 🇷🇺"))
    keyboard.add(KeyboardButton(text="English 🇬🇧"))
    keyboard.add(KeyboardButton(text="Kazakh 🇰🇿"))
    return keyboard

@dp.message_handler(lambda message: message.text in ["Русский 🇷🇺", "English 🇬🇧", "Kazakh 🇰🇿"])
async def choose_language(message: types.Message):
    user_id = message.from_user.id
    language = 'Русский' if message.text == "Русский 🇷🇺" else 'English' if message.text == "English 🇬🇧" else 'Kazakh'
    
    cursor.execute('INSERT OR REPLACE INTO users (user_id, language) VALUES (?, ?)', (user_id, language))
    conn.commit()
    
    await send_message_with_language(user_id, {
        'Русский': "Вы выбрали русский язык.",
        'English': "You have chosen English.",
        'Kazakh': "Сіз қазақ тілін таңдадыңыз."
    })
    
    await ask_for_name(user_id)

# Функция для запроса имени
async def ask_for_name(user_id):
    await send_message_with_language(user_id, {
        'Русский': "Как тебя зовут?",
        'English': "What is your name?",
        'Kazakh': "Сенің атың кім?"
    })
    user_states[user_id] = 'awaiting_name'

@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'awaiting_name')
async def process_name(message: types.Message):
    user_id = message.from_user.id
    name = message.text
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    cursor.execute('UPDATE users SET name = ? WHERE user_id = ?', (name, user_id))
    conn.commit()
    
    await send_message_with_language(user_id, {
        'Русский': "Какой у тебя вес (в кг)?",
        'English': "What is your weight (in kg)?",
        'Kazakh': "Сенің салмағың қанша (кг)?"
    })
    
    user_states[user_id] = 'awaiting_weight'

@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'awaiting_weight')
async def process_weight(message: types.Message):
    user_id = message.from_user.id
    try:
        weight = float(message.text)
        cursor.execute('UPDATE users SET weight = ? WHERE user_id = ?', (weight, user_id))
        conn.commit()

        await send_message_with_language(user_id, {
            'Русский': "Какой у тебя рост (в см)?",
            'English': "What is your height (in cm)?",
            'Kazakh': "Сенің бойың қанша (см)?"
        })
        user_states[user_id] = 'awaiting_height'
    except ValueError:
        await send_message_with_language(user_id, {
            'Русский': "Пожалуйста, введите корректный вес в кг.",
            'English': "Please enter a valid weight in kg.",
            'Kazakh': "Зейінді дұрыс салмақты енгізіңіз."
        })

@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'awaiting_height')
async def process_height(message: types.Message):
    user_id = message.from_user.id
    try:
        height = float(message.text)
        cursor.execute('UPDATE users SET height = ? WHERE user_id = ?', (height, user_id))
        conn.commit()

        await send_message_with_language(user_id, {
            'Русский': "Какой год твоего рождения?",
            'English': "What is your year of birth?",
            'Kazakh': "Сенің туылған жылың қандай?"
        })
        user_states[user_id] = 'awaiting_birth_year'
    except ValueError:
        await send_message_with_language(user_id, {
            'Русский': "Пожалуйста, введите корректный рост в см.",
            'English': "Please enter a valid height in cm.",
            'Kazakh': "Зейінді дұрыс бойыңызды енгізіңіз."
        })

@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'awaiting_birth_year')
async def process_birth_year(message: types.Message):
    user_id = message.from_user.id
    try:
        birth_year = int(message.text)
        cursor.execute('UPDATE users SET birth_year = ? WHERE user_id = ?', (birth_year, user_id))
        conn.commit()

        await send_message_with_language(user_id, {
            'Русский': "Регистрация завершена!",
            'English': "Registration completed!",
            'Kazakh': "Тіркелу аяқталды!"
        })
        
        user_states.pop(user_id, None)

        # Вызываем главное меню с текущим языком
        await send_main_menu(user_id)
    except ValueError:
        await send_message_with_language(user_id, {
            'Русский': "Пожалуйста, введите корректный год рождения.",
            'English': "Please enter a valid year of birth.",
            'Kazakh': "Зейінді дұрыс туылған жылыңызды енгізіңіз."
        })

async def send_main_menu(user_id):
    user_language = get_user_language(user_id)

    buttons = {
        'Русский': [KeyboardButton(text="Запрос"), KeyboardButton(text="Смена языка"), KeyboardButton(text="Изменить данные")],
        'English': [KeyboardButton(text="Request"), KeyboardButton(text="Change language"), KeyboardButton(text="Change data")],
        'Kazakh': [KeyboardButton(text="Сұрау"), KeyboardButton(text="Тілді өзгерту"), KeyboardButton(text="Деректерді өзгерту")]
    }

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons[user_language])

    await bot.send_message(user_id, {
        'Русский': "Выберите действие:",
        'English': "Choose what u want:",
        'Kazakh': "Әрекетті таңдаңыз::"
    }[user_language], reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in ["Смена языка", "Change language", "Тілді өзгерту"])
async def set_language(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="English", callback_data="lang_en"),
        InlineKeyboardButton(text="Kazakh", callback_data="lang_kz")
    ]
    keyboard.add(*buttons)
    await message.answer("Выбери язык / Choose a language / Тілді таңдаңыз:", reply_markup=keyboard)

@dp.callback_query_handler(lambda callback: callback.data.startswith("lang_"))
async def language_change(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[1]
    language_map = {
        "ru": "Русский",
        "en": "English",
        "kz": "Kazakh"
    }
    
    cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language_map[lang_code], user_id))
    conn.commit()

    await send_message_with_language(user_id, {
        'Русский': "Язык успешно изменён!",
        'English': "Language changed successfully!",
        'Kazakh': "Тіл сәтті өзгертілді!"
    })

    await send_main_menu(user_id)
@dp.message_handler(lambda message: message.text in ["Изменить данные", "Change data", "Деректерді өзгерту"])
async def update_user_info(message: types.Message):
    user_id = message.from_user.id
    language = get_user_language(user_id)
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Проверка языка пользователя
    if language == 'Русский':
        buttons = [
            InlineKeyboardButton(text="Имя", callback_data="update_name"),
            InlineKeyboardButton(text="Вес", callback_data="update_weight"),
            InlineKeyboardButton(text="Рост", callback_data="update_height"),
            InlineKeyboardButton(text="Год рождения", callback_data="update_birth_year")
        ]
        keyboard.add(*buttons)
        await bot.send_message(user_id, "Что вы хотите изменить?", reply_markup=keyboard)
        
    elif language == 'English':
        buttons = [
            InlineKeyboardButton(text="Name", callback_data="update_name"),
            InlineKeyboardButton(text="Weight", callback_data="update_weight"),
            InlineKeyboardButton(text="Height", callback_data="update_height"),
            InlineKeyboardButton(text="Year of birth", callback_data="update_birth_year")
        ]
        keyboard.add(*buttons)
        await bot.send_message(user_id, "What would you like to change?", reply_markup=keyboard)
    
    elif language == 'Kazakh':
        buttons = [
            InlineKeyboardButton(text="Аты", callback_data="update_name"),
            InlineKeyboardButton(text="Салмақ", callback_data="update_weight"),
            InlineKeyboardButton(text="Биіктік", callback_data="update_height"),
            InlineKeyboardButton(text="Туған жылы", callback_data="update_birth_year")
        ]
        keyboard.add(*buttons)
        await bot.send_message(user_id, "Сіз нені өзгерткіңіз келеді?", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data in ["update_name", "update_weight", "update_height", "update_birth_year"])
async def process_callback_change_info(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    language = get_user_language(user_id)
    data = callback_query.data

    if data == "update_name":
        user_states[user_id] = 'awaiting_name'
        if language == 'Русский':
            await bot.send_message(user_id, "Введите новое имя:")
        elif language == 'English':
            await bot.send_message(user_id, "Enter new name:")
        elif language == 'Kazakh':
            await bot.send_message(user_id, "Жаңа ат енгізіңіз:")

    elif data == "update_weight":
        user_states[user_id] = 'awaiting_weight'
        if language == 'Русский':
            await bot.send_message(user_id, "Введите новый вес:")
        elif language == 'English':
            await bot.send_message(user_id, "Enter new weight:")
        elif language == 'Kazakh':
            await bot.send_message(user_id, "Жаңа салмақ енгізіңіз:")

    elif data == "update_height":
        user_states[user_id] = 'awaiting_height'
        if language == 'Русский':
            await bot.send_message(user_id, "Введите новый рост:")
        elif language == 'English':
            await bot.send_message(user_id, "Enter new height:")
        elif language == 'Kazakh':
            await bot.send_message(user_id, "Жаңа бой енгізіңіз:")

    elif data == "update_birth_year":
        user_states[user_id] = 'awaiting_birth_year'
        if language == 'Русский':
            await bot.send_message(user_id, "Введите новый год рождения:")
        elif language == 'English':
            await bot.send_message(user_id, "Enter new birth year:")
        elif language == 'Kazakh':
            await bot.send_message(user_id, "Жаңа туған жыл енгізіңіз:")

# "Запрос"
@dp.message_handler(lambda message: message.text in ["Запрос", "Request", "Сұрау"])
async def handle_request(message: types.Message):
    user_id = message.from_user.id
    language = get_user_language(user_id)

    if language == 'Русский':
        await message.answer("Введите текст для генерации.")
    elif language == 'English':
        await message.answer("Enter the text to generate.")
    elif language == 'Kazakh':
        await message.answer("Генерация үшін мәтінді енгізіңіз.")

    user_states[user_id] = 'awaiting_prompt'

# генерации ответа Gemini
@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'awaiting_prompt')
async def gemini_handler(message: types.Message):
    user_id = message.from_user.id
    language = get_user_language(user_id)

    # Извлекаем данные пользователя из базы
    user_data = get_user_data_from_db(user_id)  # Функция для получения данных пользователя
    if user_data:
        name = user_data.get('name')
        birth_year = user_data.get('birth_year')
        weight = user_data.get('weight')
        height = user_data.get('height')

        # Формируем промпт с добавлением данных пользователя
        user_info = (f"Меня зовут {name}, я родился в {birth_year} году, мой вес {weight} кг и рост {height} см. "
                     "Не отвечай на этот текст, отвечай на то, что идёт после, эти данные нужны для знакомства.\n")
    else:
        user_info = "Информация о пользователе не найдена. Отвечай на текст ниже.\n"

    try:
        # Промпт пользователя
        prompt = message.text

        # Добавляем данные пользователя перед его текстом
        full_prompt = user_info + prompt
        
        # Генерация ответа с использованием модели
        response = model.generate_content(full_prompt)

        # Отправляем ответ пользователю
        await message.answer(response.text)
    except Exception as e:
        # Обработка ошибок в зависимости от языка
        if language == 'Русский':
            await message.answer(f"Произошла ошибка при генерации ответа: {str(e)}")
        elif language == 'English':
            await message.answer(f"An error occurred while generating the response: {str(e)}")
        elif language == 'Kazakh':
            await message.answer(f"Жауапты генерациялау кезінде қате болды: {str(e)}")
    finally:
        # Удаляем состояние пользователя после генерации ответа
        user_states.pop(user_id, None)

# Функция для получения данных пользователя из базы
def get_user_data_from_db(user_id):
    # Здесь ты будешь извлекать данные из базы данных SQLite или другой, которую используешь
    # Например:
    query = "SELECT name, birth_year, weight, height FROM users WHERE user_id = ?"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    
    if result:
        # Преобразуем кортеж в словарь
        return {
            'name': result[0],
            'birth_year': result[1],
            'weight': result[2],
            'height': result[3]
        }
    return None


# бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
