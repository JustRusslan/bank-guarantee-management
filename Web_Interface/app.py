import time

from flask import Flask, render_template, redirect, request, session, url_for
from flask_paginate import Pagination
import bcrypt

from config import get_env_value
from DataBase import create_conn
from DataBaseFunctions import get_records, get_table_columns, get_count, insert_record, update_record
from Guarantee import generate_hash, generate_guarantee_with_qr
from Utilities import get_table_name, get_pagination_parameters, render_interface, extract_guarantee_data_from_record

env_data = get_env_value()

app = Flask(__name__)
app.config['SECRET_KEY'] = env_data['SECRET_KEY']

pool = create_conn(env_data['DB_NAME'], env_data['DB_USER'],
                   env_data['DB_USER_PASSWORD'], env_data['HOST'], env_data['PORT'])


@app.route('/')
def index():
    return render_template('authorisation.html')


@app.route('/sign_in', methods=['POST'])
def sign_in():
    username = request.form['username']
    password_to_check = request.form.get('password').encode('utf-8')

    try:
        # Выполняем запрос на получение пользователя с данным именем
        user = dict(get_records(pool, env_data['TABLE_NAMES'].split(
            ",")[1], where={"login": username})[0])

        # Определение параметров пагинации
        per_page, page, offset = get_pagination_parameters()

        # Проверяем существование пользователя и совпадение пароля
        if user and bcrypt.checkpw(password_to_check, user['password'].encode('utf-8')):
            session['role_id'] = user['role_id']
            table_name = get_table_name(session['role_id'])

            # Получение подмножества таблицы гарантий для текущей страницы
            table_subset = get_records(
                pool, table_name, limit=per_page, offset=offset)
            total_count = get_count(pool, table_name)
            pagination = Pagination(
                page=page, per_page=per_page, total=total_count, css_framework='bootstrap4')

            return render_interface(session['role_id'], table_subset, pagination)

        else:
            return render_template('authorisation.html', error=True)

    except Exception as e:
        print(f"Произошла следующая ошибка: {str(e)}")


@app.route('/sign_out', methods=['POST'])
def sign_out():
    session.pop('role_id', None)
    return redirect('/')


@app.route('/success')
def success():
    # Определение параметров пагинации
    per_page, page, offset = get_pagination_parameters()

    try:
        # В зависимости от роли пользователя выбираем нужную таблицу
        table_name = get_table_name(session['role_id'])

        # Получаем общее количество записей в таблице и подмножество таблицы для текущей страницы
        table_subset = get_records(
            pool, table_name, limit=per_page, offset=offset)

        count = get_count(pool, table_name)

        new_count = count + 1
        new_pages = int((new_count + per_page - 1) / per_page)

        # Проверяем, не превышает ли номер страницы количество страниц, которые теперь доступны
        if page > new_pages:
            page = new_pages

    except Exception as e:
        print(f"Произошла следующая ошибка: {str(e)}")

    # Создаем объект пагинации и отображаем отфильтрованные записи с помощью соответствующего интерфейса
    pagination = Pagination(page=page, per_page=per_page,
                            total=new_count, css_framework='bootstrap4')

    return render_interface(session['role_id'], table_subset, pagination)


@app.route('/add', methods=['POST'])
def add():
    try:
        # В зависимости от роли пользователя выбираем нужную таблицу
        table_name = get_table_name(session['role_id'])

        # Получение списка колонок текущей таблицы
        columns = get_table_columns(pool, table_name)

        # Выполнение запроса на получение общего количества записей в соответствующей таблице
        count = get_count(pool, table_name)

        # Создание новой записи в таблице со значениями по умолчанию
        insert_record(pool, table_name, columns, session['role_id'])

        # Получение номера последней страницы таблицы
        last_page = -(-count // 10) if count > 0 else 1

    except Exception as e:
        # Обработка и вывод ошибки
        print(f"Произошла следующая ошибка: {str(e)}")

    # Перенаправление пользователя на последнюю страницу таблицы
    return redirect(url_for('success', page=last_page))


@app.route('/update', methods=['GET', 'POST'])
def update():
    try:
        # Получение данных из формы
        form_data = request.form

        # Получение идентификатора из формы
        id = form_data['id']

        # Получение имени таблицы в зависимости от роли пользователя
        table_name = get_table_name(session['role_id'])

        # Получение списка колонок текущей таблицы
        columns = get_table_columns(pool, table_name)

        # Получение значений из формы для каждой колонки
        values = [form_data.get(column) for column in columns]

        # Обновление записи в базе данных
        update_record(pool, table_name, columns, values, id)

    except Exception as e:
        # Обработка и вывод ошибки
        print(f"Произошла следующая ошибка: {str(e)}")

    # Перенаправление на страницу 'success'
    return redirect(url_for('success'))


@app.route('/filter', methods=['GET'])
def filter():
    # Определение параметров пагинации
    per_page, page, offset = get_pagination_parameters()

    # Получение имени таблицы в зависимости от роли пользователя
    table_name = get_table_name(session['role_id'])

    # Получение параметров фильтрации из запроса
    filter_keys = get_table_columns(pool, table_name)

    filter_params = {key: request.args.get(key) for key in filter_keys}

    # Удаление пустых параметров фильтрации
    filter_params = {k: v for k, v in filter_params.items()
                     if v is not None and v != ''}

    # Получение отфильтрованных записей из таблицы журнала
    filtered_records = get_records(
        pool, env_data['TABLE_NAMES'].split(",")[0], limit=per_page, offset=offset, where=filter_params)
    total_count = get_count(pool, env_data['TABLE_NAMES'].split(",")[0])

    # Создание объекта пагинации с использованием полученных параметров
    pagination = Pagination(page=page, per_page=per_page,
                            total=total_count, css_framework='bootstrap4')

    # Отображение отфильтрованных записей с помощью соответствующего интерфейса
    return render_interface(session['role_id'], filtered_records, pagination)


@app.route('/generate_guarantee', methods=['GET'])
def generate_guarantee():
    try:
        # 1. Получить значение параметра 'id' из аргументов запроса
        id = request.args.get('id')
        if not id:
            return "Error: No id provided. Please specify an id."

        # 2. Получить запись из таблицы по заданному id
        record = get_records(pool, env_data['TABLE_NAMES'].split(",")[
                             0], where={"id": id})
        if not record:
            return f"Error: No record found for id {id}."

        # 3. Подготовить данные для гарантии на основе полученной записи
        data = extract_guarantee_data_from_record(record[0])

        # 4. Сгенерировать хеш для данных гарантии
        hash = generate_hash(data)

        # 5. Обновить запись в таблице новым хешем
        update_record(pool, env_data['TABLE_NAMES'].split(
            ",")[0], ['hash'], [hash], id)

        # 6. Генерировать гарантию с QR-кодом на основе подготовленных данных и сгенерированного хеша
        generate_guarantee_with_qr(data, hash)

        # 7. Отобразить шаблон 'guarantee.html' с переданными данными
        return render_template('guarantee.html', time=int(time.time()))

    except Exception as e:
        # возвращаем сообщение об ошибке как строку для отображения
        print(f"Произошла следующая ошибка: {str(e)}")


@app.route('/validate_guarantee', methods=['GET'])
def validate_and_display_guarantee():
    try:
        # 1. Получить значение параметра 'hash' из аргументов запроса
        hash_value = request.args.get('hash')
        if not hash_value:
            return "Ошибка: Не указан хэш. Пожалуйста, укажите хэш."

        # 2. Получить результат запроса (первую запись)
        record = get_records(pool, env_data['TABLE_NAMES'].split(",")[0],
                             where={"hash": hash_value})

        # 3. Проверить, была ли найдена запись с указанным хешем
        if record:
            # 4. Создать словарь с данными из найденной записи
            data = extract_guarantee_data_from_record(record[0])

            # 5. Отобразить шаблон 'confirmation_letter.html' с переданными данными
            return render_template('confirmation_letter.html', data=data)
        else:
            # 6. Вернуть сообщение об ошибке и код ошибки 404, если запись не найдена
            return "Гарантия не найдена или недействительна", 404

    except Exception as e:
        # возвращаем сообщение об ошибке как строку для отображения
        print(f"Произошла следующая ошибка: {str(e)}")


@app.route('/back', methods=['GET', 'POST'])
def go_back():
    return redirect(url_for('success'))


if __name__ == '__main__':
    app.run(debug=True)
