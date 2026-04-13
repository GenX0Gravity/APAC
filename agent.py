"""
Text Summarization Agent using Google ADK + Gemini via Vertex AI.
Accepts any text input and returns a concise summary.
Uses Vertex AI backend (project billing) instead of AI Studio free tier.
"""

import os

from google.adk.agents import Agent
from google import genai

# Define the summarization tool
def summarize_text(text: str) -> dict:
    """
    Summarizes the provided text into a concise, clear summary.

    Args:
        text: The input text to summarize.

    Returns:
        A dictionary containing the summary and metadata.
    """
    # The agent itself (Gemini) will perform the summarization.
    # This tool acts as the structured entry point.
    return {
        "status": "success",
        "input_length": len(text.split()),
        "text": text,
    }


# Configure client for Vertex AI on Cloud Run (ADC) or AI Studio locally (API key)
_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
_location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

if _project:
    genai_client = genai.Client(vertexai=True, project=_project, location=_location)
else:
    genai_client = genai.Client()

root_agent = Agent(
    name="text_summarizer_agent",
    model="gemini-2.0-flash",
    client=genai_client,
    description=(
        "An AI agent that summarizes text. "
        "Given any text input, it returns a concise and accurate summary."
    ),
    instruction=(
        "You are a professional text summarization assistant. "
        "When the user provides text to summarize, use the summarize_text tool "
        "to process it, then provide a clear, concise summary that captures "
        "the key points. Keep summaries to 2-3 sentences unless the text is very long. "
        "Always respond in a structured, helpful manner."
    ),
    tools=[summarize_text],
)
