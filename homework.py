import json
import logging
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import (InvalidTokenError, WrongArrayTypeError,
                        WrongStausCodeError)

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(name)s - '
    '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправялет сообщения в телеграмм чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение отправлено в телеграмм!')
    except Exception as error:
        logger.exception(f'Сообщение не отправлено: {error}')
        raise


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра функция получает временную метку.
    В случае успешного запроса должна вернуть ответ API,
    преобразовав его из формата JSON к типам данных Python.
    """
    params = {'from_date': current_timestamp}
    logger.info('Начат запрос к API')
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except requests.exceptions.ConnectionError:
        logger.exception(
            'Ошибка во время соединения с API, '
            'проверьте подключение к интернету'
        )
        raise
    except Exception:
        logger.exception('Непредвиденная ошибка во время соеденения с API')
        raise
    status_code = homework_statuses.status_code
    try:
        assert status_code == HTTPStatus.OK
    except Exception as error:
        logger.exception('Код ответа API != 200')
        raise WrongStausCodeError(status_code) from error
    try:
        return homework_statuses.json()
    except json.JSONDecodeError:
        logger.exception(
            'Ошибка во время преобразования ответа API к формату JSON'
        )
        raise


def check_response(response):
    """Проверяет ответ API на корректность.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python. Если ответ API соответствует
    ожиданиям, то функция должна вернуть список домашних работ
    (он может быть и пустым), доступный в ответе API по ключу 'homeworks'.
    """
    try:
        homework_key = 'homeworks'
        homework = response[homework_key]
    except KeyError:
        logger.exception(f'В ответе API отсутствует ключ {homework_key}')
        raise
    try:
        expected_type = list
        assert isinstance(homework, expected_type)
    except Exception as error:
        logger.exception('Некорректный тип данных')
        raise WrongArrayTypeError(expected_type, type(homework)) from error
    logger.info('Получен список домашних работ')
    return homework


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха, функция возвращает подготовленную для
    отправки в Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_STATUSES.
    """
    try:
        homework_name_key = 'homework_name'
        homework_name = homework[homework_name_key]
    except KeyError:
        logger.exception(
            f'Невозможно получить имя домашней работы '
            f'по ключу {homework_name_key}'
        )
        raise
    status = homework.get('status')
    try:
        verdict = HOMEWORK_STATUSES[status]
    except KeyError:
        logger.exception(
            f'Обнаружен незадокументированный статус '
            f'домашней работы 'f'- {status}.'
        )
        raise
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения, необходимых для работы.
    Если отсутствует хотя бы одна переменная окружения — функция
    должна вернуть False, иначе — True.
    """
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    send_message(
        bot,
        'Привет, Я заступил в дежурство, с этого момента '
        'я начинаю отслеживать все новые статусы домашних работ, '
        'если что-нибудь появится, я обязательно тебе сообщу!'
    )
    current_timestamp = int(time.time())
    while True:
        try:
            assert check_tokens()
        except AssertionError as error:
            logger.exception(
                'Проблема при получении токенов'
            )
            raise InvalidTokenError from error
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
                logger.info(
                    'Изменился статус проверки домашней работы'
                )
                send_message(bot, message)
                current_timestamp = int(time.time())
            else:
                logger.info(
                    f'Статус проверки домашней работы не изменился, '
                    f'следубщий запрос через {RETRY_TIME/60} мин'
                )
        except Exception as error:
            message = f'Ошибка во время работы бота {error}'
            logger.exception(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
