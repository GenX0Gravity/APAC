# 🤖 Text Summarizer Agent — ADK + Gemini on Cloud Run

A single AI agent that accepts text input and returns a concise summary.
Built with **Google Agent Development Kit (ADK)**, powered by **Gemini 2.0 Flash**,
deployed as a stateless HTTP service on **Google Cloud Run**.

---

## Architecture

```
Client (HTTP POST)
       │
       ▼
┌─────────────────────────────────┐
│        Cloud Run Service        │
│  ┌───────────────────────────┐  │
│  │   FastAPI HTTP Server     │  │
│  │   POST /summarize         │  │
│  └────────────┬──────────────┘  │
│               │                 │
│  ┌────────────▼──────────────┐  │
│  │   ADK Runner              │  │
│  │   InMemorySessionService  │  │
│  └────────────┬──────────────┘  │
│               │                 │
│  ┌────────────▼──────────────┐  │
│  │   root_agent (ADK Agent)  │  │
│  │   model: gemini-2.0-flash │  │
│  │   tool:  summarize_text() │  │
│  └────────────┬──────────────┘  │
└───────────────┼─────────────────┘
                │
                ▼
       Gemini API (Google AI)
```

---

## Project Structure

```
adk-agent/
├── agent/
│   ├── __init__.py      # Exports root_agent
│   └── agent.py         # ADK Agent definition + tool
├── tests/
│   └── test_main.py     # Unit tests (pytest)
├── main.py              # FastAPI server + ADK runner
├── requirements.txt     # Python dependencies
├── Dockerfile           # Multi-stage Cloud Run image
├── .dockerignore
├── .env.example         # Environment variable template
└── README.md
```

---

## Quick Start (Local)

### Prerequisites
- Python 3.12+
- A [Google AI Studio API key](https://aistudio.google.com/apikey)

### 1. Clone & install

```bash
git clone <your-repo>
cd adk-agent

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=<your key>
```

### 3. Run locally

```bash
source .env                      # or: export $(cat .env | xargs)
python main.py
# Server starts at http://localhost:8080
```

### 4. Test it

```bash
# Health check
curl http://localhost:8080/health

# Summarize text
curl -X POST http://localhost:8080/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence is transforming industries worldwide. From healthcare diagnostics to autonomous vehicles, machine learning models are solving complex problems that once required human expertise. However, this rapid advancement also raises important questions about ethics, job displacement, and the need for thoughtful regulation.",
    "session_id": "my-session"
  }'
```

**Expected response:**
```json
{
  "summary": "AI is rapidly transforming industries like healthcare and transportation, but raises ethical and regulatory concerns alongside its benefits.",
  "session_id": "my-session",
  "agent_name": "text_summarizer_agent",
  "status": "success"
}
```

---

## Deploy to Cloud Run

### Prerequisites
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed & authenticated
- A GCP project with billing enabled

### Step 1 — Set environment variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export SERVICE_NAME="text-summarizer-agent"
export IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"
```

### Step 2 — Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  --project $PROJECT_ID
```

### Step 3 — Store API key in Secret Manager

```bash
echo -n "YOUR_GOOGLE_API_KEY" | \
  gcloud secrets create GOOGLE_API_KEY \
    --data-file=- \
    --project $PROJECT_ID
```

### Step 4 — Build & push the container

```bash
gcloud builds submit \
  --tag $IMAGE \
  --project $PROJECT_ID
```

### Step 5 — Deploy to Cloud Run

```bash
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-secrets="GOOGLE_API_KEY=GOOGLE_API_KEY:latest" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --port 8080 \
  --project $PROJECT_ID
```

### Step 6 — Call your deployed agent

```bash
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format "value(status.url)" \
  --project $PROJECT_ID)

curl -X POST "$SERVICE_URL/summarize" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your long text goes here..."}'
```

---

## API Reference

### `POST /summarize`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | ✅ | Text to summarize (min 10 chars) |
| `session_id` | string | ❌ | Session identifier (default: `"default"`) |

**Response:**
```json
{
  "summary": "Concise summary of the text.",
  "session_id": "string",
  "agent_name": "text_summarizer_agent",
  "status": "success"
}
```

### `GET /health`
Returns `{ "status": "healthy", "agent": "...", "model": "..." }`

### `GET /docs`
Interactive Swagger UI (auto-generated by FastAPI)

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## How It Works

1. **FastAPI** receives `POST /summarize` with a JSON body
2. An **ADK `Runner`** is instantiated with `root_agent` and an `InMemorySessionService`
3. The runner sends the user message to the **Gemini 2.0 Flash** model via the ADK `Agent`
4. The agent may call the `summarize_text` tool (which structures the input), then Gemini generates the summary
5. The final response event is captured and returned as JSON

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `gemini-2.0-flash` | Fast and cost-efficient for summarization tasks |
| `InMemorySessionService` | Simple, no external DB needed for stateless Cloud Run |
| Multi-stage Dockerfile | Smaller final image (~200MB vs ~600MB) |
| FastAPI over Flask | Async-native, built-in validation, auto Swagger docs |
| Secret Manager for API key | Avoids hardcoding secrets in env vars or image layers |
