import psycopg2


def get_records(pool, table, limit=None, offset=None, where=None):
    conn = pool.getconn()  # получаем подключение из пула
    cur = None
    rows = None

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Формирование SQL-запроса
        sql = f'SELECT * FROM "{table}"'
        params = []

        if where:
            sql += " WHERE " + " AND ".join(f"{k} = %s" for k in where.keys())
            params.extend(where.values())

        sql += " ORDER BY id"

        if limit and offset:
            sql += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

        # Выполнение SQL-запроса
        cur.execute(sql, params)
        rows = cur.fetchall()
    except Exception as e:
        # Обработка и вывод ошибки
        print(f"Произошла следующая ошибка: {str(e)}")
        conn.rollback()
    finally:
        if cur is not None:
            cur.close()
        pool.putconn(conn)  # возвращаем подключение обратно в пул

    return rows


def get_table_columns(pool, table):
    conn = pool.getconn()
    cur = conn.cursor()
    columns = None

    try:
        # Получение списка колонок из информационной схемы, исключая 'id' и 'hash', в правильном порядке
        cur.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = %s AND column_name NOT IN ('id', 'hash', 'role_id', 'password') ORDER BY ordinal_position", (table,))
        columns = [row[0] for row in cur.fetchall()]
    except Exception as e:
        # Обработка и вывод ошибки
        print(f"Произошла следующая ошибка: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        pool.putconn(conn)

    return columns


def get_count(pool, table):
    conn = pool.getconn()
    try:
        cur = conn.cursor()

        # Выполнение запроса на получение общего количества записей в таблице
        cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cur.fetchone()[0]
        return count
    except Exception as e:
        # Обработка и вывод ошибки
        print(f"Произошла следующая ошибка: {str(e)}")
        conn.rollback()
    finally:
        pool.putconn(conn)


def insert_record(pool, table, columns, role_id):
    conn = pool.getconn()

    if role_id in [1, 2]:
        values = (0, '', 0, 0, '', '1998-12-28', '2023-06-17', '', '', '', '')
    elif role_id == 3:
        values = ('', '', '', '', '', '')
    else:
        return "Invalid role"

    try:
        cur = conn.cursor()

        # Формирование SQL-запроса на вставку записи
        cols = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(values))
        query = f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})'
        cur.execute(query, values)
        conn.commit()
    except Exception as e:
        # Обработка и вывод ошибки
        print(f"Произошла следующая ошибка: {str(e)}")
        conn.rollback()
    finally:
        pool.putconn(conn)


def update_record(pool, table, columns, values, id):
    conn = pool.getconn()
    try:
        cur = conn.cursor()

        # Формирование SQL-запроса на обновление записи
        updates = ', '.join([f'{column} = %s' for column in columns])
        query = f'UPDATE "{table}" SET {updates} WHERE id = %s'
        cur.execute(query, (*values, id))
        conn.commit()
    except Exception as e:
        # Обработка и вывод ошибки
        print(f"Произошла следующая ошибка: {str(e)}")
        conn.rollback()
    finally:
        pool.putconn(conn)
