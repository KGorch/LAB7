import logging
import os
import psycopg2 as pg
import re
import requests
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    BotCommand, BotCommandScopeDefault, BotCommandScopeChat

button_manage = KeyboardButton('/manage_currency')
button_convert = KeyboardButton('/convert')
button_start = KeyboardButton('/start')

buttons = ReplyKeyboardMarkup().add(button_manage,button_convert, button_start)

bot_token = os.getenv('TELEGRAMM_BOT_TOKEN')
bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())

conn = pg.connect(user='postgres', password='123', host='localhost', port='5432', database='LAB7')
cursor = conn.cursor()


param = {}

class Form(StatesGroup):
    Manage_Start = State()
    Manage_Continue = State()
    Manage_Rate = State()
    Manage_add = State()

    Start_convertion = State()
    Next_convertion = State()
    Continue_convertion = State()

param = {}

user_commands = [
    BotCommand(command='/start', description='start'),
    BotCommand(command='/convert', description='Конвертировать')
]

admin_commands = [
    BotCommand(command='/start', description='start'),
    BotCommand(command='/manage_currency', description='Менеджер валют'),
    BotCommand(command='/convert', description='Конвертировать')
    ]

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    await message.answer("Привет, я бот чтобы я сдал 7 лабу XDDDDD")

def check_id():
    df = cursor.execute("""Select chat_id from admins""")
    Admin_id = cursor.fetchall()
    Admin_id = re.sub(r"[^0-9]", r"", str(Admin_id))
    admins_list = []
    if Admin_id in admins_list:
        return (admins_list)
    else:
        admins_list.append(Admin_id)
        return (admins_list)

#1)    если пользователь не является администратором, то в чат выводится: "Нет доступа к команде";
#3)    пользователь вводит название конвертируемой валюты;
@dp.message_handler(commands=["manage_currency"])
async def adding_currency(message: types.Message):
    admin = str(message.chat.id)
    admin_id = check_id()
    if admin in admin_id:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeDefault(chat_id = admin))
        await message.answer("Введите название конвертируемой (основной) валюты", reply_markup=buttons)
        await Form.Manage_Start.set()
    else:
        await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
        await message.answer("Нет доступа к команде")

#4)    бот выводит сообщение: "Введите название валюты, в которую можно конвертировать указанную ранее валюту";
#5)    пользователь вводит название валюты;
@dp.message_handler(state=Form.Manage_Start)
async def process_save_name(message: types.Message, state: FSMContext):
    await state.update_data(baseCurrency=message.text)
    await Form.Manage_Continue.set()
    await message.reply("Введите название валюты, в которую можно конвертировать указанную ранее валюту")

#6)    бот выводит сообщение: «Введите курс»;
#7)    пользователь вводит курс;
@dp.message_handler(state=Form.Manage_Continue)
async def process_save_name(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    await Form.Manage_Rate.set()
    await message.reply("Введите курс")

#8)    бот выводит в чат сообщение: "Добавить еще валюту, в которую может сконвертирована основная валюта. Введите (Да/Нет)";
@dp.message_handler(state=Form.Manage_Rate)
async def save_converted(message: types.Message, state: FSMContext):
    # Получаем данные текущего состояния из объекта "state"
    cod = await state.get_data()
    # Получаем код основной валюты из данных
    code_ = cod['code']
    try:
        # Если данных по сконвертированным валютам нет, создаем пустой список
        rates_ = cod['rates']
    except Exception:
        rates_ = []
    # Добавляем курс сконвертированной валюты в список сконвертированных валют
    rates_.append({'code': code_, 'rate': float(message.text)})
    # Обновляем данные объекта "state" с новым списком сконвертированных валют
    await state.update_data(rates=rates_)
    await Form.Manage_add.set()
    await message.reply("Добавить еще валюту, в которую может сконвертирована основная валюта. Введите (Да/Нет)")

@dp.message_handler(state=Form.Manage_add)
async def save_converted(message: types.Message, state: FSMContext):
    cur = await state.get_data()
    check = message.text
    answer = 'да'
    if answer in check :
        await message.reply("Введите название валюты в которую будем конвертировать")
        await Form.Manage_Continue.set()
    else:
        #10)   Бот формирует запрос в микросервис currency-manager в эндпоинт /load
        # из основной валюты и всех добавленных валют, в которые может быть сконвертирована основная
        param["baseCurrency"] = str(cur["baseCurrency"])
        param["rates"] = cur["rates"]
        print(param)
        requests.post("http://localhost:10611/load", json=param)
        await message.reply("Вы завершили настройку валюты")
        param.clear()
        await state.finish()

@dp.message_handler(commands=['convert'])
async def convert_comand(message: types.Message):
    await Form.Start_convertion.set()
    await message.reply("Введите название валюты")

@dp.message_handler(state=Form.Start_convertion)
async def save_converted(message: types.Message, state: FSMContext):
    await state.update_data(baseCurrency=message.text)
    await Form.Next_convertion.set()
    await message.reply("Введите название валюты, в которую будет производится конвертация")

@dp.message_handler(state=Form.Next_convertion)
async def save_converted(message: types.Message, state: FSMContext):
    await state.update_data(convertedCurrency=message.text)
    await Form.Continue_convertion.set()
    await message.reply("Введите сумму")

@dp.message_handler(state=Form.Continue_convertion)
async def process_convert2(message: types.Message, state: FSMContext):
    sum = message.text
    cur = await state.get_data()
    param["baseCurrency"] = str(cur["baseCurrency"])
    param["convertedCurrency"] = str(cur["convertedCurrency"])
    param["sum"] = float(sum)
    print(param)
    result = requests.get("http://localhost:10610/convert", params=param)
    print(result)

    if result == "<Response [500]>":
        await message.answer('Произошла ошибка при конвертации валюты')
        param.clear()
        await state.finish()
    else:
        print(result)
        res = result.text
        res = float(re.sub(r"[^0-9.]", r"", res))
        await message.answer(f'Результат конвертации ({res})')
        param.clear()
        await state.finish()


# точка входа в приложение
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)