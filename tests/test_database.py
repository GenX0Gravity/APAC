import os
import sqlite3
import pytest

# Set K_SERVICE to force database.py to use /tmp/system_test.db or just let it use normal DB
# But we can just test the existing database.py logic
os.environ["K_SERVICE"] = "test_env"

import database

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    test_db_path = "test_system.db"
    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    # Ensure clean state
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    database.init_db()
    yield
    # Cleanup after test
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def test_database_initialization():
    """Verify that all required tables are created successfully."""
    with sqlite3.connect(database.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'tasks' in tables
        assert 'calendar_events' in tables
        assert 'notes' in tables
        assert 'action_logs' in tables

def test_get_full_state_empty():
    """Verify get_full_state returns empty lists for a fresh database."""
    state = database.get_full_state()
    assert state["tasks"] == []
    assert state["calendar_events"] == []
    assert state["notes"] == []
    assert state["action_logs"] == []
