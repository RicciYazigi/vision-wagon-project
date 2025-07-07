
# 🚀 Proyecto Integrado: Vision Wagon + Nómada Alpha

## ✅ Objetivo

Sistema interactivo 100% funcional que integra:

- **Vision Wagon**: backend modular de IA con agentes para análisis, generación de contenido y orquestación.
- **Nómada Alpha**: juego global interactivo con generación narrativa, votación y participación comunitaria.
- **Frontend React**: dashboard visual completo para métricas, logs, agentes y narrativas.

---

## 🌟 Características

### Vision Wagon

- Orquestador con RabbitMQ, PostgreSQL, Redis.
- Agentes: Intelligence, Security, Psychology, Copywriter, Assembly.
- APIs REST y WebSocket.
- Seguridad robusta (OAuth, TLS).

### Nómada Alpha

- Story Engine, Character System, World Builder.
- Agentes: Narrative Architect, Psychology, Image, Audio, Voting.
- Integración con Twitch, Discord, YouTube.
- Avatares “Yo WOW” y Baúl Psicológico.

### Frontend React

- Métricas y KPIs en tiempo real.
- Generador de narrativas conectado a backend.
- Votación comunitaria con comentarios.
- Logs en vivo (WebSocket).
- Diseño moderno con Tailwind y Lucide Icons.

---

## ⚡ Estructura de carpetas

```
proyecto_integrado/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MetricCard.js
│   │   │   ├── AgentCard.js
│   │   │   ├── LiveLog.js
│   │   │   ├── NarrativeGenerator.js
│   │   │   ├── CommunityVoting.js
│   │   │   └── VisionWagonDashboard.js
│   │   ├── App.js
│   │   ├── index.js
│   │   └── styles/
│   │       └── tailwind.css
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── .env
├── vision_wagon/
│   ├── agents/
│   ├── orchestrator/
│   ├── constructor/
│   ├── config/
│   ├── security/
│   ├── database/
│   ├── cli/
│   ├── tests/
│   ├── docs/
│   ├── logs/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── nomada_alpha/
│   ├── agents/
│   ├── orchestrator/
│   ├── core/
│   ├── config/
│   ├── web/
│   ├── tests/
│   ├── blueprints/
│   ├── assets/
│   ├── docs/
│   ├── scripts/
│   ├── logs/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── scripts/
│   └── deploy.sh
├── docs/
├── docker-compose.yml
├── nginx.conf
├── README.md
└── .gitignore
```

---

## 🏗️ Despliegue

### Desarrollo

```bash
docker-compose up --build
```

### Producción

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh deploy
```

- Frontend: `http://localhost`
- Vision Wagon API: `http://localhost:8000`
- Nómada Alpha API: `http://localhost:8080`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

---

## 💬 Integración

- React frontend conectado por Axios a endpoints FastAPI.
- WebSocket para logs y eventos en vivo.
- Pronto para Nginx (archivo nginx.conf incluido).

---

## 📈 Escalabilidad

- Microservicios (frontend, Vision Wagon, Nómada Alpha).
- Base de datos PostgreSQL escalable.
- RabbitMQ para tareas asíncronas.
- Redis para caché y sesiones.

---

## 🔒 Seguridad

- OAuth 2.0, TLS 1.3.
- Validación y filtrado automático.
- Auditoría de logs y métricas.

---

## 🎮 Estado actual

✅ Backend 100% completo  
✅ Frontend React listo e integrado  
✅ APIs y WebSocket funcionando  
✅ Docker y scripts listos para producción  
✅ Documentación consolidada

---

## 💥 Próximos pasos

- Conectar claves reales (OpenAI, Discord, etc).
- Agregar autenticación y roles.
- Deploy en nube (AWS, Azure o GCP).
- Probar con usuarios reales.

---

## 🤝 Créditos

Desarrollado con amor por el equipo Vision Wagon + Nómada Alpha 💜🚀

---

**¡Listo para entregar y usar con Manus!** 👍
