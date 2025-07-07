# Guía de Instalación - Vision Wagon Project

## Requisitos del Sistema

### Software Requerido
- Python 3.8 o superior
- Node.js 16 o superior
- npm o yarn
- Git

### Dependencias Opcionales
- PostgreSQL 12+ (para producción)
- Redis (para cache y colas)
- Docker y Docker Compose (para despliegue)

## Instalación Paso a Paso

### 1. Clonar o Descargar el Proyecto

```bash
# Si tienes el proyecto en Git
git clone <repository-url>
cd vision_wagon_project

# O si tienes el archivo ZIP
unzip vision_wagon_project.zip
cd vision_wagon_project
```

### 2. Configurar el Backend (Python)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r vision_wagon/requirements.txt

# Instalar dependencias adicionales para desarrollo
pip install aiosqlite pytest pytest-asyncio
```

### 3. Configurar la Base de Datos

```bash
# Para desarrollo (SQLite - ya configurado)
# No se requiere configuración adicional

# Para producción (PostgreSQL)
# 1. Instalar PostgreSQL
# 2. Crear base de datos
createdb vision_wagon

# 3. Actualizar config.yaml con la URL de PostgreSQL
# database:
#   url: "postgresql://usuario:password@localhost:5432/vision_wagon"
```

### 4. Configurar el Frontend (React)

```bash
# Navegar al directorio del dashboard
cd clients/nomada_alpha/dashboard

# Instalar dependencias
npm install

# Dar permisos de ejecución (en sistemas Unix)
chmod +x node_modules/.bin/*
chmod +x node_modules/@esbuild/linux-x64/bin/esbuild

# Construir para producción
npm run build

# O ejecutar en modo desarrollo
npm run dev
```

### 5. Configuración del Sistema

```bash
# Copiar archivo de configuración de ejemplo
cp vision_wagon/config.yaml vision_wagon/config.yaml.backup

# Editar configuración según tus necesidades
nano vision_wagon/config.yaml
```

#### Configuraciones Importantes:

```yaml
# Para desarrollo
security:
  enable_authentication: false
  enable_authorization: false

# Para producción
security:
  enable_authentication: true
  enable_authorization: true
  jwt_secret_key: "tu-clave-secreta-muy-segura"

# Base de datos
database:
  url: "sqlite:///./vision_wagon.db"  # Desarrollo
  # url: "postgresql://user:pass@localhost:5432/vision_wagon"  # Producción
```

### 6. Inicializar la Base de Datos

```bash
# Ejecutar migraciones (si están configuradas)
cd vision_wagon
alembic upgrade head

# O crear las tablas manualmente ejecutando el sistema una vez
python -m vision_wagon.main
```

### 7. Verificar la Instalación

```bash
# Ejecutar pruebas básicas
python test_basic.py

# Debería mostrar:
# Total: 4 pruebas
# Pasaron: 3 o 4
# Fallaron: 0 o 1
```

## Ejecución del Sistema

### Modo Desarrollo

```bash
# Terminal 1: Backend
cd vision_wagon_project
source venv/bin/activate  # En Windows: venv\Scripts\activate
python -m vision_wagon.main

# Terminal 2: Frontend
cd clients/nomada_alpha/dashboard
npm run dev
```

### Modo Producción

```bash
# Construir frontend
cd clients/nomada_alpha/dashboard
npm run build

# Ejecutar backend
cd ../../..
source venv/bin/activate
python -m vision_wagon.main
```

### Usando Docker (Opcional)

```bash
# Construir y ejecutar con Docker Compose
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

## Acceso al Sistema

- **Backend API**: http://localhost:8000
- **Frontend Dashboard**: http://localhost:3000 (desarrollo) o http://localhost:8000 (producción)
- **Documentación API**: http://localhost:8000/docs
- **Grafana (si está habilitado)**: http://localhost:3000
- **Prometheus (si está habilitado)**: http://localhost:9090

## Solución de Problemas Comunes

### Error: "No module named 'aiosqlite'"
```bash
pip install aiosqlite
```

### Error: "Permission denied" en npm build
```bash
chmod +x node_modules/.bin/*
chmod +x node_modules/@esbuild/linux-x64/bin/esbuild
```

### Error: "JWT secret key es requerido"
Editar `vision_wagon/config.yaml` y establecer:
```yaml
security:
  enable_authentication: false
```

### Error de importación de módulos
Asegúrate de estar en el directorio correcto y que el entorno virtual esté activado:
```bash
cd vision_wagon_project
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Problemas con la base de datos
```bash
# Eliminar base de datos existente y recrear
rm vision_wagon.db
python -m vision_wagon.main
```

## Configuración Avanzada

### Variables de Entorno

Puedes usar variables de entorno para sobrescribir configuraciones:

```bash
export VISION_WAGON_CONFIG="/ruta/a/tu/config.yaml"
export DATABASE_URL="postgresql://user:pass@localhost:5432/vision_wagon"
export JWT_SECRET_KEY="tu-clave-secreta"
export ENVIRONMENT="production"
export DEBUG="false"
```

### Configuración de Agentes

Edita `vision_wagon/config.yaml` para habilitar/deshabilitar agentes:

```yaml
agents:
  assembly:
    enabled: true
    max_concurrent_tasks: 5
  
  coaching:
    enabled: true
    max_concurrent_tasks: 3
  
  moderation:
    enabled: false  # Deshabilitar si no es necesario
```

### Configuración de APIs Externas

Para usar funcionalidades avanzadas, configura las claves de API:

```yaml
api:
  openai_api_key: "tu-clave-openai"
  anthropic_api_key: "tu-clave-anthropic"
  stability_api_key: "tu-clave-stability"
```

## Mantenimiento

### Actualizar Dependencias

```bash
# Backend
pip install --upgrade -r vision_wagon/requirements.txt

# Frontend
cd clients/nomada_alpha/dashboard
npm update
```

### Backup de Base de Datos

```bash
# SQLite
cp vision_wagon.db vision_wagon.db.backup

# PostgreSQL
pg_dump vision_wagon > vision_wagon_backup.sql
```

### Logs

Los logs se guardan en:
- `logs/vision_wagon.log` (backend)
- Consola del navegador (frontend)

## Soporte

Para problemas o preguntas:
1. Revisa la documentación en `docs/`
2. Ejecuta las pruebas: `python test_basic.py`
3. Revisa los logs en `logs/vision_wagon.log`
4. Consulta el archivo `README.md` para más detalles

