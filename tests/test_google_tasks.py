import pytest
from utils.google_tasks import GoogleTasksManager

@pytest.fixture
async def tasks_manager():
    manager = GoogleTasksManager()
    await manager.authenticate()
    return manager

async def test_create_task(tasks_manager):
    task = await tasks_manager.create_task(
        title="Test Task",
        notes="Test Description"
    )
    assert task['title'] == "Test Task"
    assert task['notes'] == "Test Description" 