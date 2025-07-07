

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from vision_wagon.agents.core.base_agent import BaseAgent

class ConcreteAgent(BaseAgent):
    def __init__(self, agent_id: str, agent_type: str, config: dict = None):
        super().__init__(agent_id, agent_type, config)
        self.initialized = False
        self.processed_context = None
        self.cleaned_up = False

    async def initialize(self) -> bool:
        await asyncio.sleep(0.01) # Simulate async operation
        self.initialized = True
        return True

    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.01) # Simulate async operation
        self.processed_context = context
        return {"status": "processed", "data": context}

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        return "valid" in data and data["valid"]

    async def cleanup(self) -> None:
        await asyncio.sleep(0.01) # Simulate async operation
        self.cleaned_up = True

@pytest.mark.asyncio
async def test_base_agent_initialization():
    agent = ConcreteAgent("test_agent", "executive")
    assert agent.status == "inactive"
    assert not agent.initialized

    await agent.start()
    assert agent.status == "active"
    assert agent.initialized

@pytest.mark.asyncio
async def test_base_agent_process_success():
    agent = ConcreteAgent("test_agent", "executive")
    await agent.start()

    context = {"valid": True, "key": "value"}
    result = await agent.execute(context)

    assert result["status"] == "processed"
    assert agent.processed_context == context
    assert agent.execution_count == 1

@pytest.mark.asyncio
async def test_base_agent_process_validation_failure():
    agent = ConcreteAgent("test_agent", "executive")
    await agent.start()

    context = {"valid": False, "key": "value"}
    result = await agent.execute(context)

    assert result["status"] == "error"
    assert "Validación de entrada falló" in result["error"]
    assert agent.execution_count == 0 # Should not increment on validation failure

@pytest.mark.asyncio
async def test_base_agent_stop():
    agent = ConcreteAgent("test_agent", "executive")
    await agent.start()
    assert agent.status == "active"

    await agent.stop()
    assert agent.status == "inactive"
    assert agent.cleaned_up

@pytest.mark.asyncio
async def test_base_agent_log_action():
    agent = ConcreteAgent("test_agent", "executive")
    mock_logger = MagicMock()
    agent.logger = mock_logger

    await agent.log_action("test_action", {"data": "some_data"})
    mock_logger.info.assert_called_with("Acción test_action: {"data": "some_data"}")
    assert agent.last_activity is not None


