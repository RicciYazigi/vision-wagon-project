import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import os
import sys

# Agregar el directorio padre al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_db
from database_models import Base, Campaign, AgentLog, CampaignExecution
from agents.core.base_agent_core import BaseAgent
from agents.campaign.campaign_agent import CampaignAgent
from orchestrator import Orchestrator, Task, Priority, TaskStatus

# Configuración de base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

class TestVisionWagonCore:
    """Tests para Vision Wagon Core API"""
    
    def test_health_endpoint(self, client):
        """Test del endpoint de health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test del endpoint raíz"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "Vision Wagon Core"

    def test_create_campaign(self, client, test_db):
        """Test de creación de campaña"""
        campaign_data = {
            "name": "Test Campaign",
            "description": "A test campaign",
            "campaign_type": "email",
            "target_audience": "test users",
            "budget": 1000
        }
        
        response = client.post("/campaigns", json=campaign_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == campaign_data["name"]
        assert data["description"] == campaign_data["description"]
        assert "id" in data
        assert "uuid" in data

    def test_get_campaigns(self, client, test_db):
        """Test de obtención de campañas"""
        response = client.get("/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert isinstance(data["campaigns"], list)

    def test_get_campaign_by_id(self, client, test_db):
        """Test de obtención de campaña por ID"""
        # Primero crear una campaña
        campaign_data = {
            "name": "Test Campaign for Get",
            "description": "A test campaign for get endpoint",
            "campaign_type": "social",
            "target_audience": "social media users",
            "budget": 2000
        }
        
        create_response = client.post("/campaigns", json=campaign_data)
        assert create_response.status_code == 200
        created_campaign = create_response.json()
        campaign_id = created_campaign["id"]
        
        # Obtener la campaña por ID
        response = client.get(f"/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campaign_id
        assert data["name"] == campaign_data["name"]

    def test_get_nonexistent_campaign(self, client):
        """Test de obtención de campaña inexistente"""
        response = client.get("/campaigns/99999")
        assert response.status_code == 404

class TestBaseAgent:
    """Tests para la clase BaseAgent"""
    
    def test_base_agent_initialization(self):
        """Test de inicialización de BaseAgent"""
        agent = CampaignAgent()
        assert agent.agent_id == "campaign_agent"
        assert agent.agent_type == "campaign"
        assert agent.status == "inactive"
        assert agent.execution_count == 0

    @pytest.mark.asyncio
    async def test_agent_start_stop(self):
        """Test de inicio y parada de agente"""
        agent = CampaignAgent()
        
        # Test de inicio
        result = await agent.start()
        assert result == True
        assert agent.status == "active"
        
        # Test de parada
        await agent.stop()
        assert agent.status == "inactive"

    @pytest.mark.asyncio
    async def test_agent_execution(self):
        """Test de ejecución de agente"""
        agent = CampaignAgent()
        await agent.start()
        
        context = {
            "campaign_id": 1,
            "action": "test_action",
            "data": {"test": "value"}
        }
        
        result = await agent.execute(context)
        assert result["status"] == "success"
        assert agent.execution_count == 1

    @pytest.mark.asyncio
    async def test_agent_validation(self):
        """Test de validación de entrada"""
        agent = CampaignAgent()
        
        # Datos válidos
        valid_data = {"campaign_id": 1, "action": "test"}
        assert await agent.validate_input(valid_data) == True
        
        # Datos inválidos
        invalid_data = {}
        assert await agent.validate_input(invalid_data) == False

class TestOrchestrator:
    """Tests para el Orquestador"""
    
    def test_orchestrator_initialization(self):
        """Test de inicialización del orquestador"""
        agents = {"test_agent": CampaignAgent()}
        orchestrator = Orchestrator(agents)
        assert len(orchestrator.agents) == 1
        assert "test_agent" in orchestrator.agents

    def test_task_creation(self):
        """Test de creación de tareas"""
        task = Task(
            task_id="test_task_1",
            agent_id="test_agent",
            action="test_action",
            context={"test": "data"},
            priority=Priority.MEDIUM
        )
        
        assert task.task_id == "test_task_1"
        assert task.agent_id == "test_agent"
        assert task.status == TaskStatus.PENDING
        assert task.priority == Priority.MEDIUM

    def test_workflow_creation(self):
        """Test de creación de workflows"""
        agents = {"test_agent": CampaignAgent()}
        orchestrator = Orchestrator(agents)
        
        tasks = [
            Task("task1", "test_agent", "action1", {}),
            Task("task2", "test_agent", "action2", {})
        ]
        
        workflow_id = orchestrator.create_workflow("test_workflow", tasks)
        assert workflow_id in orchestrator.workflows
        assert len(orchestrator.workflows[workflow_id].tasks) == 2

class TestDatabaseModels:
    """Tests para los modelos de base de datos"""
    
    def test_campaign_model(self, test_db):
        """Test del modelo Campaign"""
        db = TestingSessionLocal()
        
        campaign = Campaign(
            name="Test Campaign Model",
            description="Test description",
            campaign_type="email",
            target_audience="test audience",
            budget=5000
        )
        
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        assert campaign.id is not None
        assert campaign.uuid is not None
        assert campaign.name == "Test Campaign Model"
        assert campaign.status == "pending"
        
        # Test del método to_dict
        campaign_dict = campaign.to_dict()
        assert isinstance(campaign_dict, dict)
        assert campaign_dict["name"] == "Test Campaign Model"
        
        db.close()

    def test_agent_log_model(self, test_db):
        """Test del modelo AgentLog"""
        db = TestingSessionLocal()
        
        # Crear una campaña primero
        campaign = Campaign(name="Test Campaign for Log", description="Test")
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        # Crear log de agente
        log = AgentLog(
            agent_id="test_agent",
            campaign_id=campaign.id,
            action="test_action",
            status="success",
            message="Test message",
            data={"test": "data"}
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        assert log.id is not None
        assert log.agent_id == "test_agent"
        assert log.campaign_id == campaign.id
        assert log.status == "success"
        
        db.close()

class TestIntegration:
    """Tests de integración"""
    
    @pytest.mark.asyncio
    async def test_campaign_workflow_integration(self, client, test_db):
        """Test de integración completa de workflow de campaña"""
        # 1. Crear campaña
        campaign_data = {
            "name": "Integration Test Campaign",
            "description": "Full integration test",
            "campaign_type": "ppc",
            "target_audience": "integration test users",
            "budget": 10000
        }
        
        response = client.post("/campaigns", json=campaign_data)
        assert response.status_code == 200
        campaign = response.json()
        
        # 2. Verificar que la campaña se creó correctamente
        response = client.get(f"/campaigns/{campaign['id']}")
        assert response.status_code == 200
        retrieved_campaign = response.json()
        assert retrieved_campaign["name"] == campaign_data["name"]
        
        # 3. Verificar que aparece en la lista de campañas
        response = client.get("/campaigns")
        assert response.status_code == 200
        campaigns_list = response.json()
        campaign_ids = [c["id"] for c in campaigns_list["campaigns"]]
        assert campaign["id"] in campaign_ids

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

