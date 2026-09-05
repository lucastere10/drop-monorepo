COMPOSE := docker compose
API := apps/api
WEB := apps/web
export DROP_ENV := local

.PHONY: db migrate seed api web dev up up-full down logs test

db:
	$(COMPOSE) up -d --wait db

migrate: db
	cd $(API) && uv run python manage.py migrate

seed: migrate
	cd $(API) && uv run python manage.py seed_data

api:
	cd $(API) && uv run python manage.py runserver

web:
	cd $(WEB) && pnpm dev

dev: seed
	@echo "Postgres is up and migrated."
	@echo "In two terminals:"
	@echo "  make api"
	@echo "  make web"

up:
	$(COMPOSE) up --build

up-full:
	$(COMPOSE) --profile full up --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

test:
	cd $(API) && uv run ruff check .
	cd $(API) && uv run pytest -q
