from dotenv import load_dotenv
import os

load_dotenv('.env')


def get_env_value():
    env_values = {
        'DB_NAME': os.getenv('DB_NAME'),
        'DB_USER': os.getenv('DB_USER'),
        'DB_USER_PASSWORD': os.getenv('DB_USER_PASSWORD'),
        'TABLE_NAMES': os.getenv('TABLE_NAMES'),
        'PORT': os.getenv('PORT'),
        'HOST': os.getenv('HOST'),
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'DATA_URL': os.getenv('DATA_URL')
    }

    for key, value in env_values.items():
        if value is None:
            raise ValueError(f'Отсутствующая переменная окружения: {key}')

    return env_values
