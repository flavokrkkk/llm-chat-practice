from starlette import status

from .exceptions import AppException


class EmailAlreadyRegisteredError(AppException):
    """Регистрация с email, который уже занят (без учёта регистра)."""

    status_code = status.HTTP_409_CONFLICT
    error_code = "EMAIL_ALREADY_REGISTERED"


class InvalidCredentialsError(AppException):
    """Неверный email или пароль.

    Намеренно один и тот же ответ для обоих случаев,
    чтобы нельзя было узнать, зарегистрирован ли email.
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "INVALID_CREDENTIALS"


class InvalidTokenError(AppException):
    """Access- или refresh-токен недействителен: подпись, срок, отзыв."""

    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "INVALID_TOKEN"


class AccountDisabledError(AppException):
    """Учётные данные верны, но аккаунт деактивирован (is_active=False)."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = "ACCOUNT_DISABLED"
