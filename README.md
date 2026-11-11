Ожидаю	Метод у Result	Получаю
ровно одно значение	.scalar_one()	значение; если строк 0 или больше 1 — ошибка
одно значение или ничего	.scalar_one_or_none()	значение или None
список моделей или значений одной колонки	.scalars().all()	список
несколько колонок, по строке на запись	.mappings().all()	


uv run python scripts/loop-lag.py
PYTHONASYNCIODEBUG=1 uv run uvicorn app.main:app --reload --port 8080

<!-- Тесты -->
uv run pytest -v                                   # имя каждого теста и результат
uv run pytest tests/unit/test_error_handlers.py    # один файл
uv run pytest -k "refresh"                         # только тесты, в названии которых есть "refresh"
uv run pytest -x                                   # остановиться на первом упавшем
uv run pytest --lf                                 # перезапустить только упавшие в прошлый раз
uv run pytest -m "not api"                         # только unit, без сервера
uv run pytest -s                                   # показывать print() из тестов