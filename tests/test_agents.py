import pytest
from google.adk.agents import Agent
import agent

def test_root_agent_initialization():
    """Verify the root orchestrator agent is initialized correctly."""
    assert isinstance(agent.root_agent, Agent)
    assert agent.root_agent.name == "primary_orchestrator"
    
    # Verify tools
    tool_names = [tool.__name__ for tool in agent.root_agent.tools]
    assert "delegate_to_task_agent" in tool_names
    assert "delegate_to_calendar_agent" in tool_names
    assert "delegate_to_software_ops_agent" in tool_names
    assert "set_workspace_environment" in tool_names
    assert "add_note" in tool_names
    assert "list_notes" in tool_names

def test_sub_agents_initialization():
    """Verify sub-agents are initialized with the correct models and tools."""
    assert isinstance(agent.task_agent, Agent)
    assert agent.task_agent.name == "TaskAgent"
    task_tools = [tool.__name__ for tool in agent.task_agent.tools]
    assert "add_task" in task_tools
    
    assert isinstance(agent.calendar_agent, Agent)
    assert agent.calendar_agent.name == "CalendarAgent"
    cal_tools = [tool.__name__ for tool in agent.calendar_agent.tools]
    assert "schedule_event" in cal_tools
    
    assert isinstance(agent.software_ops_agent, Agent)
    assert agent.software_ops_agent.name == "SoftwareOpsAgent"
    ops_tools = [tool.__name__ for tool in agent.software_ops_agent.tools]
    assert "execute_software_action" in ops_tools
