"""
Text Summarization Agent using Google ADK + Gemini via Vertex AI.
Accepts any text input and returns a concise summary.
Uses Vertex AI backend (project billing) instead of AI Studio free tier.
"""

import os

from google.adk.agents import Agent

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


# Use Vertex AI to leverage project billing and avoid free-tier quota limits
root_agent = Agent(
    name="text_summarizer_agent",
    model="vertexai/gemini-2.0-flash",
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
