"""
Revenue API Server

FastAPI server exposing all 10 revenue streams as REST endpoints.

Start: python revenue/run.py api [--port 8080]
  Or:  uvicorn revenue.api.server:app --port 8080 --reload

API KEY: Set REVENUE_API_KEY env var to require authentication.
         Leave unset for development (no auth required).

Endpoints:
  POST /v1/{stream_id}               Run a revenue stream
  GET  /v1/sessions                  List all sessions
  GET  /v1/sessions/{session_id}     Get session result
  GET  /v1/sessions/{session_id}/files/{filename}  Download file
  GET  /v1/streams                   List all available streams
  GET  /healthz                      Health check
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Make sure we can import from project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from revenue.core.engine import RevenueEngine
from revenue.streams import REGISTRY

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Revenue Streams API",
    description=(
        "AI-powered content generation API. "
        "Send a task → receive professional deliverable files."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = os.path.abspath(
    os.getenv("REVENUE_OUTPUT_DIR", "./revenue/output")
)
API_KEY = os.getenv("REVENUE_API_KEY", "")


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def check_auth(x_api_key: Optional[str] = None) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class TaskRequest(BaseModel):
    params: Dict[str, Any]
    model: str = "gpt-4o"
    max_steps: int = 20
    async_run: bool = False  # If True, return session_id immediately


class TaskResponse(BaseModel):
    session_id: str
    stream_id: str
    status: str
    steps: int
    created_files: list
    summary: str
    output_dir: str


# ---------------------------------------------------------------------------
# In-memory session store (for async results)
# ---------------------------------------------------------------------------

_sessions: Dict[str, Dict] = {}


def _run_stream(stream_id: str, request: TaskRequest) -> Dict:
    """Synchronously run a stream and store result."""
    stream = REGISTRY[stream_id]
    ok, err = stream.validate_params(request.params)
    if not ok:
        return {"status": "error", "error": err, "session_id": "", "created_files": []}

    engine = RevenueEngine(
        model=request.model,
        max_steps=request.max_steps,
        output_dir=OUTPUT_DIR,
    )
    result = engine.run(
        stream_id=stream_id,
        system_prompt=stream.SYSTEM_PROMPT,
        task_prompt=stream.build_task_prompt(request.params),
        params=request.params,
    )
    _sessions[result["session_id"]] = result
    return result


# ---------------------------------------------------------------------------
# Routes: stream execution
# ---------------------------------------------------------------------------

@app.get("/healthz")
def health():
    return {"status": "ok", "streams": list(REGISTRY.keys())}


@app.get("/v1/streams")
def list_streams():
    """List all available revenue streams with metadata."""
    return {
        sid: {
            "name": mod.NAME,
            "description": mod.DESCRIPTION,
            "pricing": mod.PRICING,
            "parameters": mod.PARAMETERS,
        }
        for sid, mod in REGISTRY.items()
    }


@app.post("/v1/{stream_id}", response_model=TaskResponse)
def run_stream(
    stream_id: str,
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(default=None),
):
    """
    Execute a revenue stream pipeline.

    Returns the session result with created file paths.
    Files are downloadable via GET /v1/sessions/{session_id}/files/{filename}
    """
    check_auth(x_api_key)

    if stream_id not in REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"Stream '{stream_id}' not found. Available: {list(REGISTRY.keys())}",
        )

    if request.async_run:
        # Return a placeholder session immediately, run in background
        import uuid
        session_id = f"{stream_id}_async_{uuid.uuid4().hex[:8]}"
        _sessions[session_id] = {"session_id": session_id, "status": "running", "stream_id": stream_id}
        background_tasks.add_task(_run_and_store, stream_id, request, session_id)
        return TaskResponse(
            session_id=session_id,
            stream_id=stream_id,
            status="running",
            steps=0,
            created_files=[],
            summary="Task queued for background execution.",
            output_dir="",
        )

    result = _run_stream(stream_id, request)
    return TaskResponse(
        session_id=result.get("session_id", ""),
        stream_id=stream_id,
        status=result.get("status", "unknown"),
        steps=result.get("steps", 0),
        created_files=result.get("created_files", []),
        summary=result.get("summary", ""),
        output_dir=result.get("output_dir", ""),
    )


def _run_and_store(stream_id: str, request: TaskRequest, placeholder_id: str) -> None:
    result = _run_stream(stream_id, request)
    _sessions[placeholder_id].update(result)


# ---------------------------------------------------------------------------
# Routes: session management
# ---------------------------------------------------------------------------

@app.get("/v1/sessions")
def list_sessions(stream_id: Optional[str] = None):
    """List all completed sessions."""
    from revenue.core.output import OutputManager
    om = OutputManager(OUTPUT_DIR)
    sessions = om.list_sessions(stream_id)
    # Also include in-memory async sessions
    for sid, s in _sessions.items():
        if not any(x.get("session_id") == sid for x in sessions):
            sessions.append(s)
    return {"sessions": sessions, "count": len(sessions)}


@app.get("/v1/sessions/{session_id}")
def get_session(session_id: str):
    """Get the result of a specific session."""
    # Check in-memory first (async sessions)
    if session_id in _sessions:
        return _sessions[session_id]

    # Search on disk
    from revenue.core.output import OutputManager
    om = OutputManager(OUTPUT_DIR)
    all_sessions = om.list_sessions()
    for s in all_sessions:
        if s.get("session_id") == session_id:
            return s

    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")


@app.get("/v1/sessions/{session_id}/files/{filename}")
def download_file(session_id: str, filename: str):
    """Download a file produced by a session."""
    session = get_session(session_id)
    output_dir = session.get("output_dir", "")
    file_path = os.path.join(output_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found in session")

    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


# ---------------------------------------------------------------------------
# Dev server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("REVENUE_PORT", "8080"))
    print(f"\n Revenue Streams API starting on http://localhost:{port}")
    print(f"  Docs: http://localhost:{port}/docs")
    print(f"  Streams: {list(REGISTRY.keys())}\n")
    uvicorn.run("revenue.api.server:app", host="0.0.0.0", port=port, reload=True)
