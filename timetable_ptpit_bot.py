import json
import urllib

import schedule
from threading import Thread
from time import sleep

from urllib import request

import telebot
from psycopg2._json import Json
from telebot import types

import psycopg2

import datetime
import requests
from bs4 import BeautifulSoup

bot = telebot.TeleBot("5130698267:AAErP_4sPv4j7moAzqW7LZeePEWtG6CWw38")

DB_URI = "postgres://elbthyzcnbsebw:1f94045c08512cf2aa72f7cdcdf3dc123f5e2689b02761953725502618352e12@ec2-34-247-172-149.eu-west-1.compute.amazonaws.com:5432/dc0i6ie87j51p"

db_connection = psycopg2.connect(DB_URI, sslmode="require")
db_object = db_connection.cursor()

# news_status = False

time_of_lessons = {1: "8:30 - 10:05",
                   2: "10:25 - 12:00",
                   3: "12:20 - 14:10",
                   4: "14:15 - 15:50",
                   5: "16:10 - 17:55",
                   6: "18:00 - 19:35"
                   }

time_of_lessons_with_breaks = ["1 Занятие: 8:30 - 9:15",
                               "----------------------------------------------------------------",
                               "Перерыв - 5 минут",
                               "----------------------------------------------------------------",
                               "2 Занятие: 9:20 - 10:05",
                               "----------------------------------------------------------------",
                               "Перерыв на обед для 1 курса - 20 минут",
                               "----------------------------------------------------------------",
                               "3 Занятие: 10:25 - 11:10",
                               "----------------------------------------------------------------",
                               "Перерыв - 5 минут",
                               "----------------------------------------------------------------",
                               "4 Занятие: 11:15 - 12:00",
                               "----------------------------------------------------------------",
                               "Перерыв на обед для 2 курса - 20 минут",
                               "----------------------------------------------------------------",
                               "5 Занятие: 12:20 - 13:05",
                               "----------------------------------------------------------------",
                               "Перерыв на обед для 3, 4 курсов - 20 минут",
                               "----------------------------------------------------------------",
                               "6 Занятие: 13:25 - 14:10",
                               "----------------------------------------------------------------",
                               "Перерыв - 5 минут",
                               "----------------------------------------------------------------",
                               "7 Занятие: 14:15 - 15:00",
                               "----------------------------------------------------------------",
                               "Перерыв - 5 минут",
                               "----------------------------------------------------------------",
                               "8 Занятие: 15:05 - 15:50",
                               "----------------------------------------------------------------",
                               "Перерыв на обед для 2 смены - 20 минут",
                               "----------------------------------------------------------------",
                               "9 Занятие: 16:10 - 16:55",
                               "----------------------------------------------------------------",
                               "Перерыв на обед для мастерских 1 этажа - 15 минут",
                               "----------------------------------------------------------------",
                               "10 Занятие: 17:10 - 17:55",
                               "----------------------------------------------------------------",
                               "Перерыв - 5 минут",
                               "----------------------------------------------------------------",
                               "11 Занятие: 18:00 - 18:45",
                               "----------------------------------------------------------------",
                               "Перерыв - 5 минут",
                               "----------------------------------------------------------------",
                               "11 Занятие: 18:50 - 19:35"
                               ]

day_of_week = {0: "Понедельник",
               1: "Вторник",
               2: "Среда",
               3: "Четверг",
               4: "Пятница",
               5: "Суббота",
               6: "Воскресенье"
               }


def menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Выбрать группу")
    btn2 = types.KeyboardButton("Выбрать подгруппу")
    markup.add(btn1, btn2)
    btn3 = types.KeyboardButton("Показать расписание на сегодня")
    markup.add(btn3)
    btn4 = types.KeyboardButton("Показать расписание на завтра")
    markup.add(btn4)
    btn5 = types.KeyboardButton("Показать расписание на дату")
    markup.add(btn5)
    # if news_status is False:
    #     btn6 = types.KeyboardButton("Включить отображение новостей")
    # else:
    #     btn6 = types.KeyboardButton("Выключить отображение новостей")
    btn6 = types.KeyboardButton("Отобразить последние 3 новости")
    markup.add(btn6)
    btn7 = types.KeyboardButton("Расписание звонков")
    markup.add(btn7)
    btn8 = types.KeyboardButton("О боте")
    btn9 = types.KeyboardButton("Помощь")
    markup.add(btn8, btn9)
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    db_object.execute(f"SELECT id FROM users WHERE id = {user_id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, subgroup) VALUES (%s, %s, %s)", (user_id, username, -1))
        db_connection.commit()
    bot.send_message(message.chat.id,
                     text="Привет, {0.first_name}! для начала работы выберите свою группу и подгруппу".format(
                         message.from_user), reply_markup=menu_keyboard())


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id,
                     text='Для выбора группы вы можете ввести /group и название своей группы или нажав на кнопку. Для выбора подгруппы вы можете ввести /subgroup и название своей группы или нажав на кнопку.')


@bot.message_handler(commands=['group'])
def list_group(message):
    groups = []
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    with urllib.request.urlopen("https://api.ptpit.ru/groups") as url:
        data = json.loads(url.read().decode())
        for group in data:
            groups.append(group["name"])
    markup.add(*groups)
    bot.send_message(message.chat.id, text="Выберите вашу группу",
                     reply_markup=markup)
    bot.register_next_step_handler(message, get_group, data)


def get_group(message, data):
    bot.send_message(message.chat.id, text="Выбрана группа: " + message.text,
                     reply_markup=menu_keyboard())
    group = message.text
    # with urllib.request.urlopen("https://api.ptpit.ru/groups") as url:
    #     data = json.loads(url.read().decode())
    for group_data in data:
        if group_data["name"] == group:
            group_id = group_data["id"]
            user_id = message.from_user.id
            db_object.execute(f"UPDATE users SET group_id = {group_id} WHERE id = {user_id}")
            db_connection.commit()

            db_object.execute(f"SELECT group_id FROM timetable")
            result = db_object.fetchall()
            if group_id not in result:
                print(group_id)
                db_object.execute("INSERT INTO timetable (group_id) VALUES (%s)", [group_id])
                db_connection.commit()


@bot.message_handler(commands=['subgroup'])
def list_subgroup(message):
    subgroups = ["1", "2"]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*subgroups)
    btn3 = types.KeyboardButton("Не Устанавливать")
    markup.add(btn3)
    bot.send_message(message.chat.id, text="Выберите вашу подгруппу",
                     reply_markup=markup)
    bot.register_next_step_handler(message, get_subgroup)


def get_subgroup(message):
    user_id = message.from_user.id
    if message.text == "Не Устанавливать":
        subgroup = -1
        db_object.execute(f"UPDATE users SET subgroup = {subgroup} WHERE id = {user_id}")
        db_connection.commit()
        bot.send_message(message.chat.id, text="Подгруппа не установлена", reply_markup=menu_keyboard())
    else:
        subgroup = int(message.text)
        db_object.execute(f"UPDATE users SET subgroup = {subgroup} WHERE id = {user_id}")
        db_connection.commit()
        bot.send_message(message.chat.id, text="Выбрана подгруппа: " + message.text,
                         reply_markup=menu_keyboard())


@bot.message_handler(commands=['about'])
def about(message):
    bot.send_message(message.chat.id,
                     text='Этот будет отправлять вам сообщения об изменениях в расписании и свежие новости. '
                          'Бот разработал Султангулов Д. Р. '
                          'Также пользовтаель может вывести расписание на сегодня, завтра или на выбранную дату. '
                          'Помимо расписания есть возможность вывести последние 3 новости.')


@bot.message_handler(content_types=['text'])
def menu(message):
    global news_status
    if message.text == "Выбрать группу":
        list_group(message)
    elif message.text == "Выбрать подгруппу":
        list_subgroup(message)
    elif message.text == "О боте":
        about(message)
    elif message.text == "Помощь":
        help(message)
    # elif message.text == "Включить отображение новостей":
    #     news_status = True
    #     bot.send_message(message.chat.id, text="Включено отображение новостей",
    #                      reply_markup=menu_keyboard())
    # elif message.text == "Выключить отображение новостей":
    #     news_status = False
    #     bot.send_message(message.chat.id, text="Выключено отображение новостей",
    #                      reply_markup=menu_keyboard())
    elif message.text == "Отобразить последние 3 новости":
        send_news(message)
    elif message.text == "Показать расписание на сегодня":
        send_timetable_today(message)
    elif message.text == "Показать расписание на завтра":
        send_timetable_tomorrow(message)
    elif message.text == "Показать расписание на дату":
        bot.send_message(message.chat.id,
                         text='Введите дату в формате: год-месяц-день(ГГГГ-ММ-ДД)(например: 2022-04-21)',
                         reply_markup=menu_keyboard())
        bot.register_next_step_handler(message, send_timetable_date)
    elif message.text == "Расписание звонков":
        send_time_of_lessons_with_breaks(message)


# https://api.ptpit.ru/timetable/groups/121/2022-04-04
@bot.message_handler(commands=['send_timetable_today'])
def send_timetable_today(message):
    now = datetime.datetime.now().astimezone()
    current_date = now.strftime("%Y-%m-%d")
    user_id = message.from_user.id
    db_object.execute(f"SELECT group_id FROM users WHERE id = {user_id}")
    group_id = db_object.fetchone()[0]
    db_object.execute(f"SELECT subgroup FROM users WHERE id = {user_id}")
    subgroup = db_object.fetchone()[0]
    if not group_id:
        bot.send_message(message.chat.id,
                         text='Выберите группу')
    else:
        print("https://api.ptpit.ru/timetable/groups/" + str(group_id) + "/" + now.strftime("%Y-%m-%d"))
        with urllib.request.urlopen(
                "https://api.ptpit.ru/timetable/groups/" + str(group_id) + "/" + current_date) as url:
            data = json.loads(url.read().decode())
            week = day_of_week[datetime.date(now.year, now.month, now.day).weekday()]
            print(data)
            print("Расписание на " + week + " (" + current_date + ")")
            if len(data):
                if data[0]["date"] != current_date:
                    bot.send_message(message.chat.id,
                                     text="Расписание на " + week + " (" + current_date + ") отсутствует")
                else:
                    bot.send_message(message.chat.id,
                                     text="Расписание на " + week + " (" + current_date + ")")
                    for timetable in data:
                        if timetable["date"] == current_date:
                            print(timetable)
                            if timetable["subgroup"] == 0:
                                # print("Номер пары: " + str(timetable["num"]))
                                # print("Предмет: " + timetable["subject_name"])
                                # print("Подгруппа: " + str(timetable["subgroup"]))
                                # print("Время: " + time_of_lessons[timetable["num"]])
                                # print("Кабинет: " + str(timetable["room_name"]))
                                # print("ФИО: " + timetable["teacher_surname"] + " " +
                                #               timetable["teacher_name"] + " " +
                                #               timetable["teacher_secondname"])
                                bot.send_message(message.chat.id,
                                                 text=(
                                                     f'Номер пары: {str(timetable["num"])}''\n'
                                                     f'Предмет: {timetable["subject_name"]}''\n'
                                                     f'Подгруппа: Группа''\n'
                                                     f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                     f'Кабинет: {str(timetable["room_name"])}''\n'
                                                     f'ФИО: {timetable["teacher_surname"]} '
                                                     f'{timetable["teacher_name"]} '
                                                     f'{timetable["teacher_secondname"]}'
                                                 ))
                            elif timetable["subgroup"] > 0 and subgroup == -1:
                                bot.send_message(message.chat.id,
                                                 text=(
                                                     f'Номер пары: {str(timetable["num"])}''\n'
                                                     f'Предмет: {timetable["subject_name"]}''\n'
                                                     f'Подгруппа: {str(timetable["subgroup"])}''\n'
                                                     f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                     f'Кабинет: {str(timetable["room_name"])}''\n'
                                                     f'ФИО: {timetable["teacher_surname"]} '
                                                     f'{timetable["teacher_name"]} '
                                                     f'{timetable["teacher_secondname"]}'
                                                 ))
                            elif timetable["subgroup"] > 0 and subgroup > 0:
                                if timetable["subgroup"] == subgroup:
                                    bot.send_message(message.chat.id,
                                                     text=(
                                                         f'Номер пары: {str(timetable["num"])}''\n'
                                                         f'Предмет: {timetable["subject_name"]}''\n'
                                                         f'Подгруппа: {str(timetable["subgroup"])}''\n'
                                                         f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                         f'Кабинет: {str(timetable["room_name"])}''\n'
                                                         f'ФИО: {timetable["teacher_surname"]} '
                                                         f'{timetable["teacher_name"]} '
                                                         f'{timetable["teacher_secondname"]}'
                                                     ))
            else:
                bot.send_message(message.chat.id,
                                 text="Расписание на " + week + " (" + current_date + ") отсутствует")

@bot.message_handler(commands=['send_timetable_tomorrow'])
def send_timetable_tomorrow(message):
    now = datetime.datetime.now().astimezone()
    tomorrow_date = now + datetime.timedelta(days=1)
    tomorrow_date = tomorrow_date.strftime("%Y-%m-%d")

    user_id = message.from_user.id
    db_object.execute(f"SELECT group_id FROM users WHERE id = {user_id}")
    group_id = db_object.fetchone()[0]
    db_object.execute(f"SELECT subgroup FROM users WHERE id = {user_id}")
    subgroup = db_object.fetchone()[0]
    print(group_id)
    print(subgroup)
    if not group_id:
        bot.send_message(message.chat.id,
                         text='Выберите группу')
    else:
        print("https://api.ptpit.ru/timetable/groups/" + str(group_id) + "/" + tomorrow_date)
        with urllib.request.urlopen(
                "https://api.ptpit.ru/timetable/groups/" + str(group_id) + "/" + tomorrow_date) as url:
            data = json.loads(url.read().decode())
            week = day_of_week[datetime.date(now.year, now.month, now.day + 1).weekday()]
            print(data)
            print("Расписание на " + tomorrow_date)
            if len(data):
                if data[0]["date"] != tomorrow_date:
                    bot.send_message(message.chat.id,
                                     text="Расписание на " + week + " (" + tomorrow_date + ") отсутствует")
                else:
                    bot.send_message(message.chat.id,
                                     text="Расписание на " + week + " (" + tomorrow_date + ")")
                    for timetable in data:
                        if timetable["date"] == tomorrow_date:
                            if timetable["subgroup"] == 0:
                                bot.send_message(message.chat.id,
                                                 text=(
                                                     f'Номер пары: {str(timetable["num"])}''\n'
                                                     f'Предмет: {timetable["subject_name"]}''\n'
                                                     f'Подгруппа: Группа''\n'
                                                     f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                     f'Кабинет: {str(timetable["room_name"])}''\n'
                                                     f'ФИО: {timetable["teacher_surname"]} '
                                                     f'{timetable["teacher_name"]} '
                                                     f'{timetable["teacher_secondname"]}'
                                                 ))
                            elif timetable["subgroup"] > 0 and subgroup == -1:
                                bot.send_message(message.chat.id,
                                                 text=(
                                                     f'Номер пары: {str(timetable["num"])}''\n'
                                                     f'Предмет: {timetable["subject_name"]}''\n'
                                                     f'Подгруппа: {str(timetable["subgroup"])}''\n'
                                                     f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                     f'Кабинет: {str(timetable["room_name"])}''\n'
                                                     f'ФИО: {timetable["teacher_surname"]} '
                                                     f'{timetable["teacher_name"]} '
                                                     f'{timetable["teacher_secondname"]}'
                                                 ))
                            elif timetable["subgroup"] > 0 and subgroup > 0:
                                if timetable["subgroup"] == subgroup:
                                    bot.send_message(message.chat.id,
                                                     text=(
                                                         f'Номер пары: {str(timetable["num"])}''\n'
                                                         f'Предмет: {timetable["subject_name"]}''\n'
                                                         f'Подгруппа: {str(timetable["subgroup"])}''\n'
                                                         f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                         f'Кабинет: {str(timetable["room_name"])}''\n'
                                                         f'ФИО: {timetable["teacher_surname"]} '
                                                         f'{timetable["teacher_name"]} '
                                                         f'{timetable["teacher_secondname"]}'
                                                     ))
            else:
                bot.send_message(message.chat.id,
                                 text="Расписание на " + week + " (" + tomorrow_date + ") отсутствует")

@bot.message_handler(commands=['send_timetable_date'])
def send_timetable_date(message):
    date = message.text

    user_id = message.from_user.id
    db_object.execute(f"SELECT group_id FROM users WHERE id = {user_id}")
    group_id = db_object.fetchone()[0]
    db_object.execute(f"SELECT subgroup FROM users WHERE id = {user_id}")
    subgroup = db_object.fetchone()[0]
    if not group_id:
        bot.send_message(message.chat.id,
                         text='Выберите группу')
    else:
        print(date)
        print(date.split("-")[0])
        print("https://api.ptpit.ru/timetable/groups/" + str(group_id) + "/" + date)
        with urllib.request.urlopen("https://api.ptpit.ru/timetable/groups/" + str(group_id) + "/" + date) as url:
            data = json.loads(url.read().decode())
            week = day_of_week[
                datetime.date(int(date.split("-")[0]), int(date.split("-")[1]), int(date.split("-")[2])).weekday()]
            print(data)
            print("Расписание на " + week + " (" + date + ")")
            if len(data):
                if data[0]["date"] != date:
                    bot.send_message(message.chat.id,
                                     text="Расписание на " + week + " (" + date + ") отсутствует")
                else:
                    bot.send_message(message.chat.id,
                                     text="Расписание на " + week + " (" + date + ")")
                    for timetable in data:
                        if timetable["date"] == date:
                            if timetable["subgroup"] == 0:
                                print(str(timetable["num"]))
                                print(timetable["num"])
                                bot.send_message(message.chat.id,
                                                 text=(
                                                     f'Номер пары: {str(timetable["num"])}''\n'
                                                     f'Предмет: {timetable["subject_name"]}''\n'
                                                     f'Подгруппа: Группа''\n'
                                                     f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                     f'Кабинет: {str(timetable["room_name"])}''\n'
                                                     f'ФИО: {timetable["teacher_surname"]} '
                                                     f'{timetable["teacher_name"]} '
                                                     f'{timetable["teacher_secondname"]}'
                                                 ))
                            elif timetable["subgroup"] > 0 and subgroup == -1:
                                bot.send_message(message.chat.id,
                                                 text=(
                                                     f'Номер пары: {str(timetable["num"])}''\n'
                                                     f'Предмет: {timetable["subject_name"]}''\n'
                                                     f'Подгруппа: {str(timetable["subgroup"])}''\n'
                                                     f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                     f'Кабинет: {str(timetable["room_name"])}''\n'
                                                     f'ФИО: {timetable["teacher_surname"]} '
                                                     f'{timetable["teacher_name"]} '
                                                     f'{timetable["teacher_secondname"]}'
                                                 ))

                            elif timetable["subgroup"] > 0 and subgroup > 0:
                                if timetable["subgroup"] == subgroup:
                                    bot.send_message(message.chat.id,
                                                     text=(
                                                         f'Номер пары: {str(timetable["num"])}''\n'
                                                         f'Предмет: {timetable["subject_name"]}''\n'
                                                         f'Подгруппа: {str(timetable["subgroup"])}''\n'
                                                         f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                         f'Кабинет: {str(timetable["room_name"])}''\n'
                                                         f'ФИО: {timetable["teacher_surname"]} '
                                                         f'{timetable["teacher_name"]} '
                                                         f'{timetable["teacher_secondname"]}'
                                                     ))
            else:
                bot.send_message(message.chat.id,
                                 text="Расписание на " + week + " (" + date + ") отсутствует")

@bot.message_handler(content_types=['send_news'])
def send_news(message):
    url = 'https://ptpit.ru/?cat=16'
    page = requests.get(url)
    print(page.status_code)

    urlsNews = []
    allNews = []
    titlesNews = []

    soup = BeautifulSoup(page.text, "html.parser")

    NewsUrl = soup.findAll('a', class_='read-more')
    for index, data in enumerate(NewsUrl):
        if index == 3:
            break
        urlsNews.append(data.get('href'))

    print(urlsNews)

    for urlNews in urlsNews:
        url = urlNews
        print(url)
        page = requests.get(url)
        print(page.status_code)

        soup = BeautifulSoup(page.text, "html.parser")

        Titles = soup.findAll('h2', class_='post-title')
        for data in Titles:
            titlesNews.append(data.text.strip())

        News = soup.findAll('div', class_='entry')
        for data in News:
            allNews.append(data.text.strip())

    for i in range(3):
        bot.send_message(message.chat.id, text=titlesNews[i] + '\n' + '\n' + allNews[i])


@bot.message_handler(content_types=['send_time_of_lessons_with_breaks'])
def send_time_of_lessons_with_breaks(message):
    bot.send_message(message.chat.id, '\n'.join(time_of_lessons_with_breaks))


# def write_current_timetable():
#     db_object.execute(f"SELECT group_id FROM timetable")
#     group_ids = db_object.fetchall()
#     for group_id in group_ids:
#         # print(group_id)
#         now = datetime.datetime.now().astimezone()
#         current_date = now.strftime("%Y-%m-%d")
#         print("https://api.ptpit.ru/timetable/groups/" + str(group_id[0]) + "/" + now.strftime("%Y-%m-%d"))
#         with urllib.request.urlopen(
#                 "https://api.ptpit.ru/timetable/groups/" + str(group_id[0]) + "/" + current_date) as url:
#             data = json.loads(url.read().decode())
#             # print(data)
#             db_object.execute(f"UPDATE timetable SET current_timetable = {Json(data)} WHERE group_id = {group_id[0]}")
#             db_connection.commit()


def send_refreshed_timetable():
    db_object.execute(f"SELECT group_id FROM timetable")
    group_ids = db_object.fetchall()
    for group_id in group_ids:
        print(group_id)
        now = datetime.datetime.now().astimezone()
        current_date = now.strftime("%Y-%m-%d")
        print("https://api.ptpit.ru/timetable/groups/" + str(group_id[0]) + "/" + now.strftime("%Y-%m-%d"))
        with urllib.request.urlopen(
                "https://api.ptpit.ru/timetable/groups/" + str(group_id[0]) + "/" + current_date) as url:
            data = json.loads(url.read().decode())

            db_object.execute(f"SELECT current_timetable FROM timetable WHERE {group_id[0]} = group_id")
            current_timetable = db_object.fetchone()[0]
            if current_timetable:
                dates_refreshed_timetable = []

                for i in range(len([ele for ele in data if isinstance(ele, dict)])):
                    if i < len([ele for ele in current_timetable if isinstance(ele, dict)]):
                        # print(i)
                        # print(len([ele for ele in data if isinstance(ele, dict)]))
                        # print(len([ele for ele in current_timetable if isinstance(ele, dict)]))
                        date = data[i]["date"]
                        # print(data[i])
                        # print(current_timetable[i])
                        if data[i] != current_timetable[i]:
                            dates_refreshed_timetable.append(date)



                print(dates_refreshed_timetable)
                # users_id = []
                # db_object.execute(f"SELECT id FROM users")
                # ids = db_object.fetchall()
                # for id in ids:
                #     users_id.append(id[0])
                # print(users_id)
                if dates_refreshed_timetable:
                    db_object.execute(f"UPDATE timetable SET current_timetable = {Json(data)} WHERE group_id = {group_id[0]}")
                    db_connection.commit()
                for date in dates_refreshed_timetable:
                    db_object.execute(f"SELECT id FROM users WHERE group_id = {group_id[0]}")
                    chat_ids = db_object.fetchall()[0]
                    print(chat_ids)
                    for chat_id in chat_ids:
                        db_object.execute(f"SELECT subgroup FROM users WHERE id = {chat_id}")
                        subgroup = db_object.fetchone()[0]

                        week = day_of_week[
                            datetime.date(int(date.split("-")[0]), int(date.split("-")[1]),
                                          int(date.split("-")[2])).weekday()]
                        print("Обновленное расписание на " + week + " (" + date + ")")
                        bot.send_message(chat_id=chat_id,
                                         text="Обновленное расписание на " + week + " (" + date + ")")
                        for timetable in data:
                            if timetable["date"] == date:
                                # for user_id in range(len(users_id)):
                                #     chat_id = users_id[user_id]
                                #     print(chat_id)
                                if timetable["subgroup"] == 0:
                                    bot.send_message(chat_id=chat_id,
                                                     text=(
                                                         f'Номер пары: {str(timetable["num"])}''\n'
                                                         f'Предмет: {timetable["subject_name"]}''\n'
                                                         f'Подгруппа: Группа''\n'
                                                         f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                         f'Кабинет: {str(timetable["room_name"])}''\n'
                                                         f'ФИО: {timetable["teacher_surname"]} '
                                                         f'{timetable["teacher_name"]} '
                                                         f'{timetable["teacher_secondname"]}'
                                                     ))
                                elif timetable["subgroup"] > 0 and subgroup == -1:
                                    bot.send_message(chat_id=chat_id,
                                                     text=(
                                                         f'Номер пары: {str(timetable["num"])}''\n'
                                                         f'Предмет: {timetable["subject_name"]}''\n'
                                                         f'Подгруппа: {str(timetable["subgroup"])}''\n'
                                                         f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                         f'Кабинет: {str(timetable["room_name"])}''\n'
                                                         f'ФИО: {timetable["teacher_surname"]} '
                                                         f'{timetable["teacher_name"]} '
                                                         f'{timetable["teacher_secondname"]}'
                                                     ))
                                elif timetable["subgroup"] > 0 and subgroup > 0:
                                    if timetable["subgroup"] == subgroup:
                                        bot.send_message(chat_id=chat_id,
                                                         text=(
                                                             f'Номер пары: {str(timetable["num"])}''\n'
                                                             f'Предмет: {timetable["subject_name"]}''\n'
                                                             f'Подгруппа: {str(timetable["subgroup"])}''\n'
                                                             f'Время: {time_of_lessons[timetable["num"]]}''\n'
                                                             f'Кабинет: {str(timetable["room_name"])}''\n'
                                                             f'ФИО: {timetable["teacher_surname"]} '
                                                             f'{timetable["teacher_name"]} '
                                                             f'{timetable["teacher_secondname"]}'
                                                         ))
                dates_refreshed_timetable.clear()
            db_object.execute(f"UPDATE timetable SET current_timetable = {Json(data)} WHERE group_id = {group_id[0]}")
            db_connection.commit()


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    schedule.every(10).minutes.do(send_refreshed_timetable)
    Thread(target=schedule_checker).start()
    bot.polling()
