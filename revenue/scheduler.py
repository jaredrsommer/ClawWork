"""
Revenue Scheduler

Autonomous cron-based runner for all 10 revenue streams.
Runs streams on a schedule, then pushes output to configured platforms.

Usage:
  python revenue/run.py schedule start                  # Start daemon
  python revenue/run.py schedule status                 # Show next runs
  python revenue/run.py schedule run-now <schedule_id>  # Trigger immediately
  python revenue/run.py schedule history                # Past runs

Config: revenue/scheduler_config.json
State:  revenue/scheduler_state.json
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from revenue.core.engine import RevenueEngine
from revenue.streams import REGISTRY
from revenue.publishers import get_publisher, list_publishers

logger = logging.getLogger("revenue.scheduler")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "scheduler_config.json")
STATE_PATH = os.path.join(os.path.dirname(__file__), "scheduler_state.json")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def _load_state() -> Dict:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"counters": {}, "last_runs": {}, "history": []}


def _save_state(state: Dict) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str)


def _load_config() -> Dict:
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(
            f"Scheduler config not found: {CONFIG_PATH}\n"
            "Run: python revenue/run.py schedule init"
        )
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Keyword queue
# ---------------------------------------------------------------------------

def _pop_keyword(queue_path: str) -> Optional[str]:
    """Pop the next keyword from the queue file (one keyword per line)."""
    if not os.path.exists(queue_path):
        return None
    with open(queue_path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    if not lines:
        return None
    keyword = lines[0]
    # Remove it from the queue (rotate: move to end)
    remaining = lines[1:] + [keyword]
    with open(queue_path, "w", encoding="utf-8") as f:
        f.write("\n".join(remaining) + "\n")
    return keyword


# ---------------------------------------------------------------------------
# Core: run one scheduled job
# ---------------------------------------------------------------------------

def run_schedule(schedule_cfg: Dict, dry_run: bool = False) -> Dict:
    """
    Execute one scheduled stream run + publish to configured platforms.

    Args:
        schedule_cfg: A schedule entry from scheduler_config.json
        dry_run:      If True, skip actual LLM calls and publishing

    Returns:
        Run result dict
    """
    schedule_id = schedule_cfg["id"]
    stream_id = schedule_cfg["stream"]
    params = dict(schedule_cfg.get("params", {}))

    print(f"\n{'='*62}")
    print(f"  Scheduler: {schedule_id}")
    print(f"  Stream   : {stream_id}")
    print(f"  Time     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*62}")

    state = _load_state()

    # ---- Auto-increment params (e.g. issue_number) ----
    auto_inc = schedule_cfg.get("auto_increment")
    if auto_inc:
        param_name = auto_inc["param"]
        state_key = auto_inc["state_key"]
        current = state["counters"].get(state_key, 0) + 1
        params[param_name] = current
        state["counters"][state_key] = current

    # ---- Keyword queue ----
    kw_queue = schedule_cfg.get("keyword_queue")
    if kw_queue:
        kw_queue = os.path.expanduser(kw_queue)
        keyword = _pop_keyword(kw_queue)
        if keyword:
            params["keyword"] = keyword
            print(f"  Keyword  : {keyword}")
        else:
            print("  WARNING: Keyword queue is empty — skipping run")
            return {"status": "skipped", "reason": "keyword queue empty"}

    # ---- Get stream ----
    if stream_id not in REGISTRY:
        return {"status": "error", "error": f"Unknown stream: {stream_id}"}

    stream = REGISTRY[stream_id]
    ok, err = stream.validate_params(params)
    if not ok:
        return {"status": "error", "error": f"Param validation failed: {err}"}

    # ---- Run pipeline ----
    result = {"status": "dry_run", "stream_id": stream_id, "params": params}
    if not dry_run:
        model = schedule_cfg.get("model", os.getenv("REVENUE_MODEL", "gpt-4o"))
        engine = RevenueEngine(
            model=model,
            max_steps=schedule_cfg.get("max_steps", 20),
            output_dir=OUTPUT_DIR,
        )
        result = engine.run(
            stream_id=stream_id,
            system_prompt=stream.SYSTEM_PROMPT,
            task_prompt=stream.build_task_prompt(params),
            params=params,
        )

    # ---- Publish to platforms ----
    publish_results = []
    config = _load_config()
    global_publisher_settings = config.get("publisher_settings", {})

    for platform in schedule_cfg.get("publish_to", []):
        publisher = get_publisher(platform)
        if publisher is None:
            publish_results.append({"platform": platform, "status": "not_found"})
            continue
        if not publisher.can_publish():
            publish_results.append({
                "platform": platform,
                "status": "skipped",
                "reason": "credentials not configured",
            })
            print(f"  Publisher [{platform}]: credentials not set — skipping")
            continue

        print(f"  Publisher [{platform}]: publishing...")
        if dry_run:
            publish_results.append({"platform": platform, "status": "dry_run"})
        else:
            pres = publisher.publish(
                session_result=result,
                stream_id=stream_id,
                settings=global_publisher_settings.get(platform, {}),
            )
            publish_results.append(pres)
            status_icon = "✓" if pres.get("success") else "✗"
            print(f"  Publisher [{platform}]: {status_icon} {pres.get('url') or pres.get('error', '')}")

    # ---- Update state ----
    run_record = {
        "schedule_id": schedule_id,
        "stream_id": stream_id,
        "timestamp": datetime.now().isoformat(),
        "status": result.get("status", "unknown"),
        "session_id": result.get("session_id", ""),
        "files_created": len(result.get("created_files", [])),
        "publish_results": publish_results,
    }
    state["last_runs"][schedule_id] = run_record
    state["history"] = [run_record] + state["history"][:99]  # keep last 100
    _save_state(state)

    return run_record


# ---------------------------------------------------------------------------
# Scheduler daemon
# ---------------------------------------------------------------------------

def start_daemon(dry_run: bool = False) -> None:
    """Start the APScheduler daemon and block."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        print("ERROR: apscheduler not installed. Run: pip install apscheduler")
        sys.exit(1)

    config = _load_config()
    scheduler = BlockingScheduler(timezone="UTC")

    registered = 0
    for sched in config.get("schedules", []):
        if not sched.get("enabled", True):
            print(f"  [skip]    {sched['id']} (disabled)")
            continue

        cron_cfg = sched.get("cron", {})

        def make_job(s=sched):
            def job():
                run_schedule(s, dry_run=dry_run)
            job.__name__ = s["id"]
            return job

        trigger = CronTrigger(**cron_cfg, timezone="UTC")
        scheduler.add_job(
            make_job(),
            trigger=trigger,
            id=sched["id"],
            name=sched.get("name", sched["id"]),
            misfire_grace_time=3600,
        )
        next_run = trigger.get_next_fire_time(None, datetime.utcnow())
        print(f"  [scheduled] {sched['id']:<30} next: {next_run}")
        registered += 1

    if registered == 0:
        print("\n  No enabled schedules found. Edit revenue/scheduler_config.json")
        return

    print(f"\n  Scheduler started with {registered} job(s). Ctrl+C to stop.\n")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n  Scheduler stopped.")


def print_status() -> None:
    """Print scheduled jobs and their next run times."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        print("  apscheduler not installed.")
        return

    config = _load_config()
    state = _load_state()

    print(f"\n  {'ID':<30} {'ENABLED':<8} {'CRON':<30} {'LAST RUN':<22} {'STATUS'}")
    print(f"  {'-'*30} {'-'*8} {'-'*30} {'-'*22} {'-'*10}")

    for sched in config.get("schedules", []):
        sid = sched["id"]
        enabled = "yes" if sched.get("enabled", True) else "no"
        cron_cfg = sched.get("cron", {})
        cron_str = " ".join(f"{k}={v}" for k, v in cron_cfg.items())
        last = state["last_runs"].get(sid, {})
        last_ts = last.get("timestamp", "never")[:19]
        last_status = last.get("status", "-")
        print(f"  {sid:<30} {enabled:<8} {cron_str:<30} {last_ts:<22} {last_status}")
    print()

    # Counter state
    if state.get("counters"):
        print("  Counters:")
        for k, v in state["counters"].items():
            print(f"    {k}: {v}")
        print()


def print_history(limit: int = 20) -> None:
    """Print recent scheduler run history."""
    state = _load_state()
    history = state.get("history", [])[:limit]

    if not history:
        print("\n  No run history yet.\n")
        return

    print(f"\n  {'TIMESTAMP':<22} {'SCHEDULE ID':<30} {'STATUS':<12} {'FILES':<6} {'PUBLISHED'}")
    print(f"  {'-'*22} {'-'*30} {'-'*12} {'-'*6} {'-'*20}")
    for r in history:
        ts = r.get("timestamp", "")[:19]
        sid = r.get("schedule_id", "")[:30]
        status = r.get("status", "")[:12]
        files = str(r.get("files_created", "?"))
        pub = ", ".join(
            p.get("platform", "") for p in r.get("publish_results", [])
            if p.get("status") not in ("skipped", "not_found", "dry_run")
        ) or "-"
        print(f"  {ts:<22} {sid:<30} {status:<12} {files:<6} {pub}")
    print()
