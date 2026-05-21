from __future__ import annotations

import functools
import inspect
import os
import sys
import time
from enum import Enum
from typing import Any, Callable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich import box


# ──────────────────────────────────────────────────────────────────────────
#  Console & file writer (persistent, ANSI-stripped)
# ──────────────────────────────────────────────────────────────────────────
_console = Console(stderr=False, highlight=True)

_LOG_FILE = "debug.log"          # you can change the path
_LOG_FILE_ENABLED = False

def _write_to_file(message: str) -> None:
    """Write plain-text log message to file (no ANSI codes)."""
    if not _LOG_FILE_ENABLED:
        return
    # simple ANSI strip
    import re
    clean = re.sub(r'\x1b\[[0-9;]*m', '', message)
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(clean + "\n")


# ──────────────────────────────────────────────────────────────────────────
#  Event Level & style mapping
# ──────────────────────────────────────────────────────────────────────────
class EventLevel(Enum):
    INFO       = ("INFO",       "cyan",   "bold cyan")
    SUCCESS    = ("SUCCESS",    "green",  "bold green")
    WARNING    = ("WARNING",    "yellow", "bold yellow")
    ERROR      = ("ERROR",      "red",    "bold red")
    PERFORMANCE = ("PERF",      "blue",   "bold blue")

    def __init__(self, label: str, tag_color: str, text_style: str):
        self.label = label
        self.tag_color = tag_color
        self.text_style = text_style


# ──────────────────────────────────────────────────────────────────────────
#  Main Debug class
# ──────────────────────────────────────────────────────────────────────────
class Debug:
    """
    A beautiful, context-aware debug logger with Rich.

    Features:
        • Event levels with distinct colors
        • Automatic caller detection (function, file, line)
        • Tags like [IO], [SECURITY] for quick scanning
        • Terminal output (Rich) + persistent file log
        • Global toggle (Debug.enabled = False) to silence all output
        • Decorator @Debug.observe for function introspection

    Usage:
        Debug.info("User logged in", tag="AUTH")
        Debug.warning("Disk space low", tag="STORAGE")
        Debug.success("Backup completed", tag="IO")
        Debug.error("Connection refused", tag="NETWORK")
        Debug.performance("Query took", duration=0.042, tag="DB")
    """

    # Global toggle – set False to suppress all debug output
    enabled: bool = True

    # ── Public logging methods ───────────────────────────────────
    @staticmethod
    def info(message: str, *, tag: str = "") -> None:
        Debug._log(EventLevel.INFO, message, tag)

    @staticmethod
    def success(message: str, *, tag: str = "") -> None:
        Debug._log(EventLevel.SUCCESS, message, tag)

    @staticmethod
    def warning(message: str, *, tag: str = "") -> None:
        Debug._log(EventLevel.WARNING, message, tag)

    @staticmethod
    def error(message: str, *, tag: str = "") -> None:
        Debug._log(EventLevel.ERROR, message, tag)

    @staticmethod
    def performance(message: str, *, duration: float, tag: str = "") -> None:
        """
        Log a performance event with measured duration.
        You must pass `duration` (in seconds).
        """
        full_msg = f"{message}  ({duration*1000:.2f} ms)"
        Debug._log(EventLevel.PERFORMANCE, full_msg, tag)

    # ── Internal logging method ──────────────────────────────────
    @staticmethod
    def _log(level: EventLevel, message: str, tag: str) -> None:
        if not Debug.enabled:
            return

        # ---- 1. Auto-detect caller (skip the Debug static methods) ----
        frame = inspect.currentframe()
        if frame is None:
            caller_func = "?"
            caller_file = "?"
            caller_line = 0
        else:
            # Go up two frames: _log() ← public method ← user code
            caller_frame = frame.f_back.f_back if frame.f_back else frame
            info = inspect.getframeinfo(caller_frame)
            caller_func = info.function
            caller_file = os.path.basename(info.filename)
            caller_line = info.lineno

        # ---- 2. Build the rich content ----
        location = f"{caller_file}:{caller_line}"

        # --- Timestamp (short) ---
        timestamp = time.strftime("%H:%M:%S", time.localtime())

        # --- Tag block (optional) ---
        tag_text = Text()
        if tag:
            tag_text.append(f"[{tag}] ", style=level.tag_color)

        # --- Level badge ---
        badge = Text(f" {level.label} ", style=level.tag_color + " on default")

        # --- Main line ---
        main = Text()
        main.append(f" {message}", style=level.text_style)

        # --- Caller line (dim) ---
        caller = Text()
        caller.append(f"\n    → {caller_func}()", style="dim")
        caller.append(f"  @ {location}", style="dim italic")

        # ---- 3. Assemble into a compact panel ----
        content = Text()
        content.append(badge)
        content.append(tag_text)
        content.append(main)
        content.append(caller)

        panel = Panel(
            content,
            border_style=level.tag_color,
            box=box.SIMPLE,
            padding=(0, 2),
            expand=False,
        )

        # ---- 4. Output ----
        console_msg = f"[{timestamp}] "
        console_msg += (f"[{tag}] " if tag else "")
        console_msg += f"[{level.label}] {message}  ({caller_func} @ {location})"

        _console.print(panel)
        _write_to_file(console_msg)

    # ── Decorator for function observation ───────────────────────
    @staticmethod
    def observe(tag: str = ""):
        """
        Decorator that logs entry, exit, and execution time for any function.
        Usage:
            @Debug.observe(tag="DB")
            def query_database(sql):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Log entry
                Debug.info(
                    f"Entering {func.__name__}()",
                    tag=f"OBSERVE {tag}" if tag else "OBSERVE"
                )
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.perf_counter() - start
                    Debug.performance(
                        f"{func.__name__}() completed",
                        duration=elapsed,
                        tag=f"OBSERVE {tag}" if tag else "OBSERVE"
                    )
                    return result
                except Exception as e:
                    elapsed = time.perf_counter() - start
                    Debug.error(
                        f"{func.__name__}() raised {type(e).__name__}: {e}",
                        tag=f"OBSERVE {tag}" if tag else "OBSERVE"
                    )
                    raise
            return wrapper
        return decorator
