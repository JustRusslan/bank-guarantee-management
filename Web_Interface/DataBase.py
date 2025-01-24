from psycopg2 import OperationalError, pool, extras
import psycopg2


def create_conn(database, user, password, host, port):
    conn_pool = None
    try:
        conn_pool = psycopg2.pool.SimpleConnectionPool(1, 10,   # значения minconn и maxconn
                                                       database=database,
                                                       user=user,
                                                       password=password,
                                                       host=host,
                                                       port=port,
                                                       )
        print("Пул подключений к BankGuaranteesDB успешно создан")
    except OperationalError as e:
        print(f"Произошла следующая ошибка: {str(e)}")
    return conn_pool
