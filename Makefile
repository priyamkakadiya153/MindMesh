# MindMesh Development Make Runner

.PHONY: install build dev-api dev-web db-up db-down db-migrate clean

install:
	npm install
	pip install -r apps/api/requirements.txt

build:
	node "node_modules/typescript/bin/tsc" --project "packages/shared"
	node "node_modules/vite/bin/vite.js" build "apps/web"

dev-api:
	cd apps/api && python -m uvicorn main:app --reload --port 4000

dev-web:
	npm run dev:web

db-up:
	docker-compose up -d

db-down:
	docker-compose down

db-migrate:
	cd apps/api && alembic upgrade head

db-revision:
	cd apps/api && alembic revision --autogenerate

clean:
	@powershell -Command "Remove-Item -Recurse -Force **/node_modules, **/dist, **/out, **/htmlcov, **/.pytest_cache, **/build -ErrorAction SilentlyContinue"
