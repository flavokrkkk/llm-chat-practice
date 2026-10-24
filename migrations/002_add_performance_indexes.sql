-- Подключаем pg_trgm
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Функциональный индекс для email
CREATE INDEX IF NOT EXISTS idx_users_lower_email ON users (lower(email));
-- GIN индекс для подстрочного поиска
CREATE INDEX IF NOT EXISTS idx_messages_content_trgm ON messages USING gin (content gin_trgm_ops);
-- Частичный индекс для сообщений пользователей
CREATE INDEX IF NOT EXISTS idx_messages_user_role ON messages (chat_id, created_at DESC)
WHERE role = 'user';
-- Составной индекс для Keyset-пагинации
CREATE INDEX IF NOT EXISTS idx_messages_chat_keyset ON messages (chat_id, created_at DESC, id DESC);