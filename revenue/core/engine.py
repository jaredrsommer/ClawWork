"""
Revenue Pipeline Engine

Agentic loop that drives all 10 revenue stream workflows.
Uses OpenAI function calling to orchestrate search → analyze → create cycles.

Content Policy:
  All generated content is strictly politically neutral. The engine injects
  a non-negotiable neutrality directive into every system prompt to ensure
  content never takes political sides, mentions political parties, or
  expresses political opinions — making it appropriate for any audience.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import OpenAI

from .tools import TOOL_DEFINITIONS, execute_tool
from .output import OutputManager


class RevenueEngine:
    """
    Agentic pipeline engine for all revenue streams.

    Each run():
    1. Builds a conversation with the stream's system + task prompt
    2. Calls the LLM in a tool-use loop (search → analyze → create)
    3. Executes tools locally (search, file creation, Python execution)
    4. Terminates when the agent calls finish() or hits max_steps
    5. Returns a session result with all created file paths
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        max_steps: int = 20,
        output_dir: str = "./revenue/output",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.7,
        verbose: bool = True,
    ):
        self.model = model
        self.max_steps = max_steps
        self.temperature = temperature
        self.verbose = verbose
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=api_base or os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1",
        )
        self.output_manager = OutputManager(output_dir)

    # Injected into EVERY system prompt — non-negotiable
    NEUTRALITY_DIRECTIVE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTENT POLICY — STRICTLY ENFORCED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All output must be politically neutral and universally appealing.

NEVER:
- Express or imply support for any political party, politician, or ideology
- Take sides on politically divisive topics (abortion, gun control, immigration policy, etc.)
- Use coded political language, dog whistles, or partisan framing
- Write content that would alienate readers based on political beliefs

ALWAYS:
- Stick to business, professional development, finance, technology, and industry topics
- When covering news or trends, present facts without political spin
- If a topic touches politics, reframe it around its business/economic implications only
- Write for ALL readers — conservative, liberal, and everyone in between
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    def run(
        self,
        stream_id: str,
        system_prompt: str,
        task_prompt: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a revenue stream pipeline end-to-end.

        Args:
            stream_id:     Stream identifier (e.g. "ghostwriting")
            system_prompt: Agent persona and capabilities
            task_prompt:   Specific task with parameters interpolated
            params:        Original input params (for logging)

        Returns:
            session_result dict with:
                - session_id, stream_id, params
                - created_files: list of absolute file paths
                - summary: agent's completion summary
                - steps: number of LLM calls used
                - status: "complete" | "timeout" | "error"
        """
        session_id = f"{stream_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = self.output_manager.create_session_dir(stream_id, session_id)

        self._log(f"\n{'='*62}")
        self._log(f"  Revenue Stream : {stream_id.upper().replace('_', ' ')}")
        self._log(f"  Session        : {session_id}")
        self._log(f"  Output dir     : {output_dir}")
        self._log(f"{'='*62}\n")

        # Prepend the neutrality directive to every system prompt
        full_system = system_prompt + self.NEUTRALITY_DIRECTIVE

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": task_prompt},
        ]

        created_files: List[str] = []
        step = 0
        done = False

        session_result: Dict[str, Any] = {
            "session_id": session_id,
            "stream_id": stream_id,
            "params": params,
            "created_files": [],
            "summary": "",
            "steps": 0,
            "status": "running",
            "output_dir": output_dir,
        }

        while step < self.max_steps and not done:
            step += 1
            self._log(f"  [Step {step:02d}/{self.max_steps}] calling LLM...")

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=self.temperature,
                )
            except Exception as exc:
                self._log(f"  [ERROR] LLM call failed: {exc}")
                session_result["status"] = "error"
                session_result["error"] = str(exc)
                break

            assistant_msg = response.choices[0].message

            # Convert to dict for messages list (handles both object and dict forms)
            if hasattr(assistant_msg, "model_dump"):
                messages.append(assistant_msg.model_dump(exclude_none=True))
            else:
                messages.append(assistant_msg)

            # No tool calls = agent finished with text response
            if not assistant_msg.tool_calls:
                session_result["status"] = "complete"
                session_result["summary"] = assistant_msg.content or "Task completed."
                done = True
                break

            # Execute each tool call
            for tool_call in assistant_msg.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                # Pretty-print the call
                arg_preview = ", ".join(
                    f"{k}={repr(v)[:60]}" for k, v in tool_args.items()
                )
                self._log(f"  → {tool_name}({arg_preview})")

                # Handle finish() as a special case
                if tool_name == "finish":
                    session_result["status"] = "complete"
                    session_result["summary"] = tool_args.get("summary", "")
                    deliverables = tool_args.get("deliverables", [])
                    created_files.extend([d for d in deliverables if d not in created_files])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({"status": "finished"}),
                    })
                    done = True
                    break

                # Execute the tool
                tool_result = execute_tool(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    output_dir=output_dir,
                )

                # Track any files produced
                if isinstance(tool_result, dict):
                    for key in ("file_path", "file_paths"):
                        val = tool_result.get(key)
                        if val:
                            if isinstance(val, list):
                                created_files.extend([p for p in val if p])
                            elif val not in created_files:
                                created_files.append(val)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": (
                        json.dumps(tool_result)
                        if not isinstance(tool_result, str)
                        else tool_result
                    ),
                })

                if done:
                    break

        if not done:
            session_result["status"] = "timeout"
            session_result["summary"] = f"Reached max steps ({self.max_steps})."

        # Deduplicate file list
        all_files = list(dict.fromkeys(created_files + session_result.get("created_files", [])))
        session_result["created_files"] = [f for f in all_files if f and os.path.exists(f)]
        session_result["steps"] = step

        # Persist session log
        self.output_manager.save_session_log(session_result, output_dir)

        # Summary output
        self._log(f"\n{'='*62}")
        self._log(f"  Status  : {session_result['status'].upper()}")
        self._log(f"  Steps   : {step}")
        self._log(f"  Files   : {len(session_result['created_files'])}")
        for fpath in session_result["created_files"]:
            self._log(f"            → {fpath}")
        summary_preview = (session_result["summary"] or "")[:200]
        self._log(f"  Summary : {summary_preview}")
        self._log(f"{'='*62}\n")

        return session_result

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)
