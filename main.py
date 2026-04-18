"""
HTTP server for the Multi-Agent Workspace system.
Exposes the ADK agent via a REST API, deployable to Cloud Run.
"""

# Load .env FIRST — before any SDK imports read env vars
from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agent import root_agent
from database import get_full_state


# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── ADK Session Service ───────────────────────────────────────────────────────
SESSION_SERVICE = InMemorySessionService()
APP_NAME = "workspace-agent"

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Workspace Agent starting up...")
    yield
    logger.info("Workspace Agent shutting down...")

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Workspace Agent",
    description="An AI-powered workspace agent built with Google ADK and Gemini.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Assets and Frontend Directory
assets_dir = os.path.join(os.path.dirname(__file__), "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="frontend_static")

# ── Request / Response Models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    text: str = Field(..., min_length=2, description="User instruction or message")
    session_id: str = Field(default="default", description="Optional session identifier")


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    agent_name: str
    status: str = "success"


class HealthResponse(BaseModel):
    status: str
    agent: str
    model: str


# ── Helper ────────────────────────────────────────────────────────────────────
async def run_agent(user_message: str, session_id: str) -> str:
    """Run the ADK agent and return the final text response."""
    # Ensure session exists (both methods are async in ADK >= 0.4)
    session = await SESSION_SERVICE.get_session(
        app_name=APP_NAME, user_id="api_user", session_id=session_id
    )
    if session is None:
        await SESSION_SERVICE.create_session(
            app_name=APP_NAME, user_id="api_user", session_id=session_id
        )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=SESSION_SERVICE,
    )

    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_message)],
    )

    final_response = ""
    async for event in runner.run_async(
        user_id="api_user",
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            break

    return final_response or "No response generated."


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Dashboard"])
async def get_dashboard():
    """Serve the Workspace Dashboard."""
    index_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend index.html not found.")


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint required by Cloud Run."""
    return HealthResponse(
        status="healthy",
        agent=root_agent.name,
        model="gemini-3-flash-preview",
    )


@app.post("/chat", tags=["Agent"])
async def chat(request: ChatRequest):
    """
    Send an instruction to the Primary Orchestrator Agent.
    Returns a stream of events (thoughts, text, and metadata).
    """
    try:
        logger.info(f"Chat request | session={request.session_id}")

        async def event_generator():
            # Ensure session exists
            session = await SESSION_SERVICE.get_session(
                app_name=APP_NAME, user_id="api_user", session_id=request.session_id
            )
            if session is None:
                await SESSION_SERVICE.create_session(
                    app_name=APP_NAME, user_id="api_user", session_id=request.session_id
                )

            runner = Runner(
                agent=root_agent,
                app_name=APP_NAME,
                session_service=SESSION_SERVICE,
            )

            content = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=request.text)],
            )

            async for event in runner.run_async(
                user_id="api_user",
                session_id=request.session_id,
                new_message=content,
            ):
                try:
                    chunk = {"type": "unknown", "content": ""}
                    
                    # 1. Detect Tool Calls
                    func_calls = getattr(event, 'get_function_calls', lambda: [])()
                    if func_calls:
                        chunk["type"] = "tool_start"
                        chunk["content"] = func_calls[0].name
                    
                    # 2. Extract Response Text (and check for Environment Overrides)
                    elif hasattr(event, 'content') and event.content and event.content.parts:
                        text_parts = [p.text for p in event.content.parts if hasattr(p, 'text') and p.text]
                        if text_parts:
                            combined_text = " ".join(text_parts)
                            
                            # Intercept environment commands
                            if "ENVIRONMENT_OVERRIDE:" in combined_text:
                                mood = combined_text.split("ENVIRONMENT_OVERRIDE:")[1].strip()
                                chunk["type"] = "environment_change"
                                chunk["content"] = mood
                            else:
                                chunk["type"] = "final"
                                chunk["content"] = combined_text
                    
                    if chunk["content"]:
                        yield json.dumps(chunk) + "\n"
                        
                except Exception as e:
                    logging.error(f"Error processing stream chunk: {e}")
                    # Skip malformed chunks but keep the stream alive
                    continue

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/workspace/state", tags=["Workspace"])
async def get_workspace_state():
    """Fetch the full system state for tasks, calendar, notes, and actions."""
    try:
        return get_full_state()
    except Exception as e:
        logger.error(f"Error fetching workspace state: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    """Serve the frontend UI."""
    frontend = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend):
        return FileResponse(frontend, media_type="text/html")
    return {
        "service": "Multi-Agent Coordinator",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Interact with the Orchestrator",
            "GET /health": "Health check",
            "GET /docs": "Interactive API docs (Swagger UI)",
        },
    }


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
