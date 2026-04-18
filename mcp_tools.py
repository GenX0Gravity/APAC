import sqlite3
import json
from typing import Dict, Any, List

from database import get_connection
import random
import string

def generate_meet_link() -> str:
    """Generates a mock Google Meet link."""
    code = f"{''.join(random.choices(string.ascii_lowercase, k=3))}-{''.join(random.choices(string.ascii_lowercase, k=4))}-{''.join(random.choices(string.ascii_lowercase, k=3))}"
    return f"https://meet.google.com/{code}"

# --- Task Manager Mock MCP Tools ---

def add_task(description: str, due_date: str = "No due date") -> str:
    """
    Adds a new task to the task manager.

    Args:
        description: The description of the task.
        due_date: The due date/time of the task (e.g., 'tomorrow', '2026-05-01').
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (description, due_date)
                VALUES (?, ?)
            ''', (description, due_date))
            conn.commit()
            return f"Task added successfully with ID {cursor.lastrowid}: '{description}' due {due_date}"
    except Exception as e:
        return f"Error adding task: {e}"

def list_tasks() -> str:
    """
    Lists all tasks currently in the task manager.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, description, due_date, status FROM tasks')
            rows = cursor.fetchall()
            if not rows:
                return "No tasks found."
            
            result = ["Current Tasks:"]
            for r in rows:
                result.append(f"[{r[0]}] {r[1]} | Due: {r[2]} | Status: {r[3]}")
            return "\n".join(result)
    except Exception as e:
        return f"Error listing tasks: {e}"


# --- Calendar Mock MCP Tools ---

def schedule_event(title: str, event_time: str) -> str:
    """
    Schedules a new event in the calendar.

    Args:
        title: The title of the calendar event.
        event_time: The date and time of the event (e.g., '2026-04-20 10:00 AM').
    """
    try:
        meet_link = generate_meet_link()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO calendar_events (title, event_time, meet_link)
                VALUES (?, ?, ?)
            ''', (title, event_time, meet_link))
            conn.commit()
            return f"Event scheduled successfully with ID {cursor.lastrowid}: '{title}' at {event_time}. Meet Link generated: {meet_link}"
    except Exception as e:
        return f"Error scheduling event: {e}"

def list_events() -> str:
    """
    Lists all scheduled calendar events.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, event_time, meet_link FROM calendar_events')
            rows = cursor.fetchall()
            if not rows:
                return "No events found in the calendar."
            
            result = ["Upcoming Events:"]
            for r in rows:
                link = r[3] if len(r) > 3 and r[3] else "No link"
                result.append(f"[{r[0]}] {r[1]} - {r[2]} (Link: {link})")
            return "\n".join(result)
    except Exception as e:
        return f"Error listing events: {e}"


# --- Notes Mock MCP Tools ---

def add_note(content: str) -> str:
    """
    Saves a new note to the knowledge base.

    Args:
        content: The text content of the note.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notes (content)
                VALUES (?)
            ''', (content,))
            conn.commit()
            return f"Note added successfully with ID {cursor.lastrowid}."
    except Exception as e:
        return f"Error adding note: {e}"

def list_notes() -> str:
    """
    Lists all saved notes from the knowledge base.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, content, created_at FROM notes')
            rows = cursor.fetchall()
            if not rows:
                return "No notes found."
            
            result = ["Saved Notes:"]
            for r in rows:
                result.append(f"[{r[0]}] (Saved {r[2]}): {r[1]}")
            return "\n".join(result)
    except Exception as e:
        return f"Error listing notes: {e}"

# --- Universal Software Task Executor ---

def execute_software_action(action_name: str, parameters: str) -> str:
    """
    Executes a generic software-based action or system workflow not explicitly covered by other tools.

    Args:
        action_name: A short descriptor of the task being performed (e.g., 'trigger_build', 'book_flight', 'provision_server').
        parameters: A stringified dictionary or summary of all the rigorously collected parameters specific to the task.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO action_logs (action_name, parameters)
                VALUES (?, ?)
            ''', (action_name, parameters))
            conn.commit()
            return f"Action '{action_name}' executed successfully with params: {parameters}. Ref ID: {cursor.lastrowid}"
    except Exception as e:
        return f"Error executing software action: {e}"
