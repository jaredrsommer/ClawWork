#!/usr/bin/env python3
"""
Revenue Streams CLI — ClawWork AI Revenue Generation System

Commands:
  list                          List all available revenue streams
  run  <stream> [--param value] Run a specific revenue stream pipeline
  api  [--port 8080]            Start the SaaS REST API server
  history [--stream <id>]       Show past sessions

Examples:

  # Ghostwriting (LinkedIn/Twitter content)
  python revenue/run.py run ghostwriting --client "Sarah Chen" --niche "B2B SaaS" --posts 10

  # SEO article
  python revenue/run.py run seo_content --keyword "best CRM software 2026" --words 1800

  # Digital product (Excel template)
  python revenue/run.py run products --product-type excel_tracker --niche "personal finance"

  # PowerPoint deck
  python revenue/run.py run slide_decks --deck-type pitch_deck --topic "AI startup raising seed"

  # Research report
  python revenue/run.py run research --topic "State of AI in Healthcare 2026" --industry healthcare

  # Podcast production
  python revenue/run.py run podcast --topic "How to build a SaaS without code" --guest "Jane Doe"

  # Book manuscript (KDP)
  python revenue/run.py run publishing --title "The 5AM Framework" --genre self_help

  # Data analysis
  python revenue/run.py run data_analysis --analysis-topic "Q4 2025 sales performance" --industry ecommerce

  # Newsletter issue
  python revenue/run.py run newsletter --newsletter-name "The AI Brief" --niche "artificial intelligence"

  # SaaS API marketing kit
  python revenue/run.py run saas_api --asset-type full_kit --product-name "ContentAPI"

  # Start REST API server
  python revenue/run.py api --port 8080

  # View session history
  python revenue/run.py history
  python revenue/run.py history --stream ghostwriting
"""

import sys
import os
import argparse
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from revenue.streams import REGISTRY
from revenue.core.engine import RevenueEngine
from revenue.core.output import OutputManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bold(s: str) -> str:
    return f"\033[1m{s}\033[0m"

def _green(s: str) -> str:
    return f"\033[32m{s}\033[0m"

def _yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m"

def _cyan(s: str) -> str:
    return f"\033[36m{s}\033[0m"

def _red(s: str) -> str:
    return f"\033[31m{s}\033[0m"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_list(args) -> None:
    """Print a table of all available streams."""
    print(f"\n{_bold('  REVENUE STREAMS — ClawWork AI')}\n")
    print(f"  {'ID':<20} {'NAME':<35} {'PRICING'}")
    print(f"  {'-'*20} {'-'*35} {'-'*30}")
    for sid, mod in REGISTRY.items():
        # Pick a short pricing string
        pricing = list(mod.PRICING.values())[0] if mod.PRICING else ""
        print(f"  {_cyan(sid):<29} {mod.NAME:<35} {_green(str(pricing))}")
    print(f"\n  Run a stream: {_bold('python revenue/run.py run <stream_id> [options]')}")
    print(f"  Get help:     {_bold('python revenue/run.py run <stream_id> --help')}\n")


def cmd_run(args) -> None:
    """Run a revenue stream pipeline."""
    stream_id = args.stream

    if stream_id not in REGISTRY:
        print(_red(f"\n  Error: '{stream_id}' is not a valid stream."))
        print(f"  Available: {', '.join(REGISTRY.keys())}\n")
        sys.exit(1)

    stream = REGISTRY[stream_id]

    # Show help BEFORE validation — check both the flag and REMAINDER list
    raw = args.params or []
    if getattr(args, "help_stream", False) or "--help-stream" in raw or "-h" in raw:
        _print_stream_help(stream_id, stream)
        return

    # Parse extra --param value arguments from args.params
    params = _parse_params([x for x in raw if x != "--help-stream"], stream)

    # Validate
    ok, err = stream.validate_params(params)
    if not ok:
        print(_red(f"\n  Validation error: {err}"))
        _print_stream_help(stream_id, stream)
        sys.exit(1)

    # Run the engine
    model = args.model or os.getenv("REVENUE_MODEL", "gpt-4o")
    max_steps = args.max_steps or 20
    output_dir = args.output or "./revenue/output"

    engine = RevenueEngine(
        model=model,
        max_steps=max_steps,
        output_dir=output_dir,
        verbose=True,
    )

    result = engine.run(
        stream_id=stream_id,
        system_prompt=stream.SYSTEM_PROMPT,
        task_prompt=stream.build_task_prompt(params),
        params=params,
    )

    # Print final file list
    if result.get("created_files"):
        print(f"\n{_bold('  DELIVERABLES')}")
        for fpath in result["created_files"]:
            size_kb = os.path.getsize(fpath) // 1024 if os.path.exists(fpath) else 0
            print(f"  {_green('✓')} {fpath}  ({size_kb} KB)")
    else:
        print(_yellow("\n  No files were created. Check the session log."))

    print(f"\n  Session: {result.get('session_id', '')}")
    print(f"  Status:  {result.get('status', '')}\n")


def cmd_api(args) -> None:
    """Start the SaaS REST API server."""
    port = args.port or int(os.getenv("REVENUE_PORT", "8080"))
    host = args.host or "0.0.0.0"
    output_dir = args.output or "./revenue/output"
    os.environ["REVENUE_OUTPUT_DIR"] = output_dir

    print(f"\n{_bold('  Revenue Streams API')}")
    print(f"  Listening : http://{host}:{port}")
    print(f"  Docs      : http://localhost:{port}/docs")
    print(f"  Streams   : {', '.join(REGISTRY.keys())}")
    api_key = os.getenv("REVENUE_API_KEY", "")
    if api_key:
        print(f"  Auth      : API key required (set in REVENUE_API_KEY)")
    else:
        print(f"  Auth      : {_yellow('None (dev mode) — set REVENUE_API_KEY for production')}")
    print()

    try:
        import uvicorn
        uvicorn.run(
            "revenue.api.server:app",
            host=host,
            port=port,
            reload=args.reload,
            log_level="info",
        )
    except ImportError:
        print(_red("  Error: uvicorn not installed. Run: pip install uvicorn"))
        sys.exit(1)


def cmd_history(args) -> None:
    """Show session history."""
    output_dir = args.output or "./revenue/output"
    stream_id = args.stream or None

    om = OutputManager(output_dir)
    sessions = om.list_sessions(stream_id)

    if not sessions:
        filter_note = f" for stream '{stream_id}'" if stream_id else ""
        print(f"\n  No sessions found{filter_note}.")
        print(f"  Run a stream first: python revenue/run.py run <stream_id>\n")
        return

    print(f"\n{_bold('  SESSION HISTORY')}\n")
    print(f"  {'SESSION ID':<45} {'STREAM':<20} {'STATUS':<10} {'FILES':<6} {'STEPS'}")
    print(f"  {'-'*45} {'-'*20} {'-'*10} {'-'*6} {'-'*5}")
    for s in sessions[:50]:  # cap at 50
        sid = (s.get("session_id") or "")[:45]
        stream = (s.get("stream_id") or "")[:20]
        status = (s.get("status") or "")[:10]
        files = len(s.get("created_files") or [])
        steps = s.get("steps", "?")

        status_colored = (
            _green(status) if status == "complete"
            else _red(status) if status == "error"
            else _yellow(status)
        )
        print(f"  {sid:<45} {stream:<20} {status_colored:<19} {files:<6} {steps}")

    print(f"\n  Total: {len(sessions)} session(s)\n")


# ---------------------------------------------------------------------------
# Param parsing
# ---------------------------------------------------------------------------

def _parse_params(raw_pairs: list, stream) -> dict:
    """
    Convert a flat list of ['--key', 'value', '--key2', 'value2', ...]
    into a params dict, coercing types based on the stream's PARAMETERS spec.
    """
    params = {}
    i = 0
    while i < len(raw_pairs):
        key = raw_pairs[i].lstrip("-").replace("-", "_")
        if i + 1 < len(raw_pairs) and not raw_pairs[i + 1].startswith("--"):
            val = raw_pairs[i + 1]
            i += 2
        else:
            val = "true"
            i += 1

        # Type coercion
        spec = stream.PARAMETERS.get(key, {})
        param_type = spec.get("type", "str")
        try:
            if param_type == "int":
                val = int(val)
            elif param_type == "bool":
                val = val.lower() in ("true", "1", "yes")
            elif param_type == "float":
                val = float(val)
        except (ValueError, TypeError):
            pass

        params[key] = val

    # Apply defaults for missing optional params
    for k, spec in stream.PARAMETERS.items():
        if k not in params and "default" in spec:
            params[k] = spec["default"]

    return params


def _print_stream_help(stream_id: str, stream) -> None:
    """Print help for a specific stream."""
    print(f"\n{_bold(f'  {stream.NAME}')}")
    print(f"  {stream.DESCRIPTION}\n")

    print(f"  {_bold('PRICING')}")
    for k, v in stream.PRICING.items():
        print(f"    {k}: {_green(str(v))}")

    print(f"\n  {_bold('PARAMETERS')}")
    for name, spec in stream.PARAMETERS.items():
        req = _red("required") if spec.get("required") else _yellow(f"default: {spec.get('default', '')}")
        choices = f"  choices: {spec['choices']}" if "choices" in spec else ""
        print(f"    --{name.replace('_', '-'):<25} {spec.get('help', '')}  [{req}]{choices}")

    print(f"\n  {_bold('EXAMPLE')}")
    # Build example command from required params
    required = [
        f"--{k.replace('_', '-')} \"<{v.get('help', k)}>\""
        for k, v in stream.PARAMETERS.items()
        if v.get("required")
    ]
    print(f"    python revenue/run.py run {stream_id} {' '.join(required)}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="revenue",
        description="ClawWork Revenue Streams — AI-powered content generation pipelines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        add_help=True,
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # ---- list ----
    list_parser = subparsers.add_parser("list", help="List all available revenue streams")
    list_parser.set_defaults(func=cmd_list)

    # ---- run ----
    run_parser = subparsers.add_parser("run", help="Run a revenue stream pipeline")
    run_parser.add_argument("stream", help="Stream ID (see: python revenue/run.py list)")
    run_parser.add_argument("--model", default=None, help="LLM model (default: gpt-4o)")
    run_parser.add_argument("--max-steps", type=int, default=20, help="Max agent iterations (default: 20)")
    run_parser.add_argument("--output", default="./revenue/output", help="Output directory")
    run_parser.add_argument("--help-stream", action="store_true", help="Show help for this stream")
    run_parser.add_argument(
        "params",
        nargs=argparse.REMAINDER,
        help="Stream parameters as --key value pairs",
    )
    run_parser.set_defaults(func=cmd_run)

    # ---- api ----
    api_parser = subparsers.add_parser("api", help="Start the SaaS REST API server")
    api_parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    api_parser.add_argument("--output", default="./revenue/output", help="Output directory")
    api_parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev mode)")
    api_parser.set_defaults(func=cmd_api)

    # ---- history ----
    hist_parser = subparsers.add_parser("history", help="View past sessions")
    hist_parser.add_argument("--stream", default=None, help="Filter by stream ID")
    hist_parser.add_argument("--output", default="./revenue/output", help="Output directory")
    hist_parser.set_defaults(func=cmd_history)

    # Parse
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print(f"\n  Quick start: {_bold('python revenue/run.py list')}\n")
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
