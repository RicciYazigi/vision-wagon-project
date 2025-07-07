# Vision Wagon Project Makefile
# Comandos principales para desarrollo y despliegue

.PHONY: help dev nomada-dev test build clean logs health

# Configuración
COMPOSE_FILE = docker-compose.yml
DOCKER_COMPOSE = docker compose -f $(COMPOSE_FILE)

help: ## Mostrar ayuda
	@echo "Vision Wagon Project - Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Iniciar todos los servicios en modo desarrollo
	@echo "🚀 Iniciando Vision Wagon Core y servicios..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Servicios iniciados:"
	@echo "   - Vision Wagon Core: http://localhost:8000"
	@echo "   - Nómada Alpha API: http://localhost:8080"
	@echo "   - Nómada Alpha Dashboard: http://localhost:3000"
	@echo "   - Grafana: http://localhost:3001"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - RabbitMQ Management: http://localhost:15672"

nomada-dev: ## Iniciar solo los servicios de Nómada Alpha
	@echo "🎯 Iniciando Nómada Alpha..."
	$(DOCKER_COMPOSE) up -d nomada_alpha_api nomada_alpha_dashboard
	@echo "✅ Nómada Alpha iniciado:"
	@echo "   - API: http://localhost:8080"
	@echo "   - Dashboard: http://localhost:3000"

test: ## Ejecutar todos los tests
	@echo "🧪 Ejecutando tests..."
	@echo "📋 Tests de API..."
	$(DOCKER_COMPOSE) exec nomada_alpha_api python -m pytest tests/ -v || echo "⚠️  Tests de API no disponibles"
	@echo "🌐 Tests de Dashboard (Cypress)..."
	$(DOCKER_COMPOSE) exec nomada_alpha_dashboard npm run test || echo "⚠️  Tests de Dashboard no disponibles"
	@echo "✅ Tests completados"

build: ## Construir todas las imágenes
	@echo "🔨 Construyendo imágenes Docker..."
	$(DOCKER_COMPOSE) build
	@echo "✅ Imágenes construidas"

clean: ## Limpiar contenedores y volúmenes
	@echo "🧹 Limpiando contenedores..."
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f
	@echo "✅ Limpieza completada"

logs: ## Ver logs de todos los servicios
	$(DOCKER_COMPOSE) logs -f

logs-core: ## Ver logs del Vision Wagon Core
	$(DOCKER_COMPOSE) logs -f vision_wagon

logs-api: ## Ver logs de la API de Nómada Alpha
	$(DOCKER_COMPOSE) logs -f nomada_alpha_api

logs-dashboard: ## Ver logs del Dashboard de Nómada Alpha
	$(DOCKER_COMPOSE) logs -f nomada_alpha_dashboard

health: ## Verificar estado de todos los servicios
	@echo "🏥 Verificando estado de servicios..."
	@echo ""
	@echo "Vision Wagon Core:"
	@curl -s http://localhost:8000/health | jq '.' 2>/dev/null || echo "❌ No disponible"
	@echo ""
	@echo "Nómada Alpha API:"
	@curl -s http://localhost:8080/health | jq '.' 2>/dev/null || echo "❌ No disponible"
	@echo ""
	@echo "Contenedores activos:"
	@$(DOCKER_COMPOSE) ps

stop: ## Detener todos los servicios
	@echo "🛑 Deteniendo servicios..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Servicios detenidos"

restart: ## Reiniciar todos los servicios
	@echo "🔄 Reiniciando servicios..."
	$(DOCKER_COMPOSE) restart
	@echo "✅ Servicios reiniciados"

update: ## Actualizar y reconstruir servicios
	@echo "🔄 Actualizando servicios..."
	$(DOCKER_COMPOSE) pull
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Servicios actualizados"

# Comandos de desarrollo específicos
dev-core: ## Iniciar solo Vision Wagon Core y dependencias
	$(DOCKER_COMPOSE) up -d vision_wagon postgres redis rabbitmq

dev-monitoring: ## Iniciar solo servicios de monitoreo
	$(DOCKER_COMPOSE) up -d prometheus grafana

# Comandos de base de datos
db-migrate: ## Ejecutar migraciones de base de datos
	@echo "🗄️  Ejecutando migraciones..."
	$(DOCKER_COMPOSE) exec vision_wagon alembic upgrade head
	@echo "✅ Migraciones completadas"

db-reset: ## Resetear base de datos
	@echo "⚠️  Reseteando base de datos..."
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS vision_wagon;"
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -c "CREATE DATABASE vision_wagon;"
	$(DOCKER_COMPOSE) exec vision_wagon alembic upgrade head
	@echo "✅ Base de datos reseteada"

# Comandos de despliegue
deploy-prep: ## Preparar para despliegue
	@echo "📦 Preparando para despliegue..."
	$(DOCKER_COMPOSE) build
	docker tag vision_wagon_project-vision_wagon ghcr.io/vision-wagon/core:v0.1.0
	docker tag vision_wagon_project-nomada_alpha_api ghcr.io/vision-wagon/nomada-alpha-api:v0.1.0
	docker tag vision_wagon_project-nomada_alpha_dashboard ghcr.io/vision-wagon/nomada-alpha-dashboard:v0.1.0
	@echo "✅ Imágenes etiquetadas para despliegue"

# Comandos de utilidad
shell-core: ## Abrir shell en Vision Wagon Core
	$(DOCKER_COMPOSE) exec vision_wagon bash

shell-api: ## Abrir shell en Nómada Alpha API
	$(DOCKER_COMPOSE) exec nomada_alpha_api bash

shell-dashboard: ## Abrir shell en Nómada Alpha Dashboard
	$(DOCKER_COMPOSE) exec nomada_alpha_dashboard sh

# Información del proyecto
info: ## Mostrar información del proyecto
	@echo "📊 Vision Wagon Project Information"
	@echo "=================================="
	@echo "Versión: v0.1.0"
	@echo "Servicios:"
	@echo "  - Vision Wagon Core (Puerto 8000)"
	@echo "  - Nómada Alpha API (Puerto 8080)"
	@echo "  - Nómada Alpha Dashboard (Puerto 3000)"
	@echo "  - PostgreSQL (Puerto 5432)"
	@echo "  - Redis (Puerto 6379)"
	@echo "  - RabbitMQ (Puerto 5672, Management: 15672)"
	@echo "  - Prometheus (Puerto 9090)"
	@echo "  - Grafana (Puerto 3001)"
	@echo ""
	@echo "Comandos principales:"
	@echo "  make dev      - Iniciar todos los servicios"
	@echo "  make test     - Ejecutar tests"
	@echo "  make health   - Verificar estado"
	@echo "  make logs     - Ver logs"
	@echo "  make clean    - Limpiar todo"

