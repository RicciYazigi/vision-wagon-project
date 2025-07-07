import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Label } from '@/components/ui/label.jsx'
import { 
  Activity, 
  Users, 
  MessageSquare, 
  Shield, 
  Brain, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Settings,
  Eye,
  ThumbsUp,
  ThumbsDown,
  Send,
  Bot,
  Zap
} from 'lucide-react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const [moderationQueue, setModerationQueue] = useState([
    {
      id: 1,
      content: "¡Esta historia es increíble! Me encanta cómo se desarrolla el personaje principal.",
      author: "Usuario123",
      timestamp: "2025-01-04 14:30",
      status: "pending",
      flagged_categories: []
    },
    {
      id: 2,
      content: "No me gusta para nada esta dirección de la historia. Es muy aburrida.",
      author: "CriticoNarrativo",
      timestamp: "2025-01-04 14:25",
      status: "pending",
      flagged_categories: ["negativity"]
    },
    {
      id: 3,
      content: "¿Podríamos hacer que el protagonista sea más valiente en la próxima escena?",
      author: "FanDeAventura",
      timestamp: "2025-01-04 14:20",
      status: "pending",
      flagged_categories: []
    }
  ])

  const [coachingProfiles, setCoachingProfiles] = useState([
    {
      id: "avatar_001",
      name: "Elena - Narradora Principal",
      traits: ["empática", "creativa", "detallista"],
      tone: "cálido y acogedor",
      lastUpdated: "2025-01-04 13:45"
    },
    {
      id: "avatar_002", 
      name: "Marcus - Personaje Aventurero",
      traits: ["valiente", "impulsivo", "leal"],
      tone: "enérgico y decidido",
      lastUpdated: "2025-01-04 12:30"
    }
  ])

  const [newGuidelines, setNewGuidelines] = useState({
    avatar_id: "",
    add_traits: "",
    remove_traits: "",
    set_tone: ""
  })

  const [systemMetrics, setSystemMetrics] = useState({
    totalComments: 1247,
    moderatedToday: 89,
    flaggedContent: 12,
    activeAvatars: 5,
    coachingSessions: 23
  })

  const handleModeration = (commentId, action) => {
    setModerationQueue(prev => 
      prev.map(comment => 
        comment.id === commentId 
          ? { ...comment, status: action }
          : comment
      )
    )
  }

  const handleCoaching = () => {
    if (!newGuidelines.avatar_id) return

    const guidelines = {
      add_traits: newGuidelines.add_traits.split(',').map(t => t.trim()).filter(t => t),
      remove_traits: newGuidelines.remove_traits.split(',').map(t => t.trim()).filter(t => t),
      set_tone: newGuidelines.set_tone || undefined
    }

    // Simular llamada al CoachingAgent
    console.log('Enviando directrices de coaching:', {
      avatar_id: newGuidelines.avatar_id,
      guidelines
    })

    // Actualizar perfil localmente para demo
    setCoachingProfiles(prev => 
      prev.map(profile => 
        profile.id === newGuidelines.avatar_id
          ? {
              ...profile,
              traits: [
                ...profile.traits.filter(t => !guidelines.remove_traits.includes(t)),
                ...guidelines.add_traits
              ],
              tone: guidelines.set_tone || profile.tone,
              lastUpdated: new Date().toLocaleString('es-ES')
            }
          : profile
      )
    )

    // Limpiar formulario
    setNewGuidelines({
      avatar_id: "",
      add_traits: "",
      remove_traits: "",
      set_tone: ""
    })
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Nómada Alpha Dashboard
          </h1>
          <p className="text-muted-foreground">
            Sistema integrado de moderación de contenido y coaching de avatares IA
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="moderation">Moderación</TabsTrigger>
            <TabsTrigger value="coaching">Coaching IA</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Comentarios Totales</CardTitle>
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemMetrics.totalComments}</div>
                  <p className="text-xs text-muted-foreground">+12% desde ayer</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Moderados Hoy</CardTitle>
                  <Shield className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemMetrics.moderatedToday}</div>
                  <p className="text-xs text-muted-foreground">+5% desde ayer</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Contenido Flagged</CardTitle>
                  <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemMetrics.flaggedContent}</div>
                  <p className="text-xs text-muted-foreground">-2% desde ayer</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Avatares Activos</CardTitle>
                  <Bot className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemMetrics.activeAvatars}</div>
                  <p className="text-xs text-muted-foreground">Todos operativos</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Sesiones Coaching</CardTitle>
                  <Brain className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemMetrics.coachingSessions}</div>
                  <p className="text-xs text-muted-foreground">+8% desde ayer</p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Estado del Sistema</CardTitle>
                  <CardDescription>Monitoreo en tiempo real</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">ModerationAgent</span>
                    <Badge variant="default" className="bg-green-500">Activo</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">CoachingAgent</span>
                    <Badge variant="default" className="bg-green-500">Activo</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">NarrativeArchitect</span>
                    <Badge variant="default" className="bg-green-500">Activo</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">AssemblyAgent</span>
                    <Badge variant="default" className="bg-green-500">Activo</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Actividad Reciente</CardTitle>
                  <CardDescription>Últimas acciones del sistema</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <Shield className="h-4 w-4 text-blue-500" />
                    <span className="text-sm">Comentario moderado automáticamente</span>
                    <span className="text-xs text-muted-foreground">hace 2 min</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Brain className="h-4 w-4 text-purple-500" />
                    <span className="text-sm">Perfil de Elena actualizado</span>
                    <span className="text-xs text-muted-foreground">hace 5 min</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <MessageSquare className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Nueva narrativa generada</span>
                    <span className="text-xs text-muted-foreground">hace 8 min</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Zap className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm">Sistema optimizado automáticamente</span>
                    <span className="text-xs text-muted-foreground">hace 15 min</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="moderation" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Cola de Moderación
                </CardTitle>
                <CardDescription>
                  Comentarios pendientes de revisión por el ModerationAgent
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {moderationQueue.filter(comment => comment.status === 'pending').map(comment => (
                  <div key={comment.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="text-sm font-medium">{comment.author}</p>
                        <p className="text-xs text-muted-foreground">{comment.timestamp}</p>
                      </div>
                      {comment.flagged_categories.length > 0 && (
                        <div className="flex gap-1">
                          {comment.flagged_categories.map(category => (
                            <Badge key={category} variant="destructive" className="text-xs">
                              {category}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <p className="text-sm bg-muted p-3 rounded">{comment.content}</p>
                    
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        variant="default"
                        onClick={() => handleModeration(comment.id, 'approved')}
                        className="flex items-center gap-1"
                      >
                        <CheckCircle className="h-4 w-4" />
                        Aprobar
                      </Button>
                      <Button 
                        size="sm" 
                        variant="destructive"
                        onClick={() => handleModeration(comment.id, 'rejected')}
                        className="flex items-center gap-1"
                      >
                        <XCircle className="h-4 w-4" />
                        Rechazar
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => handleModeration(comment.id, 'flagged')}
                        className="flex items-center gap-1"
                      >
                        <AlertTriangle className="h-4 w-4" />
                        Marcar
                      </Button>
                    </div>
                  </div>
                ))}
                
                {moderationQueue.filter(comment => comment.status === 'pending').length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No hay comentarios pendientes de moderación</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Historial de Moderación</CardTitle>
                <CardDescription>Últimas decisiones del sistema</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {moderationQueue.filter(comment => comment.status !== 'pending').map(comment => (
                    <div key={comment.id} className="flex items-center justify-between p-3 border rounded">
                      <div>
                        <p className="text-sm font-medium">{comment.author}</p>
                        <p className="text-xs text-muted-foreground truncate max-w-md">
                          {comment.content}
                        </p>
                      </div>
                      <Badge 
                        variant={comment.status === 'approved' ? 'default' : 'destructive'}
                      >
                        {comment.status === 'approved' ? 'Aprobado' : 
                         comment.status === 'rejected' ? 'Rechazado' : 'Marcado'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="coaching" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    Perfiles de Avatares
                  </CardTitle>
                  <CardDescription>
                    Estado actual de los avatares IA
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {coachingProfiles.map(profile => (
                    <div key={profile.id} className="border rounded-lg p-4 space-y-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-medium">{profile.name}</h4>
                          <p className="text-xs text-muted-foreground">
                            Actualizado: {profile.lastUpdated}
                          </p>
                        </div>
                        <Badge variant="outline">{profile.id}</Badge>
                      </div>
                      
                      <div>
                        <p className="text-sm font-medium mb-1">Rasgos:</p>
                        <div className="flex flex-wrap gap-1">
                          {profile.traits.map(trait => (
                            <Badge key={trait} variant="secondary" className="text-xs">
                              {trait}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <p className="text-sm font-medium mb-1">Tono:</p>
                        <p className="text-sm text-muted-foreground">{profile.tone}</p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    Panel de Coaching
                  </CardTitle>
                  <CardDescription>
                    Aplicar nuevas directrices a los avatares
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="avatar-select">Avatar</Label>
                    <select 
                      id="avatar-select"
                      className="w-full p-2 border rounded-md bg-background"
                      value={newGuidelines.avatar_id}
                      onChange={(e) => setNewGuidelines(prev => ({...prev, avatar_id: e.target.value}))}
                    >
                      <option value="">Seleccionar avatar...</option>
                      {coachingProfiles.map(profile => (
                        <option key={profile.id} value={profile.id}>
                          {profile.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="add-traits">Añadir Rasgos (separados por comas)</Label>
                    <Input
                      id="add-traits"
                      placeholder="ej: valiente, optimista, carismático"
                      value={newGuidelines.add_traits}
                      onChange={(e) => setNewGuidelines(prev => ({...prev, add_traits: e.target.value}))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="remove-traits">Remover Rasgos (separados por comas)</Label>
                    <Input
                      id="remove-traits"
                      placeholder="ej: tímido, pesimista"
                      value={newGuidelines.remove_traits}
                      onChange={(e) => setNewGuidelines(prev => ({...prev, remove_traits: e.target.value}))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="set-tone">Establecer Tono</Label>
                    <Input
                      id="set-tone"
                      placeholder="ej: enérgico y motivador"
                      value={newGuidelines.set_tone}
                      onChange={(e) => setNewGuidelines(prev => ({...prev, set_tone: e.target.value}))}
                    />
                  </div>

                  <Button 
                    onClick={handleCoaching}
                    disabled={!newGuidelines.avatar_id}
                    className="w-full flex items-center gap-2"
                  >
                    <Send className="h-4 w-4" />
                    Aplicar Directrices
                  </Button>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Historial de Coaching</CardTitle>
                <CardDescription>Últimas sesiones de entrenamiento</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="text-sm font-medium">Elena - Narradora Principal</p>
                      <p className="text-xs text-muted-foreground">
                        Añadidos: empática, detallista | Tono: más cálido
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground">hace 15 min</span>
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="text-sm font-medium">Marcus - Personaje Aventurero</p>
                      <p className="text-xs text-muted-foreground">
                        Removidos: imprudente | Añadidos: estratégico
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground">hace 1 hora</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Tasa de Aprobación</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">94.2%</div>
                  <p className="text-xs text-muted-foreground">+2.1% desde la semana pasada</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Tiempo Promedio</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">1.3s</div>
                  <p className="text-xs text-muted-foreground">Moderación automática</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Sesiones de Coaching</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">156</div>
                  <p className="text-xs text-muted-foreground">Esta semana</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Satisfacción</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">4.8/5</div>
                  <p className="text-xs text-muted-foreground">Calificación de usuarios</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Tendencias del Sistema</CardTitle>
                <CardDescription>Rendimiento de los últimos 7 días</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Gráficos de tendencias disponibles próximamente</p>
                    <p className="text-sm">Integración con Recharts en desarrollo</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App

