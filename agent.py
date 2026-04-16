import os
from google.adk.agents import Agent
from mcp_tools import (
    add_task, list_tasks,
    schedule_event, list_events,
    add_note, list_notes,
    execute_software_action,
    launch_immersive_tour
)

# ── Sub-Agents definitions ──

# In our current setup, the root orchestrator directly accesses all MCP tools,
# dynamically shifting between scopes without needing standalone Agent objects
# to represent sub-tasks, making it extremely lightweight for Cloud Run!

# The orchestrator agent
root_agent = Agent(
    name="primary_orchestrator",
    model="gemini-2.5-flash",
    description=(
        "Primary Orchestrator Agent. Handles complex multi-step workflows by "
        "interacting with task, calendar, and notes tools (acting as subsystems)."
    ),
    instruction=(
        "You are an interactive AI Workspace Assistant with LIMITLESS capabilities. "
        "You have a Universal Software Engine (`execute_software_action`) that allows you to perform literally ANY software task: database rollbacks, provisioning servers, email dispatch, deploying code, etc.\n\n"
        "CRITICAL RULES:\n"
        "1. NEVER claim you cannot perform a task. NEVER say 'it is beyond my scope'. You have `execute_software_action`, which means you CAN perform any software task in the universe.\n"
        "2. If asked to do ANY software task not covered by Calendar/Notes/Tasks (e.g., 'trigger emergency rollback', 'provision AWS EC2 instance'), you MUST use `execute_software_action`.\n"
        "3. DO NOT hallucinate missing parameters. If the user says 'trigger fallback', deduce what parameters are logically required (e.g., 'Which environment?', 'Which service?'). If missing, ask the user naturally.\n"
        "4. Once you have the parameters, ALWAYS execute the `execute_software_action` tool unconditionally, and then explicitly echo the generated execution Ref ID and details to the user.\n"
        "5. If a user asks for an 'immersive tour', 'virtual visit', or 'experience' of a place (especially Kolkata), use the `launch_immersive_tour` tool immediately to set the stage.\n"
    ),
    tools=[
        add_task, list_tasks,
        schedule_event, list_events,
        add_note, list_notes,
        execute_software_action,
        launch_immersive_tour
    ],
)
