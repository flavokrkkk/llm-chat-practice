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

5. Сравнение пагинации: OFFSET vs KEYSET (Cursor) на 169 000+ строк
   Бизнес-задача: Пагинация истории сообщений в самом активном чате системы (chat_id = 'd4882a43-ea59-4e7d-93d0-e25c8925ecbc', объем: 169 214 сообщений).

Используемый составной индекс:

CREATE INDEX idx_messages_chat_keyset
ON messages (chat_id, created_at DESC, id DESC);

Запросы:
OFFSET-подход:
SELECT _ FROM messages
WHERE chat_id = $1
ORDER BY created_at DESC, id DESC
LIMIT 50 OFFSET $2;
SELECT _ FROM messages
WHERE chat_id = $1
AND (created_at, id) < ($2::timestamptz, $3::uuid)
ORDER BY created_at DESC, id DESC
LIMIT 50;

Сводная таблица результатов:
Глубина пагинации (Смещение) OFFSET (Execution Time) KEYSET (Execution Time) Разница в скорости
0 (Первая страница) 20.91 ms 0.94 ms Keyset быстрее в ~22 раза
10 000 (Середина истории) 3 484.87 ms (~3.5 сек) 2.27 ms Keyset быстрее в ~1 500 раз
100 000 (Глубокая пагинация) 4 607.34 ms (~4.6 сек) 0.68 ms Keyset быстрее в ~6 700 раз!

Детальный анализ планов выполнения:
Почему деградирует OFFSET:
Холостое сканирование: При OFFSET 100000 LIMIT 50 планировщик не может перепрыгнуть строки. Он обязан прочитать и отсортировать 100 050 строк, после чего отбросить первые 100 000.
Сброс на диск (Disk Spilling): На глубине 100 000 объем данных превысил лимит оперативной памяти work_mem. В плане зафиксировано:
Sort Method: external merge Disk: 10136kB, temp read=2952 written=3781.
База начала писать промежуточные данные на диск во временные файлы, что привело к катастрофическому падению производительности до 4.6 секунд.
Почему стабилен KEYSET:
Константная сложность
O
(
1
)
O(1)
относительно глубины: Конструкция WHERE (created_at, id) < (...) выполняет B-Tree поиск прямо в индексе.
Нулевой лишний I/O: База мгновенно попадает на точный узел дерева за
O
(
log
⁡
N
)
O(logN)
и считывает ровно 50 записей (shared hit=53). Предыдущие 100 000 сообщений вообще не считываются с диска и не обрабатываются.

6. Борьба с N+1: Оконные функции vs LEFT JOIN LATERAL vs json_agg
   Бизнес-задача: Получение списка всех чатов пользователя и последних 3 сообщений в каждом из них (GET /users/{id}/chats).
   Тестовый объект: Пользователь с user_id = '647b7fd2-7269-4aff-a94d-10335c6dbbd7', владеющий 26 чатами (суммарно 454 сообщения).
   Анализ подходов к решению проблемы:
1. Наивный подход в цикле приложения (Classic N+1)
   Архитектура: 1 запрос на получение чатов пользователя + 26 отдельных запросов из Python к БД за последними 3 сообщениями для каждого найденного чата.
   Итого запросов к СУБД: 27 сетевых обращений (1 + N).
   Минусы: Сетевой оверхед (Network RTT), блокировки пула соединений, деградация при росте количества чатов.
1. Оконная функция: ROW_NUMBER() OVER (PARTITION BY ...)

WITH ranked_messages AS (
SELECT
c.id AS chat_id, c.title, m.id, m.content, m.created_at,
ROW_NUMBER() OVER (
PARTITION BY m.chat_id
ORDER BY m.created_at DESC
) AS rn
FROM chats c
JOIN messages m ON m.chat_id = c.id
WHERE c.user_id = '647b7fd2-7269-4aff-a94d-10335c6dbbd7'
)
SELECT \* FROM ranked_messages WHERE rn <= 3;

Execution Time: 369.78 ms
План: WindowAgg -> Sort (quicksort) -> Nested Loop (прочитаны все 454 сообщения).
Причина низкой скорости: СУБД вынуждена выгрузить в оперативную память абсолютно все сообщения пользователя, отсортировать их в RAM и пронумеровать каждое, после чего отбросить лишние.

3. Продвинутый подход: LEFT JOIN LATERAL (... LIMIT 3)

SELECT c.id, c.title, m.id, m.content, m.created_at
FROM chats c
LEFT JOIN LATERAL (
SELECT id, content, created_at
FROM messages
WHERE chat_id = c.id
ORDER BY created_at DESC
LIMIT 3
) m ON true
WHERE c.user_id = '647b7fd2-7269-4aff-a94d-10335c6dbbd7';

Execution Time: 0.49 ms (ускорение в ~750 раз относительно оконной функции!).
План: Nested Loop Left Join -> Index Scan using idx_messages_chat_keyset (точечное чтение по 3 строки, 0 обращений к лишним данным).

Архитектурный оптимум: LATERAL + jsonb_agg (Zero Python Mapping)

SELECT
c.id, c.user_id, c.title, c.created_at,
COALESCE(
jsonb_agg(
jsonb_build_object(
'id', m.id,
'content', m.content,
'role', m.role,
'created_at', m.created_at
)
) FILTER (WHERE m.id IS NOT NULL),
'[]'::jsonb
) AS last_messages
FROM chats c
LEFT JOIN LATERAL (
SELECT id, content, role, created_at
FROM messages
WHERE chat_id = c.id
ORDER BY created_at DESC, id DESC
LIMIT 3
) m ON TRUE
WHERE c.user_id = $1
GROUP BY c.id;

Преимущество: Агрегация вложенных коллекций выполняется на стороне движка базы данных в C-коде. Бэкенд получает строго 26 строк с уже сформированными JSON-массивами сообщений, минуя ручную склейку и группировку словарей в Python.

Сводная таблица эффективности N+1:
Подход Количество запросов к БД Время выполнения (DB) Сортировка лишних строк в RAM
Наивный (Python loop) 27 запросов ~30-50 ms + Network RTT Нет
ROW_NUMBER() OVER 1 запрос 369.78 ms Да (все 454 строки)
LEFT JOIN LATERAL 1 запрос 0.49 ms Нет (только 76 строк)

7. Аналитические выборки: Агрегации с GROUP BY и HAVING
   Бизнес-задача: Выгрузка топ-10 самых активных пользователей платформы за последние 7 дней (GET /stats/top-users).

SELECT
u.id AS user_id,
u.email,
u.balance,
u.created_at,
COUNT(m.id) AS messages_count
FROM users u
INNER JOIN chats c ON c.user_id = u.id
INNER JOIN messages m ON m.chat_id = c.id
WHERE m.created_at >= NOW() - INTERVAL '7 days'
GROUP BY u.id
HAVING COUNT(m.id) > 0
ORDER BY messages_count DESC
LIMIT 10;

Ключевые архитектурные выводы:
Функциональная зависимость в PostgreSQL: При группировке по Primary Key (GROUP BY u.id) стандарт SQL в реализации PostgreSQL разрешает указывать любые неагрегированные столбцы этой же таблицы (u.email, u.balance, u.created_at) в блоке SELECT без необходимости их дублирования в GROUP BY.
Разница между WHERE и HAVING: Фильтрация по времени сообщений (m.created_at >= NOW() - ...) выполняется на этапе выборки строк до объединения (WHERE), в то время как фильтрация по агрегату COUNT(m.id) > 0 происходит строго после этапа группировки (HAVING).
