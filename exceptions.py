class InvalidTokenError(Exception):
    """Вызывается, когда хотя бы один из токенов невалидный."""

    def __init__(self):
        super().__init__('Отсутствуют один или несколько токенов.')


class WrongStausCodeError(Exception):
    """Вызывается, когда статус код эндпоинта неравен 200."""

    def __init__(self, status_code):
        super().__init__(
            f'Ошибка, статус кода при запросе к API = {status_code}'
        )


class WrongArrayTypeError(Exception):
    """Вызывается, когда массив данных представлен неподходящем формате."""

    def __init__(self, expected_type, current_type):
        super().__init__(
            f'Неподходящий тип данных: ожидался - {expected_type}, '
            f'поступил - {current_type}'
        )


class MessageSendError(Exception):
    """Вызывается, если не получилось отправить сообщение"""

    def __init__(self):
        super().__init__('Ошибка во время отправки сообщения ботом.')


class ApiConnectionError(Exception):
    """Вызывается, когда не получилось установить соединение с API"""

    def __init__(self):
        super().__init__(
            'Ошибка во время соединения с API, '
            'проверьте подключение к интернету.'
        )


class GetApiAnswerError(Exception):
    """Вызывается, когда возникла ошибка при запросе к API"""

    def __init__(self):
        super().__init__(
            'Ошибка при запросе к API'
        )


class ApiJsonError(Exception):
    """Вызывается, когда возникла ошибка при реобразования ответа API к JSON"""

    def __init__(self):
        super().__init__(
            'Ошибка во время преобразования ответа API к JSON'
        )


class CheckResponseError(Exception):
    """Вызывается, когда возникла ошибка при проверке ответа API"""

    def __init__(self):
        super().__init__(
            'Ошибка во время проверки ответа API'
        )


class ApiResponseKeyError(Exception):
    """Вызывается, когда ключи в ответе API не соответствуют ожиданиям"""

    def __init__(self):
        super().__init__(
            'Ключи в ответе API не соответствуют ожиданиям'
        )


# class UnknownHomeworkStatusError(Exception):
#     """Вызывается, когда обнаруживается неизвестный статус домашней работы"""

#     def __init__(self, homework_status):
#         super().__init__(
#             'Обнаружен незадокументированный статус '
#             f'домашней работы - {homework_status}.'
#         )
