.DEFAULT_GOAL := help

.PHONY: help up down logs migrate seed demo-user superuser test check

help:
	@echo "Targets: up, down, logs, migrate, seed, demo-user, superuser, test, check"

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f zain-store-web

migrate:
	docker compose exec zain-store-web python manage.py migrate

seed:
	docker compose exec zain-store-web python manage.py seed_catalog

demo-user:
	@test -n "$(DEMO_PASSWORD)" || (echo "Set DEMO_PASSWORD before running this target."; exit 2)
	docker compose exec zain-store-web python manage.py create_demo_customer --password "$(DEMO_PASSWORD)"

superuser:
	docker compose exec zain-store-web python manage.py createsuperuser

test:
	docker compose exec zain-store-web python manage.py test

check:
	docker compose exec zain-store-web python manage.py check --deploy
