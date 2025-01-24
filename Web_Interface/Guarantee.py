from PIL import Image, ImageDraw, ImageFont
from num2words import num2words
import datetime
import qrcode
import os
import datetime
import hashlib

from config import get_env_value

env_data = get_env_value()


def generate_hash(data):
    # 1. Создать список строк, представляющих значения словаря
    data_str = "".join([str(value) for value in data.values()])

    # 2. Преобразовать строку data_str в байты с использованием кодировки UTF-8
    data_bytes = data_str.encode('utf-8')

    # 3. Вычислить хеш-значение строки с помощью алгоритма SHA-256
    sha256_hash = hashlib.sha256(data_bytes)

    # 4. Получить шестнадцатеричное представление хеша
    hex_hash = sha256_hash.hexdigest()

    # 5. Вернуть полученный хеш
    return hex_hash


def generate_bank_guarantee(template_path, output_path, data, qr_code_image):
    # 1. Открыть изображение-шаблон гарантии
    image = Image.open(template_path)

    # 2. Создать объект ImageDraw для рисования на изображении
    draw = ImageDraw.Draw(image)

    # 3. Загрузить шрифт для добавления текста
    font_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "static", "fonts", "times.ttf")
    font = ImageFont.truetype(font_path, 28)

    # 4. Получить текущую дату и отформатировать её
    today = datetime.date.today()
    today_str = today.strftime('%d-%m-%Y')

    # 5. Отформатировать даты начала и окончания гарантии
    start_date = data['start_date']
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    start_date = start_date.strftime('%d-%m-%Y')

    expiration_date = data['expiration_date']
    expiration_date = datetime.datetime.strptime(expiration_date, '%Y-%m-%d')
    expiration_date = expiration_date.strftime('%d-%m-%Y')

    # 6. Заполнить поля шаблона гарантии данными из словаря 'data'
    draw.text((320, 235), str(
        data['agreement_number']), font=font, fill="black")
    draw.text((295, 271), str(today_str), font=font, fill="black")
    draw.text((1220, 519), str(data['applicant']), font=font, fill="black")
    draw.text((580, 844), str(data['branch']), font=font, fill="black")
    draw.text((285, 992), str(data['amount']), font=font, fill="black")
    draw.text((485, 992), num2words(
        str(int(data['amount'])), lang='ru'), font=font, fill="black")
    draw.text((775, 992), str(data['currency']), font=font, fill="black")
    draw.text((1110, 1690), str(start_date), font=font, fill="black")
    draw.text((1290, 1725), str(expiration_date), font=font, fill="black")

    # 7. Открыть изображение QR-кода и добавить его на шаблон гарантии
    qr_code = Image.open(qr_code_image)
    image.paste(qr_code, (1220, 1995))

    # 8. Сохранить готовое изображение гарантии с заполненными данными
    image.save(output_path)


def generate_guarantee_with_qr(data, hash):
    # 1. Создание URL для проверки гарантии с использованием хеша
    data_url = f"{env_data['DATA_URL']}/validate_guarantee?hash={hash}"

    # 2. Создание QR-кода, содержащего URL для проверки гарантии
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(data_url)
    qr.make(fit=True)
    qr_code = qr.make_image(fill_color="black", back_color="white")

    # 3. Определение путей файлов
    qr_temp_path = os.path.join('static', 'images', 'qr_temp.png')
    guarantee_template_path = os.path.join(
        'static', 'images', 'guarantee_temp.jpg')
    img_folder = os.path.join('static', 'images')
    img_path = os.path.join(img_folder, 'guarantee_with_qr.jpg')

    # 4. Сохранение QR-кода во временный файл
    qr_code.save(qr_temp_path)

    # 5. Создание необходимой директории, если она не существует
    os.makedirs(img_folder, exist_ok=True)

    # 6. Удаление существующего файла с гарантией, если он есть
    if os.path.exists(img_path):
        os.remove(img_path)

    # 7. Вызов функции generate_bank_guarantee для создания банковской гарантии с данными и QR-кодом
    generate_bank_guarantee(guarantee_template_path,
                            img_path, data, qr_temp_path)

    # 8. Удаление временного файла с QR-кодом после использования
    if os.path.exists(qr_temp_path):
        os.remove(qr_temp_path)
