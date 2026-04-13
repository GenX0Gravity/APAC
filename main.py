"""
HTTP server for the Text Summarization Agent.
Exposes the ADK agent via a REST API, deployable to Cloud Run.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agent import root_agent

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── ADK Session Service ───────────────────────────────────────────────────────
SESSION_SERVICE = InMemorySessionService()
APP_NAME = "text-summarizer-agent"

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Text Summarizer Agent starting up...")
    yield
    logger.info("Text Summarizer Agent shutting down...")

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Text Summarizer Agent",
    description="An AI-powered text summarization agent built with Google ADK and Gemini.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response Models ─────────────────────────────────────────────────
class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Text to summarize (min 10 chars)")
    session_id: str = Field(default="default", description="Optional session identifier")


class SummarizeResponse(BaseModel):
    summary: str
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
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint required by Cloud Run."""
    return HealthResponse(
        status="healthy",
        agent=root_agent.name,
        model="gemini-2.0-flash-lite",
    )


@app.post("/summarize", response_model=SummarizeResponse, tags=["Agent"])
async def summarize(request: SummarizeRequest):
    """
    Summarize the provided text using the Gemini-powered ADK agent.

    - **text**: The input text you want summarized
    - **session_id**: Optional identifier to maintain conversation context
    """
    try:
        logger.info(f"Summarize request | session={request.session_id} | chars={len(request.text)}")
        prompt = f"Please summarize the following text:\n\n{request.text}"
        summary = await run_agent(prompt, request.session_id)
        return SummarizeResponse(
            summary=summary,
            session_id=request.session_id,
            agent_name=root_agent.name,
        )
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with usage info."""
    return {
        "service": "Text Summarizer Agent",
        "version": "1.0.0",
        "endpoints": {
            "POST /summarize": "Summarize input text",
            "GET /health": "Health check",
            "GET /docs": "Interactive API docs (Swagger UI)",
        },
    }


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
