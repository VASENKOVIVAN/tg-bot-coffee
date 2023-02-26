import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher
from aiogram.types.message import ContentType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from loguru import logger
import requests


logger.add("bot/logs/debug.log", format="{time} {level} {message}", level="DEBUG", rotation="10 MB", compression="zip")

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
TELEGRAM_PAYMENTS_PROVIDER_TOKEN = os.getenv("TELEGRAM_PAYMENTS_PROVIDER_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Указываем путь к JSON
gc = gspread.service_account(filename='keys/сredentials.json')

# Открываем таблицу
sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1AwXXCO4_LIyls0nAh-DaOuD81C6rAIIdk6iSrLROkmY/edit#gid=0')

scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("keys/сredentials.json", scope)
client = gspread.authorize(credentials)
sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1AwXXCO4_LIyls0nAh-DaOuD81C6rAIIdk6iSrLROkmY').worksheet("Меню").get_values()
df =  pd.DataFrame.from_dict(sheet)

sheet_dobavki = client.open_by_url('https://docs.google.com/spreadsheets/d/1AwXXCO4_LIyls0nAh-DaOuD81C6rAIIdk6iSrLROkmY').worksheet("Добавки").get_values()
df_dobavki =  pd.DataFrame.from_dict(sheet_dobavki)

TOKEN = '6276457543:AAFGKiu224xSr9wgTB_pp-DU8hOB4n2N_IA'

TEXT_START = """
🙌🏼 С помощью этого бота вы можете сделать заказ в нашей кофейне
👍🏽 После того, как надавите на кнопку с зеленой галочкой появится меню
☕️ Можно будет добавить в корзину все, что хочется и оплатить прямо тут
🎯 Можно еще делать заказы и без оплаты, но это только для своих (тсс..)
"""

bot = Bot(TOKEN)
dp = Dispatcher(bot=bot)

photo = 'https://bobycafe.com/uploads/menu//01_%D0%9A%D0%BE%D1%84%D0%B5/%D0%BA%D0%BE%D1%84%D0%B5.png'

ikb_start = InlineKeyboardMarkup(row_width=1)
ib1_start = InlineKeyboardButton(text='✅ Ясно, дальше', callback_data='main_menu')
ikb_start.add(ib1_start)






@logger.catch
def send_to_telegram(message):

    apiToken = TELEGRAM_API_TOKEN
    chatID = TELEGRAM_CHAT_ID
    apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'

    try:
        response = requests.get(apiURL, json={'chat_id': chatID, 'text': message})
        print(response.text)
    except Exception as e:
        print(e)



@logger.catch
def create_order(callback):
    print("\n\nЭто столбец 'Категория' [еда, напитки, ...]")
    print('Колбэк:', callback.data)

    global df
    df =  pd.DataFrame.from_dict(sheet)

    # Беру все ID, которые TRUE
    data_level_category_id = list(df.loc[(df[1] == 'TRUE')][0])
    print('Все ID\n:')
    print(data_level_category_id)

    # Беру названия
    data_level_category_name = list(df.loc[(df[1] == 'TRUE')][2])
    print('Все названия:')
    print(data_level_category_name)

    # Делаю ZIP
    # [('☕️ Напитки', '1'), ('☕️ Напитки', '2'), ('🥐 Еда', '37')]
    data_level_category_zip = list(zip(data_level_category_name, data_level_category_id))
    print('ZIP:')
    print(data_level_category_zip)

    # Делаю словарь из ZIP
    data_level_category_dict = dict(data_level_category_zip)
    print('Словарь из ZIP:')
    print(data_level_category_dict)

    # Сюда сохраню все кнопки
    drinkables_list_category = []

    # Добавляю кнопки
    for n in data_level_category_dict:
        drinkables_list_category.append([InlineKeyboardButton(text=f'{n}', callback_data=f'L0#{data_level_category_dict[n]}')])

    # Добавляю кнопку назад
    drinkables_list_category.append([
        InlineKeyboardButton(text='👈🏼 Назад', callback_data='main_menu_back'),
        InlineKeyboardButton(text='🛒 Корзина', callback_data='basket')
    ])

    # Создаю клавиатуру
    ikb_drinkables_category = InlineKeyboardMarkup(inline_keyboard=drinkables_list_category)

    return bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_drinkables_category)


@logger.catch
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name


    

    await bot.send_message(chat_id=user_id,
                           text=f'🤘🏼 Привет, {user_full_name}!\n{TEXT_START}',
                           reply_markup=ikb_start)


@logger.catch
@dp.message_handler(commands=['menu'])
async def menu(message: types.Message):

    ikb = InlineKeyboardMarkup(row_width=1)
    ib1 = InlineKeyboardButton(text='Сделать заказ',
                               callback_data='order')
    ib2 = InlineKeyboardButton(text='Посмотреть заказы',
                               callback_data='order_check')
    
    ikb.add(ib1, ib2)
    user_id = message.from_user.id

    await bot.send_photo(chat_id=user_id,
                         photo=photo,
                         reply_markup=ikb)

    # await bot.send_message(chat_id=user_id,
    #                        text='Heloo World!',
    #                        reply_markup=ikb)


# pre checkout  (must be answered in 10 seconds)
@logger.catch
@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


# successful payment
@logger.catch
@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    print("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment.to_python()
    for k, v in payment_info.items():
        print(f"{k} = {v}")

    await bot.send_message(message.chat.id,
                           f"Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!")


@logger.catch
@dp.callback_query_handler()
async def vote_callback(callback: types.CallbackQuery):

    # Главное меню (Сделать заказ, Контакты)
    if callback.data[:9] == 'main_menu':

        ikb_main_menu = InlineKeyboardMarkup(row_width=1)
        ib1_main_menu = InlineKeyboardButton(text='📜 Сделать заказ', callback_data='create_order')
        ib2_main_menu = InlineKeyboardButton(text='📌 Контакты', callback_data='contacts')
        ikb_main_menu.add(ib1_main_menu, ib2_main_menu)

        if callback.data == 'main_menu_back':
            await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_main_menu)
        else:
            await callback.bot.send_photo(chat_id=callback.message.chat.id,
                                    photo=photo,
                                    reply_markup=ikb_main_menu)
            

    # Главное меню -> Сделать заказ (столбец 'Категория') [еда, напитки, ...]
    elif callback.data == 'create_order':
        await create_order(callback)


    # Главное меню -> Сделать заказ -> Напитки (столбец 'Название') [капучино, латте, ...]
    elif callback.data[:3] == 'L0#':

        print("\n\nЭто столбец 'Название' [капучино, латте, ...]")
        print('Колбэк:', callback.data)

        print('Принятый ID из прошлого меню:', callback.data[3:len(callback.data)])

        # Получаю по переданному ID название
        level_0_get_name = list(df.loc[(df[0] == callback.data[3:len(callback.data)])][2])
        print('Название полученное из принятого ID:')
        print(level_0_get_name[0])

        # Беру все ID, которые TRUE
        data_level_0_id = list(df.loc[(df[1] == 'TRUE')&(df[2] == level_0_get_name[0])][0])
        print('Беру все ID, которые TRUE:')
        print(data_level_0_id)

        # Беру названия
        data_level_0_name = list(df.loc[(df[1] == 'TRUE')&(df[2] == level_0_get_name[0])][3])
        print('Беру названия:')
        print(data_level_0_name)

        # Беру следующие названия, чтобы если там пусто перекидывать сразу через столбец
        data_level_0_name_next = list(df.loc[(df[1] == 'TRUE')&(df[2] == level_0_get_name[0])][4])
        print('Беру следующие названия:')
        print(data_level_0_name_next)

        # Делаю ZIP по ID и следующему столбцу
        # [('1', ''), ('2', ''), ('3', ''), ('4', ''), ('5', 'Латте класический'), ('6', 'Латте класический')]
        data_level_0_zip0 = list(zip(data_level_0_id, data_level_0_name_next))
        print('Делаю ZIP по ID и следующему столбцу:')
        print(data_level_0_zip0)

        # Делаю ZIP по текущему столбцу и по уже созданному ZIP (по ID и следующему столбцу)
        # [('Капучино', ('1', '')), ('Капучино', ('2', '')), ('Флэт уайт', ('4', '')), ('Латте', ('5', 'Латте класический'))]
        data_level_0_zip = list(zip(data_level_0_name, data_level_0_zip0))
        print('Делаю ZIP по текущему столбцу и по уже созданному ZIP (по ID и следующему столбцу):')
        print(data_level_0_zip)

        # Делаю словарь из ZIP
        # {'Капучино': ('3', ''), 'Флэт уайт': ('4', ''), 'Латте': ('16', 'Латте кленовый манго')}
        data_level_0_dict = dict(data_level_0_zip)
        print('Словарь из ZIP:')
        print(data_level_0_dict)

        # Сюда сохраню все кнопки
        drinkables_list = []

        # Добавляю кнопки
        for n in data_level_0_dict:
            # Если следующий столбец не пустой, то на 1 лвл, иначе на 2 сразу
            if data_level_0_dict[n][1]:
                drinkables_list.append([InlineKeyboardButton(text=f'{n}', callback_data=f'L1#{data_level_0_dict[n][0]}')])
            else:
                drinkables_list.append([InlineKeyboardButton(text=f'{n}', callback_data=f'L2#{data_level_0_dict[n][0]}')])


        # Добавляю кнопку назад
        drinkables_list.append([InlineKeyboardButton(text='👈🏼 Назад', callback_data='create_order')])

        # Создаю клавиатуру
        ikb_drinkables = InlineKeyboardMarkup(inline_keyboard=drinkables_list)

        await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_drinkables)


    # Главное меню -> Сделать заказ -> Напитки -> Латте (столбец 'Тип') [Латте класический, Латте лемонграсс, Латте кленовый манго, ...]
    elif callback.data[:3] == 'L1#':

        print("\n\nЭто столбец 'Тип' [Латте класический, Латте лемонграсс, Латте кленовый манго, ...]")
        print('Колбэк:', callback.data)

        print('Принятый ID из прошлого меню:', callback.data[3:len(callback.data)])

        # Получаю по переданному ID название
        level_1_get_name = list(df.loc[(df[0] == callback.data[3:len(callback.data)])][3])
        print('Название полученное из принятого ID:')
        print(level_1_get_name[0])

        # Беру все ID, которые TRUE
        data_level_1_id = list(df.loc[(df[1] == 'TRUE')&(df[3] == level_1_get_name[0])][0])
        print('Беру все ID, которые TRUE:')
        print(data_level_1_id)

        # Беру названия
        data_level_1_name = list(df.loc[(df[1] == 'TRUE')&(df[3] == level_1_get_name[0])][4])
        print('Беру названия:')
        print(data_level_1_name)

        # Делаю zip [('Капучино', '1'), ('Капучино', '2'), ('Капучино', '3'), ('Флэт уайт', '4')]
        data_level_1_zip = list(zip(data_level_1_name, data_level_1_id))
        print('L1 - Zip:\n', data_level_1_zip)

        # Делаю словарь из zip
        data_level_1_dict = dict(data_level_1_zip)
        print('L1 - Dict:\n', data_level_1_dict)


        # Сюда сохраню все кнопки
        drinkables_list_1 = []

        # Добавляю кнопки
        for n in data_level_1_dict:
            drinkables_list_1.append([InlineKeyboardButton(text=f'{n}', callback_data=f'L2#{callback.data[3:]}#{data_level_1_dict[n]}')])
        # print(drinkables_list_1)
        # Добавляю кнопку назад
        drinkables_list_1.append([InlineKeyboardButton(text='👈🏼 Назад', callback_data='create_order')])

        ikb_drinkables_1 = InlineKeyboardMarkup(inline_keyboard=drinkables_list_1)

        await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_drinkables_1)


    # Главное меню -> Сделать заказ -> Напитки -> Латте -> Кленовый латте (столбец 'Объем') [0.2 мл., 0.3 мл., 0.4 мл., ...]
    elif callback.data[:2] == 'L2':

        print("\n\nЭто столбец 'Объем' [0.2 мл., 0.3 мл., 0.4 мл., ...]")
        print('Колбэк:', callback.data)

        print('Принятый ID из прошлого меню:', callback.data[3:len(callback.data)])

        # Разбиваю колбэк ['L2', '16', '10']
        level_2_name = callback.data.split('#')
        print('Разбиваю колбэк:')
        print(level_2_name)

        if callback.data.count('#') == 2:
            column_jump = 4
        else:
            column_jump = 3

        # Получаю по переданному ID название
        level_2_get_name = list(df.loc[(df[0] == level_2_name[-1])][column_jump])
        print('Получаю по переданному ID название:')
        print(level_2_get_name[0])

        # Беру все ID, которые TRUE
        data_level_2_id = list(df.loc[(df[1] == 'TRUE')&(df[column_jump] == level_2_get_name[0])][0])
        print('Беру все ID, которые TRUE:')
        print(data_level_2_id)

        # Беру названия
        data_level_2_name = list(df.loc[(df[1] == 'TRUE')&(df[column_jump] == level_2_get_name[0])][5])
        print('Беру названия')
        print(data_level_2_name)

        if data_level_2_name == ['']:
            data_level_2_name = list(df.loc[(df[1] == 'TRUE')&(df[column_jump] == level_2_get_name[0])][4])
            print('Беру названия из предыдущего столбца:')
            print(data_level_2_name)

        # Беру цены
        data_level_2_price = list(df.loc[(df[1] == 'TRUE')&(df[column_jump] == level_2_get_name[0])][6])
        print('Беру цены')
        print(data_level_2_price)

        # Делаю ZIP по цене и ID
        # [('320', '23'), ('330', '24')]
        data_level_2_zip_0 = list(zip(data_level_2_price, data_level_2_id))
        print('Делаю ZIP по цене и ID')
        print(data_level_2_zip_0)

        # Делаю ZIP по текущему столбцу и по уже созданному ZIP (по цене и ID)
        # [('0.3 мл.', ('320', '23')), ('0.4 мл.', ('330', '24'))]
        data_level_2_zip_1 = list(zip(data_level_2_name, data_level_2_zip_0))
        print('Делаю ZIP по текущему столбцу и по уже созданному ZIP (по цене и ID)')
        print(data_level_2_zip_1)

        # Делаю словарь из ZIP
        # {'0.3 мл.': ('320', '23'), '0.4 мл.': ('330', '24')}
        data_level_2_dict = dict(data_level_2_zip_1)
        print('Словарь из ZIP:')
        print(data_level_2_dict)

        # Сюда сохраню все кнопки
        tesstt_level_2 = []






        level_2_get_name_next = list(df.loc[(df[0] == level_2_name[-1])][7])
        print('Проверяю следующий столбец:')
        print(level_2_get_name_next)


        if level_2_get_name_next == ['']:
            # Добавляю кнопки
            for n in data_level_2_dict:
                tesstt_level_2.append([InlineKeyboardButton(text=f'{n} ({data_level_2_dict[n][0]}₽)', callback_data=f'ATK#{callback.data[3:]}#{data_level_2_dict[n][1]}')])
        else:
            # Добавляю кнопки
            for n in data_level_2_dict:
                tesstt_level_2.append([InlineKeyboardButton(text=f'{n} ({data_level_2_dict[n][0]}₽)', callback_data=f'L3#{callback.data[3:]}#{data_level_2_dict[n][1]}')])


        print('len(level_2_name)', len(level_2_name))
        if len(level_2_name) == 2:
            back_to_L1 = '#'.join(level_2_name)[3:]
            # Добавляю кнопку назад
            tesstt_level_2.append([InlineKeyboardButton(text='👈🏼 Назад', callback_data=f'L0#{back_to_L1}')])
        else:
            back_to_L1 = '#'.join(level_2_name[:-1])[3:]
            # Добавляю кнопку назад
            tesstt_level_2.append([InlineKeyboardButton(text='👈🏼 Назад', callback_data=f'L1#{back_to_L1}')])





        # Добавляю кнопку назад
        # tesstt_level_2.append([InlineKeyboardButton(text='👈🏼 Назад', callback_data='drinkables')])

        ikb_drinkables_level_2 = InlineKeyboardMarkup(inline_keyboard=tesstt_level_2)

        await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_drinkables_level_2)


    # Сюда прихожу из 'level_2'
    elif callback.data[:2] == 'L3':

        level_3_name = callback.data.split('#')
        
        print('\nЭТО 3 ЛВЛ')
        
        print('Колбэк:',callback.data)
        print('ID:', level_3_name[-1])

        # Получаю по переданному ID название
        level_3_get_name = list(df.loc[(df[0] == level_3_name[-1])][7])
        level_3_get_price = list(df.loc[(df[0] == level_3_name[-1])][8])

        # Получаю все значения
        data_level_3_dict = level_3_get_name[0].split(', ')

        print("тут - ", data_level_3_dict)
        level_3_get_name_1 = []
        level_3_get_name_2 = []

        for n in data_level_3_dict:
            print('n = ', n)
            # Получаю название
            level_3_get_name_1 += list(df_dobavki.loc[(df_dobavki[1] == "TRUE")&(df_dobavki[2] == n)][2])
            # Получаю ID
            level_3_get_name_2 += list(df_dobavki.loc[(df_dobavki[1] == "TRUE")&(df_dobavki[2] == n)][0])


        print(level_3_get_name_1)
        print(level_3_get_name_2)

        but_dict = dict(zip(level_3_get_name_1,level_3_get_name_2))
        
        
        # Получаю по переданному ID название
        level_3_get_name = list(df.loc[(df[0] == level_3_name[-1])][6])

        # Сюда сохраню все кнопки
        tesstt_level_3 = []

        tesstt_level_3.append([InlineKeyboardButton(text='Добавить в корзину', callback_data=f'ATK#{callback.data[3:]}')])

        # Добавляю кнопки
        for n in but_dict:
            tesstt_level_3.append([InlineKeyboardButton(text=f'{n}', callback_data=f'L4#{callback.data[3:]}D{but_dict[n]}')])

        back_to_L2 = '#'.join(level_3_name[:-1])[3:]

        # Добавляю кнопку назад
        tesstt_level_3.append([InlineKeyboardButton(text='👈🏼 Назад', callback_data=f'L2#{back_to_L2}')])

        ikb_drinkables_level_3 = InlineKeyboardMarkup(inline_keyboard=tesstt_level_3)

        await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_drinkables_level_3)


    # Сюда прихожу из 'level_3' 
    elif callback.data[:2] == 'L4':
        level_4_name = callback.data.split('D')
        print('\nЭТО 4 ЛВЛ')
        print('Колбэк:',callback.data)
        
        # Получаю по переданному ID название
        level_4_get_name = list(df_dobavki.loc[(df_dobavki[0] == level_4_name[-1])][2])[-1]
        print('L4 - name:\n',level_4_get_name)
        # Беру ID
        data_level_4_id = list(df_dobavki.loc[(df_dobavki[1] == 'TRUE')&(df_dobavki[2] == level_4_get_name)][0])
        print('L4 - ID:\n', data_level_4_id)
        # Беру названия
        data_level_4_name = list(df_dobavki.loc[(df_dobavki[1] == 'TRUE')&(df_dobavki[2] == level_4_get_name)][3])
        print('L4 - Список:\n', data_level_4_name)
        # Беру цены
        data_level_4_price = list(df_dobavki.loc[(df_dobavki[1] == 'TRUE')&(df_dobavki[2] == level_4_get_name)][4])
        print('L2 - Список цен:\n', data_level_4_price)
        # Делаю zip [('Капучино', '1'), ('Капучино', '2'), ('Капучино', '3'), ('Флэт уайт', '4')]
        data_level_4_zip_0 = list(zip(data_level_4_price, data_level_4_id))
        # Делаю zip [('Капучино', '1'), ('Капучино', '2'), ('Капучино', '3'), ('Флэт уайт', '4')]
        data_level_4_zip_1 = list(zip(data_level_4_name, data_level_4_zip_0))
        print('L2 - Zip:\n', data_level_4_zip_1)
        # Делаю словарь из zip
        data_level_4_dict = dict(data_level_4_zip_1)
        print('L2 - Dict:\n', data_level_4_dict)

        # Сюда сохраню все кнопки
        tesstt_level_4 = []

        # Добавляю кнопки
        for n in data_level_4_dict:
            tesstt_level_4.append([InlineKeyboardButton(text=f'{n} ({data_level_4_dict[n][0]}₽)', callback_data=f'ATK#{callback.data[3:]}#{data_level_4_dict[n][1]}')])
        
        back_to_L1 = '#'.join(level_4_name[:-1])[3:]

        # Добавляю кнопку назад
        tesstt_level_4.append([InlineKeyboardButton(text='👈🏼 Назад', callback_data=f'L1#{back_to_L1}')])

        ikb_drinkables_level_4 = InlineKeyboardMarkup(inline_keyboard=tesstt_level_4)

        await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_drinkables_level_4)


    # Добавить в корзину
    elif callback.data[:3] == 'ATK':

        user_id = callback.from_user.id

        print("\nВ корзине колбэк: ", callback.data)
        

        if 'D' in callback.data:
                     
            id_product = callback.data.split('D')[0].split('#')[-1]
            print('\nID товара:', id_product)
            name_product = list(df.loc[(df[0] == id_product)][9])[0]
            print('Название товара:', name_product)
            price_product = int(list(df.loc[(df[0] == id_product)][6])[0])
            print('Цена товара:', price_product)


            print('\nДоп есть')

            id_product_dop = callback.data.split('D')[-1].split('#')[-1]
            print('ID допа:', id_product_dop)
            # data_ATK_dop_id = df_dobavki.loc[(df_dobavki[0] == id_dop)]
            # print('Строка допа: ', data_ATK_dop_id)
            name_product_dop = list(df_dobavki.loc[(df_dobavki[0] == id_product_dop)][3])[0]
            print('Название допа:', name_product_dop)
            price_product_dop = int(list(df_dobavki.loc[(df_dobavki[0] == id_product_dop)][4])[0])
            print('Цена допа:', price_product_dop)

        else:    
            id_product = callback.data.split('#')[-1]
            print('\nID товара:', id_product)
            name_product = list(df.loc[(df[0] == id_product)][9])[0]
            print('Название товара:', name_product)
            price_product = int(list(df.loc[(df[0] == id_product)][6])[0])
            print('Цена товара:', price_product)

        with sqlite3.connect('db/database.db') as db:
            cursor = db.cursor()

            if 'D' in callback.data:
                query = f"INSERT INTO basket (user_id, title, price) VALUES ({user_id}, '{name_product}', '{price_product*100}'), ({user_id}, '{name_product_dop}', '{price_product_dop*100}');"
            else:
                query = f"INSERT INTO basket (user_id, title, price) VALUES ({user_id}, '{name_product}', '{price_product*100}');"

            cursor.execute(query)
            print("\nЗапись успешно вставлена ​​в таблицу basket ", cursor.rowcount)
            cursor.close()

        await callback.answer(text="Добавлено в корзину")

        # drinkables_list_category123 =[]
        # # Добавляю кнопку назад
        # drinkables_list_category123.append([
        #     InlineKeyboardButton(text='В меню', callback_data='create_order')
        # ])
        await create_order(callback)

        # ikb_drinkables_category123 = InlineKeyboardMarkup(inline_keyboard=drinkables_list_category123)

        # await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_drinkables_category123)


        # await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_start)


    # Корзина
    elif callback.data == 'basket':

        user_id = callback.from_user.id

        buttonstest = []

        with sqlite3.connect('db/database.db') as db:
            cursor = db.cursor()

            query = f"SELECT * FROM basket WHERE user_id={user_id}"
            data = cursor.execute(query)

            for tovar in data:
                print(tovar)
                buttonstest.append([InlineKeyboardButton(text=f'{tovar[2]} ({int(tovar[3])/100}₽)', callback_data='dfsgs')])

            cursor.close()

        if buttonstest:
            buttonstest.append([
                InlineKeyboardButton(text='👈🏼 Назад', callback_data='create_order'),
                InlineKeyboardButton(text='Очистить', callback_data='deletekorzina'),
                InlineKeyboardButton(text='Оплатить', callback_data='oplatazakaza')
            ])
        else:
            buttonstest.append([InlineKeyboardButton(text='КОРЗИНА ПУСТАЯ', callback_data='nothing')])
            buttonstest.append([InlineKeyboardButton(text='👈🏼 Назад', callback_data='create_order')])
            
        ikb_basket = InlineKeyboardMarkup(inline_keyboard=buttonstest)

        await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_basket)


    # Очистить корзину
    elif callback.data == 'deletekorzina':

        user_id = callback.from_user.id

        with sqlite3.connect('db/database.db') as db:
            cursor = db.cursor()
            query = f"DELETE FROM basket WHERE user_id={user_id}"
            data = cursor.execute(query)

            for tovar in data:
                print('Удалено:\n', tovar)

            cursor.close()    
        
        await callback.answer(
                text="Корзина очищена"
            )

        buttonstest = []

        buttonstest.append([InlineKeyboardButton(text='КОРЗИНА ПУСТАЯ', callback_data='nothing')])
        buttonstest.append([InlineKeyboardButton(text='👈🏼 Назад', callback_data='create_order')])
        ikb_basket = InlineKeyboardMarkup(inline_keyboard=buttonstest)

        await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ikb_basket)
    

    # Оплата заказа
    elif callback.data == 'oplatazakaza':

        user_id = callback.from_user.id

        if TELEGRAM_PAYMENTS_PROVIDER_TOKEN.split(':')[1] == 'TEST':
            await bot.send_message(callback.message.chat.id, "Тестовый платеж!!!")

        corzinka_oplata = []
        description_invoice = []

        with sqlite3.connect('db/database.db') as db:
            cursor = db.cursor()

            query = f"SELECT * FROM basket WHERE user_id={user_id}"
            data = cursor.execute(query)

            for tovar in data:
                print('тут' , tovar)
                price = int(tovar[3])
                corzinka_oplata.append(types.LabeledPrice(label=f'{tovar[2]}', amount=price))

            cursor.close()


        send_to_tg = ''
        send_to_tg_price = 0


        for i, tovar in enumerate(corzinka_oplata):
            print(f'{i+1}. {tovar["label"]} ({tovar["amount"]/100} р.)\n', )
            send_to_tg += f'{i+1}. {tovar["label"]} ({tovar["amount"]/100} р.)\n'
            send_to_tg_price += tovar["amount"]/100
        
        send_to_telegram(f"📝 НОВЫЙ ЗАКАЗ\n🧸 Клиент id: {user_id}\n\n{send_to_tg}\n💵 Сумма заказа: {send_to_tg_price} р.")

        await bot.send_invoice(callback.message.chat.id,
                                title="Оплата заказа",
                                description="Оплата товаров в корзине",
                                provider_token=TELEGRAM_PAYMENTS_PROVIDER_TOKEN,
                                currency="rub",
                                # photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
                                # photo_width=416,
                                # photo_height=234,
                                # photo_size=416,
                                is_flexible=False,
                                prices=corzinka_oplata,
                                start_parameter="one-month-subscription",
                                payload="test-invoice-payload")
        
        await callback.answer('')


    else:
        await callback.answer(
                text="Это пока не работает"
            )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
    # executor.start_polling(dp)