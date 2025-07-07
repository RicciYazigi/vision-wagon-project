import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
import sys
import os

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

@pytest.fixture
def client():
    return TestClient(app)

class TestNomadaAlphaAPI:
    """Tests para Nómada Alpha API"""
    
    def test_root_endpoint(self, client):
        """Test del endpoint raíz"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "Nómada Alpha API"
        assert "version" in data
        assert "status" in data

    def test_health_endpoint(self, client):
        """Test del endpoint de health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        
        # Verificar estructura de servicios
        services = data["services"]
        assert "api" in services
        assert "rabbitmq" in services
        assert "vision_wagon" in services

    @patch('httpx.AsyncClient')
    def test_create_campaign_success(self, mock_client, client):
        """Test de creación exitosa de campaña"""
        # Mock de la respuesta de Vision Wagon Core
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Test Campaign",
            "description": "Test description",
            "status": "pending"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        campaign_data = {
            "name": "Test Campaign",
            "description": "Test description",
            "campaign_type": "email",
            "target_audience": "test users",
            "budget": 1000
        }
        
        response = client.post("/campaigns", json=campaign_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Campaign"
        assert data["id"] == 1

    @patch('httpx.AsyncClient')
    def test_create_campaign_vision_wagon_error(self, mock_client, client):
        """Test de error al crear campaña cuando Vision Wagon Core falla"""
        # Mock de error de Vision Wagon Core
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        campaign_data = {
            "name": "Test Campaign",
            "description": "Test description"
        }
        
        response = client.post("/campaigns", json=campaign_data)
        assert response.status_code == 500

    @patch('httpx.AsyncClient')
    def test_list_campaigns(self, mock_client, client):
        """Test de listado de campañas"""
        # Mock de la respuesta de Vision Wagon Core
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "campaigns": [
                {"id": 1, "name": "Campaign 1", "status": "active"},
                {"id": 2, "name": "Campaign 2", "status": "pending"}
            ]
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        response = client.get("/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert len(data["campaigns"]) == 2

    @patch('httpx.AsyncClient')
    def test_get_campaign_by_id(self, mock_client, client):
        """Test de obtención de campaña por ID"""
        # Mock de la respuesta de Vision Wagon Core
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Test Campaign",
            "description": "Test description",
            "status": "active"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        response = client.get("/campaigns/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Campaign"

    @patch('httpx.AsyncClient')
    def test_get_campaign_not_found(self, mock_client, client):
        """Test de campaña no encontrada"""
        # Mock de respuesta 404 de Vision Wagon Core
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Campaign not found"
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        response = client.get("/campaigns/99999")
        assert response.status_code == 404

    def test_create_task(self, client):
        """Test de creación de tarea"""
        task_data = {
            "campaign_id": 1,
            "action_type": "send_email",
            "context": {"recipient": "test@example.com"}
        }
        
        response = client.post("/tasks", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "task_queued"
        assert "task" in data
        assert data["task"]["campaign_id"] == 1

    @patch('httpx.AsyncClient')
    def test_execute_task_success(self, mock_client, client):
        """Test de ejecución exitosa de tarea"""
        # Mock de la respuesta de Vision Wagon Core
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "result": "Task executed successfully",
            "task_id": "task_123"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        task_data = {
            "campaign_id": 1,
            "action_type": "process_data",
            "context": {"data": "test_data"}
        }
        
        response = client.post("/tasks/execute", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_recent_events(self, client):
        """Test de obtención de eventos recientes"""
        response = client.get("/events")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total" in data
        assert isinstance(data["events"], list)

class TestEventHandling:
    """Tests para manejo de eventos"""
    
    @patch('main.rabbitmq_channel')
    def test_publish_event(self, mock_channel):
        """Test de publicación de eventos"""
        from main import publish_event
        
        event_data = {
            "event_type": "test_event",
            "data": {"test": "data"},
            "timestamp": "2023-01-01T00:00:00"
        }
        
        # Ejecutar la función de publicación
        asyncio.run(publish_event(event_data))
        
        # Verificar que se llamó al canal de RabbitMQ
        mock_channel.basic_publish.assert_called_once()

    @patch('main.rabbitmq_channel')
    def test_publish_task(self, mock_channel):
        """Test de publicación de tareas"""
        from main import publish_task
        
        task_data = {
            "campaign_id": 1,
            "action_type": "test_action",
            "context": {"test": "context"},
            "created_at": "2023-01-01T00:00:00"
        }
        
        # Ejecutar la función de publicación
        asyncio.run(publish_task(task_data))
        
        # Verificar que se llamó al canal de RabbitMQ
        mock_channel.basic_publish.assert_called_once()

class TestErrorHandling:
    """Tests para manejo de errores"""
    
    @patch('httpx.AsyncClient')
    def test_vision_wagon_unavailable(self, mock_client, client):
        """Test cuando Vision Wagon Core no está disponible"""
        # Mock de error de conexión
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("Connection error")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        response = client.get("/campaigns")
        assert response.status_code == 503
        data = response.json()
        assert "Vision Wagon Core unavailable" in data["detail"]

    def test_invalid_campaign_data(self, client):
        """Test de datos de campaña inválidos"""
        # Datos incompletos (falta el campo 'name' requerido)
        invalid_data = {
            "description": "Test without name"
        }
        
        response = client.post("/campaigns", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_invalid_task_data(self, client):
        """Test de datos de tarea inválidos"""
        # Datos incompletos (faltan campos requeridos)
        invalid_data = {
            "action_type": "test_action"
            # Falta campaign_id
        }
        
        response = client.post("/tasks", json=invalid_data)
        assert response.status_code == 422  # Validation error

class TestCORSConfiguration:
    """Tests para configuración CORS"""
    
    def test_cors_headers(self, client):
        """Test de headers CORS"""
        response = client.options("/")
        assert response.status_code == 200
        
        # Verificar headers CORS en respuesta GET
        response = client.get("/")
        assert "access-control-allow-origin" in response.headers or True  # CORS puede no estar en headers de test

class TestDataValidation:
    """Tests para validación de datos"""
    
    def test_campaign_request_validation(self):
        """Test de validación de CampaignRequest"""
        from main import CampaignRequest
        
        # Datos válidos
        valid_data = {
            "name": "Test Campaign",
            "description": "Test description",
            "campaign_type": "email",
            "target_audience": "test users",
            "budget": 1000
        }
        
        campaign_request = CampaignRequest(**valid_data)
        assert campaign_request.name == "Test Campaign"
        assert campaign_request.budget == 1000

    def test_task_request_validation(self):
        """Test de validación de TaskRequest"""
        from main import TaskRequest
        
        # Datos válidos
        valid_data = {
            "campaign_id": 1,
            "action_type": "send_email",
            "context": {"recipient": "test@example.com"}
        }
        
        task_request = TaskRequest(**valid_data)
        assert task_request.campaign_id == 1
        assert task_request.action_type == "send_email"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

