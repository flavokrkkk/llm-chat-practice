Ожидаю	Метод у Result	Получаю
ровно одно значение	.scalar_one()	значение; если строк 0 или больше 1 — ошибка
одно значение или ничего	.scalar_one_or_none()	значение или None
список моделей или значений одной колонки	.scalars().all()	список
несколько колонок, по строке на запись	.mappings().all()	


uv run python scripts/loop-lag.py
PYTHONASYNCIODEBUG=1 uv run uvicorn app.main:app --port 8080