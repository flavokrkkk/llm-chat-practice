# Комплексное исследование индексов в PostgreSQL (3M+ строк)

Практическое исследование поведения планировщика запросов PostgreSQL 16
(Cost-Based Optimizer) на базе данных объемом 3 000 000+ строк.

## 1. Составные индексы и порядок колонок (Composite Indexes)

**Бизнес-задача:** получение последних 50 сообщений конкретного чата (новые сверху).

**Запрос:**

```sql
SELECT id, chat_id, role, content, idempotency_key, created_at
FROM messages
WHERE chat_id = '0013b0b5-2d69-441f-b6c1-1c2d30215a02'
ORDER BY created_at DESC
LIMIT 50;
```

**Сравнение планов выполнения:**

| Конфигурация | Время (Execution Time) | Тип сканирования | Наличие Sort в RAM |
| --- | --- | --- | --- |
| Без индексов (Baseline) | ~2024.66 ms | Parallel Seq Scan (2 воркера) | Да (quicksort, 485 МБ I/O) |
| Одиночный (chat_id) | ~0.73 ms | Bitmap Index Scan | Да (Sort Method: quicksort) |
| Одиночный (created_at DESC) | ~194.70 ms | Parallel Seq Scan (игнор) | Да (индекс не подошел) |
| Составной (chat_id, created_at DESC) | ~0.63 ms | Index Scan | Нет (Zero Sort Overhead) |

**Выводы:**

- Правило левого префикса: составной индекс должен строиться в порядке: (колонки *точного* равенства, колонки *диапазона* или сортировки).
- Составной индекс `(chat_id, created_at DESC)` устраняет необходимость операции Sort в оперативной памяти, так как данные в дереве B-Tree физически упорядочены нужным образом.

## 2. Функциональные индексы (Expression Indexes)

**Бизнес-задача:** регистронезависимый поиск пользователя по email (GET /users/by-email).

**Запрос:**

```sql
SELECT id, email, balance, created_at
FROM users
WHERE lower(email) = 'user_5269@outlook.com';
```

**Сравнение планов:**

- Без функционального индекса (только стандартный UNIQUE по email):
  - Execution Time: 78.00 ms
  - План: Seq Scan on users (Rows Removed by Filter: 9999).
  - Причина: обычный B-Tree индекс не знает результатов применения функции `lower()`. База вынуждена последовательно сканировать таблицу и вычислять функцию для каждой строки.
- С функциональным индексом:

  ```sql
  CREATE INDEX idx_users_lower_email ON users (lower(email));
  ```

  - Execution Time: 0.94 ms (ускорение в ~80 раз).
  - План: Bitmap Index Scan on idx_users_lower_email.

- **Вывод:** функциональный индекс сохраняет в дереве сразу результат выполнения детерминированной функции. Условие в WHERE должно точно повторять выражение из индекса.

## 3. Подстрочный поиск: B-Tree vs GIN + pg_trgm

**Бизнес-задача:** поиск сообщений по подстроке (`WHERE content LIKE '%...%'`).

### Эксперимент 1: Обычный B-Tree индекс

```sql
CREATE INDEX idx_messages_content_btree ON messages(content);
SELECT * FROM messages WHERE content LIKE '%слово%';
```

- Execution Time: ~3544.07 ms (~3.5 секунды).
- План: Seq Scan on messages.
- Причина: B-Tree умеет искать только по префиксу (`'слово%'`). Маска с процентом в начале (`'%слово%'`) делает B-Tree бесполезным — планировщик уходит в полный скан диска.

### Эксперимент 2: Влияние селективности данных (Cost-Based Optimizer)

Запрос со словом, встречающимся в 100% строк: `WHERE content LIKE '%тестовое%'`:

- Execution Time: 1181.63 ms.
- План: Seq Scan on messages (GIN-индекс проигнорирован).
- **Вывод:** если условию удовлетворяет подавляющее большинство строк таблицы, чтение индекса + сборка Heap блоков дороже, чем последовательное чтение таблицы. Планировщик выбирает Seq Scan.

### Эксперимент 3: Селективный поиск через GIN + триграммы (pg_trgm)

```sql
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_messages_content_trgm ON messages USING gin (content gin_trgm_ops);

SELECT id, chat_id, content FROM messages WHERE content LIKE '%№444925%';
```

- Execution Time: 51.33 ms (среди 3 000 000 записей!).
- План: Bitmap Index Scan on idx_messages_content_trgm + Rows Removed by Index Recheck: 3.
- **Вывод:** GIN разбивает строки на триграммы (3-символьные срезы) и мгновенно локализует подходящие строки. Стадия Recheck отсекает ложноположительные совпадения хэшей триграмм.

## 4. Частичные индексы (Partial Indexes)

**Бизнес-задача:** оптимизация поиска сообщений конкретно от пользователей (`role = 'user'`), игнорируя системные сообщения и ответы ассистента (`role = 'assistant'`).

**DDL:**

```sql
CREATE INDEX idx_messages_user_role
ON messages (chat_id, created_at DESC)
WHERE role = 'user';
```

**Сравнение планов:**

- Запрос с `role = 'user'`:
  - Execution Time: 0.93 ms
  - План: Index Scan using idx_messages_user_role
  - Результат: точечное попадание в специализированный индекс без накладных расходов.

- Запрос с `role = 'assistant'`:
  - Execution Time: 3.18 ms
  - План: Bitmap Index Scan on idx_messages_chat_created + Filter: ((role)::text = 'assistant'::text) + Sort (quicksort)
  - Результат: планировщик корректно определил, что в частичном индексе записей с `role = 'assistant'` нет, и переключился на альтернативный общий индекс с последующей фильтрацией и сортировкой в памяти.

**Преимущества частичных индексов:**

- Экономия диска и RAM: индекс хранит только нужный срез данных (в 2 раза меньше при соотношении 50/50).
- Быстрее INSERT / UPDATE: при добавлении сообщений с другими ролями (`assistant`) частичный индекс не перезаписывается и не блокируется.

## 5. Сравнение пагинации: OFFSET vs KEYSET (Cursor) на 169 000+ строк

**Бизнес-задача:** пагинация истории сообщений в самом активном чате системы (chat_id = 'd4882a43-ea59-4e7d-93d0-e25c8925ecbc', объем: 169 214 сообщений).

**Используемый составной индекс:**

```sql
CREATE INDEX idx_messages_chat_keyset
ON messages (chat_id, created_at DESC, id DESC);
```

**Запросы:**

**OFFSET-подход:**

```sql
SELECT *
FROM messages
WHERE chat_id = $1
ORDER BY created_at DESC, id DESC
LIMIT 50 OFFSET $2;
```

**KEYSET-подход:**

```sql
SELECT *
FROM messages
WHERE chat_id = $1
AND (created_at, id) < ($2::timestamptz, $3::uuid)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

**Сводная таблица результатов:**

| Глубина пагинации (Смещение) | OFFSET (Execution Time) | KEYSET (Execution Time) | Разница в скорости |
| --- | --- | --- | --- |
| 0 (Первая страница) | 20.91 ms | 0.94 ms | Keyset быстрее в ~22 раза |
| 10 000 (Середина истории) | 3 484.87 ms (~3.5 сек) | 2.27 ms | Keyset быстрее в ~1 500 раз |
| 100 000 (Глубокая пагинация) | 4 607.34 ms (~4.6 сек) | 0.68 ms | Keyset быстрее в ~6 700 раз! |

**Детальный анализ планов выполнения:**

**Почему деградирует OFFSET:**

- Холостое сканирование: при OFFSET 100000 LIMIT 50 планировщик не может перепрыгнуть строки. Он обязан прочитать и отсортировать 100 050 строк, после чего отбросить первые 100 000.
- Сброс на диск (Disk Spilling): на глубине 100 000 объем данных превысил лимит оперативной памяти `work_mem`. В плане зафиксировано: `Sort Method: external merge Disk: 10136kB, temp read=2952 written=3781`.
- База начала писать промежуточные данные на диск во временные файлы, что привело к катастрофическому падению производительности до 4.6 секунд.

**Почему стабилен KEYSET:**

- Константная сложность `O(1)` относительно глубины: конструкция `WHERE (created_at, id) < (...)` выполняет B-Tree поиск прямо в индексе.
- Нулевой лишний I/O: база мгновенно попадает на точный узел дерева за `O(log N)` и считывает ровно 50 записей (shared hit=53). Предыдущие 100 000 сообщений вообще не считываются с диска и не обрабатываются.

## 6. Борьба с N+1: Оконные функции vs LEFT JOIN LATERAL vs json_agg

**Бизнес-задача:** получение списка всех чатов пользователя и последних 3 сообщений в каждом из них (GET /users/{id}/chats).

**Тестовый объект:** пользователь с user_id = '647b7fd2-7269-4aff-a94d-10335c6dbbd7', владеющий 26 чатами (суммарно 454 сообщения).

**Анализ подходов к решению проблемы:**

### 1. Наивный подход в цикле приложения (Classic N+1)

- **Архитектура:** 1 запрос на получение чатов пользователя + 26 отдельных запросов из Python к БД за последними 3 сообщениями для каждого найденного чата.
- **Итого запросов к СУБД:** 27 сетевых обращений (1 + N).
- **Минусы:** сетевой оверхед (Network RTT), блокировки пула соединений, деградация при росте количества чатов.

### 2. Оконная функция: ROW_NUMBER() OVER (PARTITION BY ...)

**Запрос:**

```sql
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
SELECT * FROM ranked_messages WHERE rn <= 3;
```

- Execution Time: 369.78 ms
- План: WindowAgg -> Sort (quicksort) -> Nested Loop (прочитаны все 454 сообщения).
- Причина низкой скорости: СУБД вынуждена выгрузить в оперативную память абсолютно все сообщения пользователя, отсортировать их в RAM и пронумеровать каждое, после чего отбросить лишние.

### 3. Продвинутый подход: LEFT JOIN LATERAL (... LIMIT 3)

**Запрос:**

```sql
SELECT c.id, c.title, m.id, m.content, m.created_at
FROM chats c
LEFT JOIN LATERAL (
    SELECT id, content, created_at
    FROM messages
    WHERE chat_id = c.id
    ORDER BY created_at DESC, id DESC
    LIMIT 3
) m ON true
WHERE c.user_id = '647b7fd2-7269-4aff-a94d-10335c6dbbd7';
```

- Execution Time: 0.49 ms (ускорение в ~750 раз относительно оконной функции!).
- План: Nested Loop Left Join -> Index Scan using idx_messages_chat_keyset (точечное чтение по 3 строки, 0 обращений к лишним данным).

### Архитектурный оптимум: LATERAL + jsonb_agg (Zero Python Mapping)

**Запрос:**

```sql
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
```

- Преимущество: агрегация вложенных коллекций выполняется на стороне движка базы данных в C-коде. Бэкенд получает строго 26 строк с уже сформированными JSON-массивами сообщений, минуя ручную склейку и группировку словарей в Python.

**Сводная таблица эффективности N+1:**

| Подход | Количество запросов к БД | Время выполнения (DB) | Сортировка лишних строк в RAM |
| --- | --- | --- | --- |
| Наивный (Python loop) | 27 запросов | ~30-50 ms + Network RTT | Нет |
| ROW_NUMBER() OVER | 1 запрос | 369.78 ms | Да (все 454 строки) |
| LEFT JOIN LATERAL | 1 запрос | 0.49 ms | Нет (только 76 строк) |

## 7. Аналитические выборки: Агрегации с GROUP BY и HAVING

**Бизнес-задача:** выгрузка топ-10 самых активных пользователей платформы за последние 7 дней (GET /stats/top-users).

**Запрос:**

```sql
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
```

**Ключевые архитектурные выводы:**

- Функциональная зависимость в PostgreSQL: при группировке по Primary Key (`GROUP BY u.id`) стандарт SQL в реализации PostgreSQL разрешает указывать любые неагрегированные столбцы этой же таблицы (`u.email`, `u.balance`, `u.created_at`) в блоке SELECT без необходимости их дублирования в GROUP BY.
- Разница между WHERE и HAVING: фильтрация по времени сообщений (`m.created_at >= NOW() - ...`) выполняется на этапе выборки строк до объединения (WHERE), в то время как фильтрация по агрегату `COUNT(m.id) > 0` происходит строго после этапа группировки (HAVING).

## 8. Транзакции, конкурентность и уровни изоляции (Race Conditions & Deadlocks)

**Практическое исследование финансовой операции перевода средств (POST /transfers) между пользователями.**

### Воспроизведение Race Condition (Lost Update / Double Spending)

**Сценарий нагрузки:** скрипт `scripts/race.py` отправляет 50 конкурентных HTTP-запросов по 100 руб. через `asyncio.gather` со счета с балансом 1000 руб. Ожидается: строго 10 успешных операций.

**Наивная реализация (Naive):** обычный `SELECT balance` -> проверка в Python -> два `UPDATE`. Временно отключено ограничение `CHECK (balance >= 0)`.

**Результат:**

- Успешно прошло 13 операций вместо 10.
- Итоговый баланс отправителя: -300.00 (уход в минус).
- На балансе получателя возникли лишние средства из воздуха (двойная трата / Double Spending).

### Сравнение 3 методов устранения Race Condition

| Способ устранения | Механизм | Результат race.py | Плюсы и минусы |
| --- | --- | --- | --- |
| `SELECT ... FOR UPDATE` | Пессимистическая блокировка строки (RowExclusiveLock) в транзакции. | 10 успешных / 40 отклон. (Баланс: 0.00) | Прост в реализации, но удерживает блокировку на всем протяжении транзакции. |
| Атомарный `UPDATE ... WHERE balance >= $1` | Перенос проверки баланса в предикат WHERE с анализом затронутых строк (RETURNING id). | 10 успешных / 40 отклон. (Баланс: 0.00) | Наиболее производительный. Минус 1 сетевой round-trip к БД, минимальное время удержания локов. |
| SERIALIZABLE + @retry | Использование наивысшего уровня изоляции транзакции с перехватом SerializationError (код 40001). | 10 успешных / 40 отклон. (Баланс: 0.00) | Декларативная надежность, но требует обязательной логики ретраев и дает накладные расходы при высокой конкурентности. |

### Исследование Deadlock (Взаимная блокировка)

**Сценарий воспроизведения:** встречные параллельные переводы двух пользователей друг другу:

```
A → B
B → A
```

**Ошибка СУБД:**

```text
asyncpg.exceptions.DeadlockDetectedError: deadlock detected
DETAIL: Process 41231 waits for ShareLock on transaction 1059; blocked by process 41232.
Process 41232 waits for ShareLock on transaction 1060; blocked by process 41231.
```

Фоновый процесс Postgres Deadlock Detector (таймаут 1 сек) обнаружил цикл взаимного ожидания и принудительно прервал одну из транзакций (Transaction Victim).

**Устранение (Deterministic Lock Ordering):** сортировка идентификаторов участников перед захватом блокировок:

```python
first_id, second_id = sorted([from_user_id, to_user_id])
```

Все транзакции захватывают строки в строго одинаковом порядке, исключая возможность возникновения цикла. Результат: 100% успешных запросов (200 OK) без дедлоков.

### Тестирование отката транзакций (Atomicity / Rollback)

Реализован интеграционный асинхронный тест `tests/test_transfers_rollback.py`:

- Вызов исключения (raise RuntimeError) в середине транзакции после первого UPDATE (списания средств).
- Результат: тест подтвердил (PASSED in 0.42s), что транзакция была полностью откачена (ROLLBACK), исходный баланс 1000.00 остался неизменным.

### Демонстрация аномалии Non-Repeatable Read (psql)

Сравнение поведения транзакций в двух параллельных сессиях psql:

**А. На уровне READ COMMITTED (По умолчанию):**

- Сессия 1: `BEGIN; SELECT balance ...;` -> Видит 1000.00.
- Сессия 2: `UPDATE users SET balance = 2000.00; (COMMIT)`.
- Сессия 1: повторный `SELECT balance ...;` -> Видит 2000.00!

**Вывод:** аномалия неповторяющегося чтения зафиксирована: данные изменились прямо в рамках одной незавершенной транзакции.

**Б. На уровне REPEATABLE READ:**

- Сессия 1: `BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ; SELECT balance ...;` -> Видит 1000.00.
- Сессия 2: `UPDATE users SET balance = 5000.00; (COMMIT)`.
- Сессия 1: повторный `SELECT balance ...;` -> Видит 1000.00.
- **Вывод:** на уровне Repeatable Read транзакция изолирована моментальным снимком (MVCC Snapshot), созданным на момент первого чтения, и гарантирует консистентность на протяжении всей своей жизни.
- Сессия 1: `COMMIT;`
- Сессия 1: новый `SELECT` вне транзакции -> Видит 5000.00.

## 9. Идемпотентность API (Idempotency Key)

**Бизнес-задача:** защита от дублирования сообщений при сетевых сбоях и повторных кликах (POST /chats/{id}/messages с заголовком Idempotency-Key).

### Архитектурное решение в СУБД

```sql
CREATE UNIQUE INDEX idx_messages_chat_idempotency
ON messages (chat_id, idempotency_key);
```

```sql
INSERT INTO messages (chat_id, role, content, idempotency_key)
VALUES ($1, $2, $3, $4)
ON CONFLICT (chat_id, idempotency_key) DO NOTHING
RETURNING id, chat_id, role, content, idempotency_key, created_at;
```

- Если строка не вставилась (RETURNING вернул None), сервис выполняет fallback SELECT и возвращает клиенту уже созданную запись.

### Результаты конкурентного теста (scripts/message-idempotency-check.py):

**Сценарий:** 20 одновременных запросов с одинаковым ключом через `asyncio.gather`.

- Результат:
  - Успешных ответов (200 OK): 20 из 20
  - Ошибок: 0
  - Создано физических записей в БД: строго 1 (ID: e02b0070-f8e3-4276-a2b8-5af47cacdbf8).

**Почему проверка «сначала SELECT, потом INSERT» не работает (TOCTOU):**

- При параллельных запросах все конкурентные потоки одновременно выполнят SELECT, увидят отсутствие записи и одновременно попытаются сделать INSERT, что приведет либо к дублированию данных (если нет UNIQUE), либо к падению с UniqueViolationError у всех запросов, кроме первого. Только атомарный ON CONFLICT на уровне СУБД решает проблему гонки.

## 10. Кэширование и Rate Limiting в Redis

### Rate Limiter (Алгоритм Fixed Window)

**Реализация:** зависимость FastAPI (RateLimiter) с использованием атомарных команд Redis:

```text
INCR rate_limit:messages:{user_id}
EXPIRE rate_limit:messages:{user_id} 60 (только при первом инкременте)
```

### Результаты тестирования:

#### Rate Limiter

- Запросы 1–10: 200 OK
- Запросы 11+: 429 Too Many Requests (срабатывание лимита).

#### Кэширование аналитики: Паттерн Cache-Aside

- **Эндпоинт:** GET /stats/top-users (тяжелый аналитический запрос с JOIN, GROUP BY и HAVING по 3M строк).
- **Срок жизни кэша (TTL):** 60 секунд.

**Замеры задержки (Latency):**

| Состояние кэша | Время ответа (Round Trip) | Источник данных |
| --- | --- | --- |
| Cache Miss (Первый запрос) | 325 ms | PostgreSQL (диск/индексы) |
| Cache Hit (Повторные запросы) | 9 – 13 ms | Redis (In-Memory RAM) |

- **Эффективность:** ускорение в ~30 раз. Нагрузка на СУБД снята.

---

**Время окончания работы над проектом:** 24.10.2026, 23:20
