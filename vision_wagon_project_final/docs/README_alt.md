# Proyecto Integrado: Vision Wagon + Nómada Alpha

Un ecosistema full-stack que combina **Vision Wagon** (backend de IA para orquestación de agentes) y **Nómada Alpha** (juego interactivo global con narrativa generativa y participación comunitaria), con un dashboard React para gestión y monitoreo.

## Características
- **Backend**: FastAPI, PostgreSQL, RabbitMQ, Redis, Auth0, Stripe, OpenSea.
- **Frontend**: React 18, Tailwind CSS, D3.js, i18next para localización.
- **Infraestructura**: Docker, Terraform para AWS ECS, Blue/Green Deployment, GitHub Actions.
- **Monetización**: Suscripciones (Voyeur, Participant, Creator) y NFTs.
- **Observabilidad**: Prometheus, Grafana, alertas en Slack.
- **Testing**: 95%+ cobertura con pytest, Jest, Cypress.

## Instalación
1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/proyecto-integrado-vision-wagon-nomada-alpha.git
   cd proyecto-integrado-vision-wagon-nomada-alpha
   ```
2. Configura los archivos `.env` en `backend/vision_wagon/`, `backend/nomada_alpha/`, y `frontend/` con las claves de Auth0, Stripe, OpenSea, etc.
3. Instala dependencias:
   ```bash
   pip install -r backend/vision_wagon/requirements.txt
   pip install -r backend/nomada_alpha/requirements.txt
   cd frontend && npm install
   ```
4. Despliega localmente:
   ```bash
   docker-compose up
   ```
5. Accede a:
   - Frontend: `http://localhost`
   - Vision Wagon API: `http://localhost:8000`
   - Nómada Alpha API: `http://localhost:8080`
   - Grafana: `http://localhost:3000`
   - Prometheus: `http://localhost:9090`

## Despliegue en Producción
1. Configura Terraform:
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform apply -var="db_password=your_password" -var="subnets=[...]" -var="vpc_id=..."
   ```
2. Configura secretos en GitHub Actions.
3. Push para activar CI/CD.

## Documentación
- [API](docs/api.md)
- [Despliegue](docs/deployment.md)
- [Testing](docs/testing.md)
- [Monetización](docs/monetization.md)

## Contribuir
1. Crea un fork del repositorio.
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`).
3. Commitea tus cambios (`git commit -m "Añadir nueva funcionalidad"`).
4. Push a la rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request.

## Licencia
MIT License