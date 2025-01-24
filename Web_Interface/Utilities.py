from flask import request, render_template
from flask_paginate import get_page_parameter
from config import get_env_value

env_data = get_env_value()


def get_table_name(role_id):
    try:
        if role_id in [1, 2]:
            return env_data['TABLE_NAMES'].split(",")[0]
        elif role_id == 3:
            return env_data['TABLE_NAMES'].split(",")[1]
    except Exception as e:
        print(f"Произошла следующая ошибка: {str(e)}")


def get_pagination_parameters():
    try:
        per_page = int(request.args.get('per_page', 10))
        page = request.args.get(get_page_parameter(), type=int, default=1)
        offset = (page - 1) * per_page
        return per_page, page, offset
    except Exception as e:
        print(f"Произошла следующая ошибка: {str(e)}")


def render_interface(role_id, table, pagination):
    """Выбор интерфейса в соответствии с ролью пользователя."""
    if role_id == 1:
        return render_template('branch_interface.html', table=table, pagination=pagination)
    elif role_id == 2:
        return render_template('headquarters_interface.html', table=table, pagination=pagination)
    elif role_id == 3:
        return render_template('moderator.html', users_table=table, pagination=pagination, template='moderator.html')
    else:
        return "Invalid role"


def extract_guarantee_data_from_record(record):
    """Извлечь данные для гарантии из полученной записи."""
    if len(record) >= 12:
        return {
            'serial_number': record[1],
            'applicant': record[2],
            'agreement_number': record[3],
            'amount': record[4],
            'currency': record[5],
            'start_date': str(record[6]),
            'expiration_date': str(record[7]),
            'branch': record[11],
        }
    else:
        print("Ошибка: запись содержит недостаточное количество элементов")
        return None
