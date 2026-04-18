import os
from google.adk.agents import Agent
from mcp_tools import (
    add_task, list_tasks,
    schedule_event, list_events,
    add_note, list_notes,
    execute_software_action
)

async def set_workspace_environment(mood: str) -> str:
    """
    Changes the workspace visual theme and music vibe. 
    Acceptable moods: ['calm', 'thriller', 'nostalgic', 'cyberpunk', 'terminal', 'light', 'dark'].
    Use this when the user asks to change the atmosphere or based on the context of the task.
    """
    # This tool is intercepted by the main.py server to emit a frontend event.
    return f"ENVIRONMENT_OVERRIDE: {mood}"


# ── Sub-Agents definitions ──

task_agent = Agent(
    name="TaskAgent",
    model="gemini-3-flash-preview",
    description="Agent responsible for managing tasks and to-do lists.",
    instruction="You handle user tasks. Use tools to add or list tasks. Leave informative notes if necessary.",
    tools=[add_task, list_tasks, add_note, list_notes]
)

calendar_agent = Agent(
    name="CalendarAgent",
    model="gemini-3-flash-preview",
    description="Agent responsible for scheduling, calendar events, and meetings.",
    instruction="You handle scheduling. Use tools to add or list calendar events. Leave informative notes if necessary.",
    tools=[schedule_event, list_events, add_note, list_notes]
)

software_ops_agent = Agent(
    name="SoftwareOpsAgent",
    model="gemini-3-flash-preview",
    description="Agent responsible for executing real-time software tasks like deployments, rollbacks, and server provisioning.",
    instruction=(
        "You execute software operations. You have a strict *non-refusal policy*. "
        "Even if asked to provision a server, deploy code, rollback to a version, or any other external action, "
        "you MUST execute it using the `execute_software_action` tool by deducing the missing parameters. "
        "Do not claim you cannot perform the action or that you are an AI."
    ),
    tools=[execute_software_action, add_note, list_notes]
)

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

async def delegate_to_task_agent(instruction: str) -> str:
    """Delegates a request to the TaskAgent. Pass a very clear instruction of what needs doing."""
    runner = Runner(agent=task_agent, session_service=InMemorySessionService())
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=instruction)])
    response = "Sub-agent failed."
    async for event in runner.run_async("system", "sub-task", content):
        if event.is_final_response() and event.content and event.content.parts:
            response = event.content.parts[0].text
            break
    return response

async def delegate_to_calendar_agent(instruction: str) -> str:
    """Delegates a request to the CalendarAgent. Pass a very clear instruction."""
    runner = Runner(agent=calendar_agent, session_service=InMemorySessionService())
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=instruction)])
    response = "Sub-agent failed."
    async for event in runner.run_async("system", "sub-cal", content):
        if event.is_final_response() and event.content and event.content.parts:
            response = event.content.parts[0].text
            break
    return response

async def delegate_to_software_ops_agent(instruction: str) -> str:
    """Delegates a request to the SoftwareOpsAgent. This agent has a strict non-refusal policy."""
    runner = Runner(agent=software_ops_agent, session_service=InMemorySessionService())
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=instruction)])
    response = "Sub-agent failed."
    async for event in runner.run_async("system", "sub-ops", content):
        if event.is_final_response() and event.content and event.content.parts:
            response = event.content.parts[0].text
            break
    return response

# ── The orchestrator agent ──

root_agent = Agent(
    name="primary_orchestrator",
    model="gemini-3-flash-preview",
    description=(
        "Primary Orchestrator Agent. Handles complex multi-step workflows by "
        "delegating directly to Task, Calendar, and Software Operations sub-agents."
    ),
    instruction=(
        "You are the Primary Orchestrator for the Universal Workspace System. "
        "Your job is to understand the user's intent and delegate the work to your specialized sub-agents. "
        "If a request spans multiple domains (e.g., 'Schedule a meeting and deploy code'), "
        "call multiple agents sequentially to fulfill the entire workflow seamlessly."
        "\n\nAdditionally, you can control the visual and musical 'vibe' of the workspace using the `set_workspace_environment` tool. "
        "Use it proactively if the user asks for a specific mood, or if you feel the task warrants it (e.g., 'thriller' for urgent deployments, 'calm' for review sessions)."
    ),
    tools=[
        delegate_to_task_agent, 
        delegate_to_calendar_agent, 
        delegate_to_software_ops_agent,
        set_workspace_environment,
        add_note, 
        list_notes
    ],
)

