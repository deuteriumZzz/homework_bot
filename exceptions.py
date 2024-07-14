class TokenError(Exception):
    """Исключение для ошибок, связанных с токенами."""
    pass


class APIRequestError(Exception):
    """Исключение для ошибок, связанных с запросами к API."""
    pass


class APIResponseError(Exception):
    """Исключение для ошибок, связанных с ответами API."""
    pass


class HomeworkStatusError(Exception):
    """Исключение для ошибок, связанных со статусом домашней работы."""
    pass
