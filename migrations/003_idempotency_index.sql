-- 1. Удаляем старый одиночный уникальный констрейнт
ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_idempotency_key_key;
-- 2. Создаем правильный составной уникальный индекс для идемпотентности
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_chat_idempotency ON messages (chat_id, idempotency_key);