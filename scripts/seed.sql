BEGIN;
TRUNCATE users,
chats,
messages,
transfers RESTART IDENTITY CASCADE;
-- 1. ЗАПОЛНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ
INSERT INTO users (
        email,
        balance,
        full_name,
        password_hash,
        created_at
    )
SELECT 'user_' || gs || '@' || (ARRAY ['gmail.com', 'yahoo.com', 'outlook.com']) [FLOOR(RANDOM() * 3 + 1)] AS email,
    ROUND((RANDOM() * 10000)::NUMERIC, 2) AS balance,
    'User ' || gs AS full_name,
    '$argon2id$v=19$m=65536,t=3,p=4$JtpHXhmX7naiQeNZ+BsbJw$jeNLu2OPXYqiS8Q8ETGp2w0GJQH6ucqSdEU7KJKrXCY' AS password_hash,
    NOW() - (gs || ' hours')::INTERVAL AS created_at
FROM generate_series(1, 10000) AS gs;
-- 2. ЗАПОЛНЕНИЕ ЧАТОВ (WITH жестко связан с INSERT)
WITH user_list AS (
    SELECT array_agg(id) AS ids
    FROM users -- Исправлено: берем из users, а не users_demo
)
INSERT INTO chats (user_id, title, created_at)
SELECT ids [floor(random() * array_length(ids, 1) + 1)] as user_id,
    'Чат №' || gs as title,
    NOW() - (RANDOM() * 5000 || ' minutes')::INTERVAL as created_at
FROM generate_series(1, 100000) AS gs
    CROSS JOIN user_list;
-- 3. ЗАПОЛНЕНИЕ СООБЩЕНИЙ (Все CTE и INSERT объединены в один блок)
WITH chat_list AS (
    -- Собираем все ID чатов в массив
    SELECT array_agg(id) AS ids
    FROM chats
),
random_assignments AS (
    -- Генерируем строк и рассчитываем неравномерный индекс чата
    SELECT ids [floor(POWER(random(), 4) * array_length(ids, 1)) + 1] AS chat_id,
        -- Случайно выбираем роль: 50/50 user или assistant
        (ARRAY ['user', 'assistant']) [floor(random() * 2 + 1)] AS role,
        gs
    FROM generate_series(1, 3000000) AS gs
        CROSS JOIN chat_list
)
INSERT INTO messages (
        chat_id,
        role,
        content,
        idempotency_key,
        created_at
    )
SELECT chat_id,
    role,
    'Это тестовое сообщение №' || gs || ' для чата ' || chat_id AS content,
    -- Идемпотентность: делаем уникальный ключ
    'key_msg_' || gs AS idempotency_key,
    -- Время: случайный разброс за последние 30 дней
    NOW() - (random() * 43200 || ' minutes')::INTERVAL AS created_at
FROM random_assignments;
COMMIT;
-- Обновляем статистику БД для корректной работы будущих индексов
ANALYZE;