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
    """Вызывается, когда массив данных представлен неподходящем формате"""
    def __init__(self, expected_type, current_type):
        super().__init__(
            f'Неподходящий тип данных: ожидался - {expected_type}, '
            f'поступил - {current_type}'
        )
