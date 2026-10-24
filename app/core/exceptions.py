class AppException(Exception):
    """Базовый класс ошибок приложения.

    Наследуется всеми бизнес- и доменными ошибками сервиса и несет
    HTTP-статус код и человекочитаемый код ошибки для клиента.

    Пример использования:
        raise NotFoundError("Chat not found")
    """

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message

        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


class NotFoundError(AppException):
    """Ресурс в базе данных не найден."""

    status_code = 404
    error_code = "NOT_FOUND"


class BadRequestError(AppException):
    """Некорректный запрос со стороны клиента."""

    status_code = 400
    error_code = "BAD_REQUEST"


class ConflictError(AppException):
    """Конфликт с существующими данными (например, дубликат операции)."""

    status_code = 409
    error_code = "CONFLICT"


class InsufficientFundsError(AppException):
    """У клиента недостаточно средств для выполнения операции."""

    status_code = 400
    error_code = "INSUFFICIENT_FUNDS"


class RateLimitExceededError(AppException):
    """Превышен лимит запросов (rate limit)."""

    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
