"""Load API keys from a .env file (current folder first, then the project root).
Variables already set in the terminal win over the file. Standard library only."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_env_file(explicit: Optional[str] = None) -> Optional[Path]:
    if explicit:
        p = Path(explicit).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"--env-file not found: {p}")
        return p
    for p in (Path.cwd() / ".env", PROJECT_ROOT / ".env"):
        if p.is_file():
            return p
    return None


def parse_env(text: str) -> dict[str, str]:
    out = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        elif " #" in val:
            val = val.split(" #", 1)[0].rstrip()
        if key:
            out[key] = val
    return out


def load_env(explicit: Optional[str] = None) -> Optional[Path]:
    """Load .env into os.environ without overriding variables that are already set."""
    path = find_env_file(explicit)
    if path is None:
        return None
    for k, v in parse_env(path.read_text(encoding="utf-8")).items():
        if v and not os.environ.get(k):
            os.environ[k] = v
    return path