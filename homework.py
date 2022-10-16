import json
import logging
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import (InvalidTokenError, WrongArrayTypeError,
                        WrongStausCodeError, MessageSendError,
                        ApiConnectionError, GetApiAnswerError, ApiJsonError,
                        CheckResponseError, ApiResponseKeyError)


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
RETRY_TTIME_MIN = RETRY_TIME / 60
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
        raise MessageSendError from error


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
    except requests.exceptions.ConnectionError as error:
        raise ApiConnectionError from error
    except Exception as error:
        logger.exception(f'Ошибка при запросе к API: {error}')
        raise GetApiAnswerError from error
    status_code = homework_statuses.status_code
    if status_code != HTTPStatus.OK:
        raise WrongStausCodeError(status_code)
    try:
        return homework_statuses.json()
    except json.JSONDecodeError as error:
        raise ApiJsonError from error


def check_response(response):
    """Проверяет ответ API на корректность.

    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python. Если ответ API соответствует
    ожиданиям, то функция должна вернуть список домашних работ
    (он может быть и пустым), доступный в ответе API по ключу 'homeworks'.
    """
    logger.info('Проверяем ответ API на корректность')
    try:
        homework_key = 'homeworks'
        homeworks = response[homework_key]
        response['current_date']
    # Когда перевожу TypeError на кастомное исключение, то тесты
    # почему-то не пропускают, поэтому оставил так...
    # пишет "test_check_response_not_dict FAILED", наверное,
    # в test_bot.py в 536 строке должно быть просто except, как
    # и в аналогичном тесте test_check_response_not_list (576 строка)
    except TypeError:
        raise TypeError(
            f'Неподходящий тип данных: ожидался - {dict}, '
            f'поступил - {type(response)}'
        )
    except KeyError as error:
        raise ApiResponseKeyError from error
    except Exception as error:
        logger.exception(f'Ошибка при проверке ответа API: {error}')
        raise CheckResponseError from error
    if type(homeworks) is not list:
        raise WrongArrayTypeError(list, type(homeworks))
    logger.info('Получен список домашних работ')
    return homeworks


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.

    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха, функция возвращает подготовленную для
    отправки в Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_STATUSES.
    """
    try:
        homework_name = homework['homework_name']
        status = homework['status']
    # Здесь я аналогично не смог перевести на кастомное исключение,
    # тесты ругаются...
    except KeyError:
        raise KeyError('Ключи в ответе API не соответствуют ожиданиям')
    try:
        verdict = HOMEWORK_STATUSES[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    # И здесь
    except KeyError:
        raise KeyError(
            'Обнаружен незадокументированный статус '
            f'домашней работы - {status}'
        )


def check_tokens():
    """Проверяет доступность переменных окружения, необходимых для работы.

    Если отсутствует хотя бы одна переменная окружения — функция
    должна вернуть False, иначе — True.
    """
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise InvalidTokenError
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    cash_status_hw_message = ''
    cash_error_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                status_hw_message = parse_status(homework[0])
                if status_hw_message != cash_status_hw_message:
                    logger.info(
                        'Изменился статус проверки домашней работы'
                    )
                    send_message(bot, status_hw_message)
                    current_timestamp = response.get(
                        'current_date',
                        current_timestamp
                    )
                    cash_status_hw_message = status_hw_message
            else:
                logger.info(
                    'Статус проверки домашней работы не изменился, '
                    f'следубщий запрос через {RETRY_TTIME_MIN} мин'
                )
        except Exception as error:
            error_message = f'Ошибка во время работы бота: {error}'
            logger.exception(error_message)
            if cash_error_message != error_message:
                send_message(bot, error_message)
                cash_error_message = error_message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
