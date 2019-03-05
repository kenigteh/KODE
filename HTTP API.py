import traceback
import DataBase

import threading
from time import sleep

import requests
import flask
from flask import request

from flask_mail import Mail, Message

app = flask.Flask(__name__)

# Данные для почты администратора
my_email = ""
password = ""


# Проверить, строка == дробное число
def check_float(number):
    try:
        float(number)
        return True
    except:
        return False


# Метод подписки на изменения
@app.route('/subscription', methods=["POST"])
def add_ticker():
    if "email" in request.form and "ticker" in request.form and (
            "max_price" in request.form or "min_price" in request.form):
        email = request.form["email"]
        ticker = request.form["ticker"]
        max_price = float(request.form["max_price"]) if "max_price" in request.form and check_float(
            request.form["max_price"]) else 10 ** 12
        min_price = float(request.form["min_price"]) if "min_price" in request.form and check_float(
            request.form["min_price"]) else 0
        if max_price or min_price:
            if email not in DataBase.users:
                DataBase.users[email] = {}
            if len(DataBase.users[email]) < 5:
                DataBase.users[email][ticker] = {"max_price": max_price,
                                                 "min_price": min_price}
                if ticker not in DataBase.help_table:
                    DataBase.help_table[ticker] = []
                if email not in DataBase.help_table[ticker]:
                    DataBase.help_table[ticker].append(email)
                print(DataBase.users[email])
                return "Succes"
            else:
                return "Error! You haw max subscribes now!"
    else:
        return "Several arguments lost"


# Функция удаления ожидания изменений
@app.route('/subscription', methods=["DELETE"])
def del_ticker():
    if "email" in request.form:
        email = request.form["email"]
        if email in DataBase.users:
            # Если есть тикер, то удаляем его
            if "ticker" in request.form:
                if request.form["ticker"] in DataBase.users[email]:
                    DataBase.users[email].pop(request.form["ticker"])
                    DataBase.help_table[request.form["ticker"]].pop(email)
                else:
                    return "У вас не было такого тикета"
            # Иначе удаляем всё
            else:
                for key in DataBase.users[email]:
                    DataBase.help_table[key].pop(email)
                DataBase.users[email] = {}
            return "Удаление прошло успешно"
        else:
            return "Пользователь не найден"
    else:
        return "Вы забыли указать email"


# Получить course
def get_cource(symbol):
    try:
        data = requests.get(
            f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=S7KY9FML01GT9X2W").json()
        return data
    except:
        return {"Global Quote": 0}


"""
status
0 - Больше нужного значения
1 - Меньше нужного значения
"""


# Функция для отправки сообщений
def send_email(email, symbol, status):
    word = ["Больше нужного значения", "Меньше нужного значения"]
    text = f"{symbol} {word[status]}"

    try:
        mail = Mail(app)
        with app.app_context():
            msg = Message(subject="Изменение котировок",
                          sender=app.config.get("MAIL_USERNAME"),
                          recipients=[email],  # replace with your email for testing
                          body=text)
            mail.send(msg)

    except:
        print('Something went wrong...')
        traceback.print_exc()

# Функция, отвечающая за проверку котировок
def send_tickers():
    while True:
        # Проходимся по всем акциям
        for symbol in list(DataBase.help_table.keys())[::-1]:
            # Получаем пользователей, которые отслеживают курс
            users = DataBase.help_table[symbol]
            # Получаем курс, пришедший от api
            cource = get_cource(symbol)
            if "Global Quote" in cource and cource["Global Quote"] and "02. open" in cource["Global Quote"]:
                # Вытаскиваем курс из словаря
                price = float(cource["Global Quote"]["02. open"])
                # Создаём список пользователей, которым больше не наддо отправлять изменение по акции
                user_for_del = []
                for user_email in users:
                    # Доп. проверка
                    if symbol in DataBase.users[user_email]:
                        if price > DataBase.users[user_email][symbol]["max_price"]:
                            send_email(user_email, symbol, 0)
                            user_for_del.append(user_email)
                        elif price < DataBase.users[user_email][symbol]["min_price"]:
                            send_email(user_email, symbol, 1)
                            user_for_del.append(user_email)
                # Удаляем пользователей, которым отправили изменения
                DataBase.help_table[symbol] = list(set(users) - set(user_for_del))
                if not DataBase.help_table[symbol]:
                    DataBase.help_table.pop(symbol)

        sleep(10)


if __name__ == '__main__':
    # Подгружаем данные для авторизации в почте
    my_email = DataBase.my_email
    password = DataBase.password

    # Настраиваем smtp протокол
    mail_settings = {
        "MAIL_SERVER": 'smtp.gmail.com',
        "MAIL_PORT": 465,
        "MAIL_USE_TLS": False,
        "MAIL_USE_SSL": True,
        "MAIL_USERNAME": my_email,
        "MAIL_PASSWORD": password
    }
    app.config.update(mail_settings)

    # Создаём отдельный поток, который получает обновления по акциям и отправляет сообщения
    t1 = threading.Thread(target=send_tickers)
    t1.start()

    app.run(host='0.0.0.0', port=4567)
