"""
HTTP server for the Multi-Agent Workspace system.
Exposes the ADK agent via a REST API, deployable to Cloud Run.
"""

# Load .env FIRST — before any SDK imports read env vars
from dotenv import load_dotenv
load_dotenv()

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agent import root_agent


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

# Mount static assets for simulation images
if os.path.exists("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# ── Request / Response Models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    text: str = Field(..., min_length=2, description="User instruction or message")
    session_id: str = Field(default="default", description="Optional session identifier")


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    agent_name: str
    status: str = "success"
    simulation_config: Optional[Dict[str, Any]] = Field(default=None, description="Configuration for immersive experiences")


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
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint required by Cloud Run."""
    return HealthResponse(
        status="healthy",
        agent=root_agent.name,
        model="gemini-2.5-flash",
    )


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
async def chat(request: ChatRequest):
    """
    Send an instruction to the Primary Orchestrator Agent.

    - **text**: The input message or instruction
    - **session_id**: Optional identifier to maintain conversation context
    """
    try:
        logger.info(f"Chat request | session={request.session_id} | chars={len(request.text)}")
        
        # We handle the agent run
        # Note: In a production setup, we'd extract the tool call results 
        # specifically if they trigger a simulation state.
        reply = await run_agent(request.text, request.session_id)
        
        # Check if the result implies a simulation (highly simplified for the hackathon)
        sim_config = None
        if "SIMULATION_CONFIG:" in reply:
            parts = reply.split("SIMULATION_CONFIG:")
            reply = parts[0].strip()
            try:
                import json
                sim_config = json.loads(parts[1].strip())
            except:
                pass

        return ChatResponse(
            reply=reply,
            session_id=request.session_id,
            agent_name=root_agent.name,
            simulation_config=sim_config
        )
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


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
