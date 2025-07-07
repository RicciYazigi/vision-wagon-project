# Nómada Alpha Dashboard - Vision Wagon

## Descripción

Dashboard web interactivo desarrollado en React que integra las funcionalidades de **Vision Wagon** y **Nómada Alpha**, proporcionando una interfaz completa para la gestión de agentes de IA y la colaboración en narrativas interactivas.

## Características Principales

### 🎯 **Vision Wagon - Gestión de Agentes**
- **Dashboard Overview**: Métricas en tiempo real de decisiones, agentes activos, eficiencia global y narrativas generadas
- **Logs en Vivo**: Monitoreo en tiempo real del sistema con capacidad de pausar/reanudar
- **Gestión de Agentes**: Visualización detallada del estado, rendimiento y especialidades de cada agente
- **Analytics Avanzado**: KPIs detallados y visualizaciones de tendencias

### 🌟 **Nómada Alpha - Narrativas Colaborativas**
- **Generador de Narrativas**: Creación de historias interactivas con prompts personalizables
- **Votación Comunitaria**: Sistema de votación democrática para aprobar narrativas
- **Comentarios en Tiempo Real**: Interacción comunitaria con sistema de comentarios
- **Métricas de Participación**: Seguimiento de narrativas aprobadas, participación y consenso

## Tecnologías Utilizadas

- **React 18** - Framework principal
- **Vite** - Build tool y servidor de desarrollo
- **Lucide React** - Iconografía moderna
- **Tailwind CSS** - Estilos y diseño responsivo
- **JavaScript ES6+** - Lógica de aplicación

## Estructura del Proyecto

```
nomada-dashboard/
├── src/
│   ├── App.jsx          # Componente principal del dashboard
│   ├── App.css          # Estilos personalizados
│   ├── main.jsx         # Punto de entrada de React
│   ├── index.css        # Estilos globales
│   └── services/
│       └── api.js       # Servicios de API (preparado para integración)
├── public/              # Archivos estáticos
├── index.html           # Template HTML
├── package.json         # Dependencias y scripts
└── README.md           # Esta documentación
```

## Instalación y Uso

### Prerrequisitos
- Node.js 18+ 
- npm o yarn

### Instalación
```bash
# Clonar o acceder al directorio del proyecto
cd nomada-dashboard

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

### Acceso
- **URL Local**: http://localhost:5173
- **Dashboard**: Navegación por pestañas (Overview, Agentes, Nómada Alpha, Analytics)

## Funcionalidades Implementadas

### ✅ **Completamente Funcional**

#### **Overview Dashboard**
- Métricas en tiempo real con tendencias
- Logs del sistema con scroll automático
- Barras de progreso de rendimiento de agentes
- Controles de pausa/reanudación

#### **Gestión de Agentes**
- Cards individuales por agente
- Estados visuales (activo, inactivo, offline)
- Métricas de rendimiento
- Información de especialidades

#### **Nómada Alpha**
- Generador de narrativas con prompts personalizables
- Simulación de generación con loading states
- Sistema de votación con botones interactivos
- Resultados de votación en tiempo real
- Sistema de comentarios funcional
- Métricas de participación comunitaria

#### **Analytics**
- KPIs principales con tendencias
- Placeholders para gráficos avanzados
- Métricas de usuarios y conversiones

### 🔄 **Interactividad**
- Navegación fluida entre pestañas
- Estados de loading realistas
- Feedback visual inmediato
- Responsive design para móviles y desktop

## Integración con Backend

El dashboard está preparado para integrarse con los servicios de backend:

### **Vision Wagon API**
- Endpoints para métricas de agentes
- Logs en tiempo real via WebSocket
- Gestión de estados de agentes

### **Nómada Alpha API**
- Generación de narrativas via LLM
- Sistema de votación persistente
- Gestión de comentarios y participación

### **Archivo de Servicios**
```javascript
// src/services/api.js - Preparado para integración
const apiService = {
  // Vision Wagon endpoints
  getAgentMetrics: () => fetch('/api/vision-wagon/metrics'),
  getAgentLogs: () => fetch('/api/vision-wagon/logs'),
  
  // Nómada Alpha endpoints
  generateNarrative: (prompt) => fetch('/api/nomada-alpha/generate', {
    method: 'POST',
    body: JSON.stringify({ prompt })
  }),
  
  submitVote: (narrativeId, vote) => fetch('/api/nomada-alpha/vote', {
    method: 'POST', 
    body: JSON.stringify({ narrativeId, vote })
  })
};
```

## Despliegue

### **Desarrollo**
```bash
npm run dev
```

### **Producción**
```bash
# Build para producción
npm run build

# Preview del build
npm run preview
```

### **Docker** (Opcional)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview", "--", "--host"]
```

## Características Técnicas

### **Rendimiento**
- Componentes optimizados con React hooks
- Lazy loading de datos
- Debouncing en inputs
- Memoización de componentes pesados

### **UX/UI**
- Diseño moderno con Tailwind CSS
- Iconografía consistente con Lucide
- Estados de loading y error
- Feedback visual inmediato
- Responsive design completo

### **Escalabilidad**
- Arquitectura modular por componentes
- Servicios de API centralizados
- Estado global preparado para Redux/Zustand
- Estructura preparada para testing

## Próximos Pasos

1. **Integración Backend**: Conectar con APIs reales de Vision Wagon y Nómada Alpha
2. **Autenticación**: Implementar sistema de login y roles
3. **WebSockets**: Conexión en tiempo real para logs y votaciones
4. **Testing**: Unit tests y E2E tests
5. **PWA**: Convertir en Progressive Web App
6. **Gráficos**: Implementar Chart.js o D3.js para analytics avanzados

## Soporte

Para soporte técnico o preguntas sobre la implementación, consultar la documentación del proyecto principal o contactar al equipo de desarrollo.

---

**Desarrollado como parte del ecosistema Vision Wagon + Nómada Alpha**

