import os
from google.adk.agents import Agent
from mcp_tools import (
    add_task, list_tasks,
    schedule_event, list_events,
    add_note, list_notes,
    execute_software_action
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
        "You are an interactive AI Workspace Assistant. "
        "You perform actual tasks by calling your integrated tools (Task Manager, Calendar, Notes, and a Universal Software Action Executor).\n\n"
        "RULES:\n"
        "1. DO NOT guess or hallucinate missing information.\n"
        "2. If requested to perform ANY real-time task (e.g. provision a server, query a database, deploy code, schedule a meeting, run scripts), deduce the logically required parameters for that task. If ANY parameters are missing, you MUST ask the user for them FIRST before proceeding.\n"
        "3. Keep your clarifying questions natural and conversational.\n"
        "4. Once you have all required parameters, execute the dedicated tool (if it relates to Calendar, Notes, or Tasks). For ALL other generic software or real-time tasks, use `execute_software_action`.\n"
        "5. After successfully executing a tool, provide a friendly final message explicitly sharing the generated data (event links, execution parameters, ref IDs) so the user knows you authentically completed it.\n"
    ),
    tools=[
        add_task, list_tasks,
        schedule_event, list_events,
        add_note, list_notes,
        execute_software_action
    ],
)
