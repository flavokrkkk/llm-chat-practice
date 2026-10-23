migrate:
	uv run python scripts/migrate.py


seed:
	docker compose exec postgres psql -U llm-chat -d llm-chat -v ON_ERROR_STOP=1 -f /scripts/seed.sql