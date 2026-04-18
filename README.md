# 🤖 Nexus Workspace Agent — Cinematic Multi-Agent AI System

An intelligent, multi-agent workspace assistant built with **Google ADK** and **Gemini 2.0 Flash**. This system helps users manage tasks, calendars, and notes, and provides a universal software execution engine for autonomous real-time workflows, all wrapped in a premium cinematic experience.

---

## 🌟 Features

- **Multi-Agent Orchestration**: A primary orchestrator coordinating specialized sub-agents (`Task`, `Calendar`, `SoftwareOps`) for a seamless, domain-aware user experience.
- **Cinematic Workspace Simulation**: A high-fidelity, dual-pane dashboard featuring 6 dynamic visual themes (Neon Dark, Corporate Light, Cyberpunk, Terminal, Cinematic Thriller, and Nostalgic).
- **Intelligent Vibe Control**: Responsive background music and visual themes that can be triggered manually or intelligently by the AI Orchestrator to match the task context.
- **Universal Software Action Executor**: Dynamically handles arbitrary software tasks (e.g., triggering rollbacks, provisioning servers) by collecting required parameters through interactive dialogue.
- **SQLite Persistence**: Fully integrated database backend for persisting tasks, calendar events, notes, and action logs.
- **Automated Scheduling**: Automatically generates and associates Google Meet links with new calendar events.
- **Cloud Run Ready**: Fully containerized and optimized for Google Cloud Run deployment.

---

## 🏗️ Technical Architecture

- **Engine**: [Google ADK (Agent Development Kit)](https://github.com/google/adk)
- **Model**: Gemini 2.0 Flash
- **Framework**: FastAPI (Python 3.12)
- **Frontend**: Vanilla JS, CSS (with Cinematic Audio Cross-fading)
- **Persistence**: SQLite 3
- **Deployment**: Docker + Google Cloud Run

---

## 🚀 Getting Started

### Local Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/GenX0Gravity/APAC.git
   cd APAC
   ```

2. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```bash
   python main.py
   ```
   The application will be available at `http://localhost:8080`.

### Cloud Run Deployment

Deploy directly from source using the Google Cloud SDK:

```bash
gcloud run deploy workspace-agent --source . --region us-central1 --allow-unauthenticated
```

---

## 🛠️ Integrated Agents & Tools

- **Primary Orchestrator**: The central brain that understands your intent and delegates to specialized sub-agents.
- **Task Manager**: Add, list, and track actionable items.
- **Calendar Supervisor**: Schedule events with auto-generated meeting links.
- **Knowledge Base**: Save and retrieve persistent notes.
- **Universal Action Executor**: Perform any generic software or system workflow with a non-refusal policy.
- **Music & Environment**: Control the "vibe" of your workspace via AI commands.

---

## 🔒 Security & Best Practices

- **Session Management**: Uses ADK's `InMemorySessionService` for context tracking across multi-agent handoffs.
- **Non-Root Execution**: Docker container runs as a non-privileged `appuser`.
- **Environment Isolation**: Sensitive keys are handled via environment variables/Secret Manager.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
