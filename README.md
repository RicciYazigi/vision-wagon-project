# Vision Wagon Project

Sistema de IA Generativa y Automatización para el ecosistema Nómada Alpha.

## Descripción

Vision Wagon es un sistema completo de inteligencia artificial que integra múltiples agentes especializados para la generación, moderación y ensamblaje de contenido digital. Diseñado específicamente para el ecosistema Nómada Alpha, proporciona una plataforma robusta para la automatización de flujos de trabajo creativos.

## Características Principales

- **Sistema de Agentes Inteligentes**: Múltiples agentes especializados trabajando en conjunto
- **Dashboard Interactivo**: Interfaz web moderna construida con React
- **Orquestación Avanzada**: Coordinación inteligente de tareas y flujos de trabajo
- **Base de Datos Integrada**: Gestión completa de contenido y metadatos
- **Seguridad y Moderación**: Validación automática de contenido
- **Arquitectura Escalable**: Diseño modular y extensible

## Agentes Incluidos

### Agentes Operacionales
- **Assembly Agent**: Ensambla activos generados en productos finales
- **Coaching Agent**: Proporciona orientación y mejoras de contenido
- **Moderation Agent**: Valida y modera contenido automáticamente
- **Narrative Architect Agent**: Diseña y estructura narrativas complejas

### Agentes de Campaña
- **Campaign Agent**: Gestiona campañas de contenido completas

## Estructura del Proyecto

```
vision_wagon_project/
├── vision_wagon/              # Código principal del sistema
│   ├── agents/               # Agentes inteligentes
│   ├── cli/                  # Interfaz de línea de comandos
│   ├── constructor/          # Constructores y generadores
│   ├── tests/               # Pruebas unitarias
│   ├── main.py              # Punto de entrada principal
│   ├── orchestrator.py      # Coordinador central
│   ├── database.py          # Gestión de base de datos
│   └── config.yaml          # Configuración del sistema
├── clients/                  # Aplicaciones cliente
│   └── nomada_alpha/        # Cliente Nómada Alpha
│       └── dashboard/       # Dashboard web React
├── infra/                   # Infraestructura
│   ├── grafana/            # Monitoreo
│   ├── nginx/              # Proxy reverso
│   └── prometheus/         # Métricas
├── docs/                    # Documentación
└── tests/                   # Pruebas de integración
```

## Instalación

### Requisitos Previos
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis (opcional, para cache)

### Instalación del Backend

```bash
# Clonar el repositorio
git clone https://github.com/visionwagon/vision-wagon.git
cd vision-wagon

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r vision_wagon/requirements.txt

# Configurar base de datos
cp vision_wagon/config.yaml.example vision_wagon/config.yaml
# Editar config.yaml con tus configuraciones

# Ejecutar migraciones
alembic upgrade head
```

### Instalación del Frontend

```bash
# Navegar al dashboard
cd clients/nomada_alpha/dashboard

# Instalar dependencias
npm install

# Construir para producción
npm run build

# O ejecutar en desarrollo
npm run dev
```

## Uso

### Ejecutar el Sistema Principal

```bash
# Desde el directorio raíz
python -m vision_wagon.main

# O usando el CLI
vision-wagon start
```

### Ejecutar el Dashboard

```bash
# En modo desarrollo
cd clients/nomada_alpha/dashboard
npm run dev

# En modo producción (después de build)
npm run preview
```

## Configuración

El sistema se configura a través del archivo `vision_wagon/config.yaml`:

```yaml
database:
  url: "postgresql://user:password@localhost/vision_wagon"
  
agents:
  assembly:
    enabled: true
    max_concurrent_tasks: 5
  
  coaching:
    enabled: true
    model: "gpt-4"
  
  moderation:
    enabled: true
    strict_mode: false

orchestrator:
  max_workers: 10
  task_timeout: 300
```

## API

El sistema expone una API REST completa:

- `GET /api/agents` - Lista todos los agentes
- `POST /api/tasks` - Crea una nueva tarea
- `GET /api/tasks/{task_id}` - Obtiene el estado de una tarea
- `GET /api/content` - Lista contenido generado
- `POST /api/campaigns` - Crea una nueva campaña

## Desarrollo

### Estructura de Agentes

Para crear un nuevo agente, extiende la clase `BaseAgent`:

```python
from vision_wagon.agents.core.base_agent import BaseAgent, AgentResult

class MiNuevoAgent(BaseAgent):
    agent_id = "mi_nuevo_agent"
    agent_type = "operational"
    description = "Descripción de mi agente"
    capabilities = ["capacidad1", "capacidad2"]
    
    async def process(self, context):
        # Lógica del agente
        return AgentResult(success=True, data={"resultado": "éxito"})
```

### Pruebas

```bash
# Ejecutar todas las pruebas
python -m pytest

# Ejecutar pruebas específicas
python -m pytest tests/test_agents.py

# Ejecutar con cobertura
python -m pytest --cov=vision_wagon
```

## Despliegue

### Docker

```bash
# Construir imagen
docker build -t vision-wagon .

# Ejecutar contenedor
docker run -p 8000:8000 vision-wagon
```

### Docker Compose

```bash
# Ejecutar stack completo
docker-compose up -d
```

## Monitoreo

El sistema incluye métricas y monitoreo integrado:

- **Grafana**: Dashboard de métricas en `http://localhost:3000`
- **Prometheus**: Métricas en `http://localhost:9090`
- **Logs**: Disponibles en `logs/vision_wagon.log`

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## Soporte

Para soporte y preguntas:
- Email: support@visionwagon.com
- Issues: [GitHub Issues](https://github.com/visionwagon/vision-wagon/issues)
- Documentación: [Wiki del Proyecto](https://github.com/visionwagon/vision-wagon/wiki)

## Roadmap

- [ ] Integración con más modelos de IA
- [ ] Soporte para múltiples idiomas
- [ ] API GraphQL
- [ ] Plugins y extensiones
- [ ] Interfaz móvil
- [ ] Integración con servicios cloud

