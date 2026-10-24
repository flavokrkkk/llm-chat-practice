Комплексное исследование индексов в PostgreSQL (3M+ строк)
Практическое исследование поведения планировщика запросов PostgreSQL 16 (Cost-Based Optimizer) на базе данных объемом 3 000 000+ строк.

1. Составные индексы и порядок колонок (Composite Indexes)
   Бизнес-задача: Получение последних 50 сообщений конкретного чата (новые сверху).
   Запрос:

SELECT id, chat_id, role, content, idempotency_key, created_at
FROM messages
WHERE chat_id = '0013b0b5-2d69-441f-b6c1-1c2d30215a02'
ORDER BY created_at DESC
LIMIT 50;

Сравнение планов выполнения:
Конфигурация Время (Execution Time) Тип сканирования Наличие Sort в RAM
Без индексов (Baseline) ~2024.66 ms Parallel Seq Scan (2 воркера) Да (quicksort, 485 МБ I/O)
Одиночный (chat_id) ~0.73 ms Bitmap Index Scan Да (Sort Method: quicksort)
Одиночный (created_at DESC) ~194.70 ms Parallel Seq Scan (игнор) Да (индекс не подошел)
Составной (chat_id, created_at DESC) ~0.63 ms Index Scan Нет (Zero Sort Overhead)

Выводы:
Правило левого префикса: Составной индекс должен строиться в порядке: (колонки*точного*равенства, колонки*диапазона*или_сортировки).
Составной индекс (chat_id, created_at DESC) устраняет необходимость операции Sort в оперативной памяти, так как данные в дереве B-Tree физически упорядочены нужным образом.

2. Функциональные индексы (Expression Indexes)

Бизнес-задача: Регистронезависимый поиск пользователя по email (GET /users/by-email).
Запрос:

SELECT id, email, balance, created_at
FROM users
WHERE lower(email) = 'user_5269@outlook.com';

Сравнение планов:
Без функционального индекса (только стандартный UNIQUE по email):
Execution Time: 78.00 ms
План: Seq Scan on users (Rows Removed by Filter: 9999).
Причина: Обычный B-Tree индекс не знает результатов применения функции lower(). База вынуждена последовательно сканировать таблицу и вычислять функцию для каждой строки.
С функциональным индексом CREATE INDEX idx_users_lower_email ON users (lower(email)):
Execution Time: 0.94 ms (ускорение в ~80 раз).
План: Bitmap Index Scan on idx_users_lower_email.
Вывод: Функциональный индекс сохраняет в дереве сразу результат выполнения детерминированной функции. Условие в WHERE должно точно повторять выражение из индекса.

3. Подстрочный поиск: B-Tree vs GIN + pg_trgm
   Бизнес-задача: Поиск сообщений по подстроке WHERE content LIKE '%...%'.
   Эксперимент 1: Обычный B-Tree индекс

CREATE INDEX idx_messages_content_btree ON messages(content);
SELECT \* FROM messages WHERE content LIKE '%слово%';

Execution Time: ~3544.07 ms (~3.5 секунды).
План: Seq Scan on messages.
Причина: B-Tree умеет искать только по префиксу ('слово%'). Маска с процентом в начале ('%слово%') делает B-Tree бесполезным — планировщик уходит в полный скан диска.
Эксперимент 2: Влияние селективности данных (Cost-Based Optimizer)
Запрос со словом, встречающимся в 100% строк: WHERE content LIKE '%тестовое%':
Execution Time: 1181.63 ms.
План: Seq Scan on messages (GIN-индекс проигнорирован).
Вывод: Если условию удовлетворяет подавляющее большинство строк таблицы, чтение индекса + сборка Heap блоков дороже, чем последовательное чтение таблицы. Планировщик выбирает Seq Scan.
Эксперимент 3: Селективный поиск через GIN + триграммы (pg_trgm)

CREATE EXTENSION pg_trgm;
CREATE INDEX idx_messages_content_trgm ON messages USING gin (content gin_trgm_ops);

SELECT id, chat_id, content FROM messages WHERE content LIKE '%№444925%';

Execution Time: 51.33 ms (среди 3 000 000 записей!).
План: Bitmap Index Scan on idx_messages_content_trgm + Rows Removed by Index Recheck: 3.
Вывод: GIN разбивает строки на триграммы (3-символьные срезы) и мгновенно локализует подходящие строки. Стадия Recheck отсекает ложноположительные совпадения хэшей триграмм.

4. Частичные индексы (Partial Indexes)
   Бизнес-задача: Оптимизация поиска сообщений конкретно от пользователей (role = 'user'), игнорируя системные сообщения и ответы ассистента (role = 'assistant').
   DDL:

CREATE INDEX idx_messages_user_role
ON messages (chat_id, created_at DESC)
WHERE role = 'user';

Сравнение планов:
Запрос с role = 'user':
Execution Time: 0.93 ms
План: Index Scan using idx_messages_user_role
Результат: Точечное попадание в специализированный индекс без накладных расходов.
Запрос с role = 'assistant':
Execution Time: 3.18 ms
План: Bitmap Index Scan on idx_messages_chat_created + Filter: ((role)::text = 'assistant'::text) + Sort (quicksort)
Результат: Планировщик корректно определил, что в частичном индексе записей с role = 'assistant' нет, и переключился на альтернативный общий индекс с последующей фильтрацией и сортировкой в памяти.
Преимущества частичных индексов:
Экономия диска и RAM: Индекс хранит только нужный срез данных (в 2 раза меньше при соотношении 50/50).
Быстрее INSERT / UPDATE: При добавлении сообщений с другими ролями (assistant) частичный индекс не перезаписывается и не блокируется.
