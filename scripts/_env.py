"""Tiny .env loader: external tools are located through environment variables."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def require(name, hint):
    load_env()
    value = os.environ.get(name)
    if not value:
        sys.exit(f"{name} is not set ({hint}). Copy .env.example to .env and fill it in.")
    path = Path(value).expanduser()
    if not path.exists():
        sys.exit(f"{name} points to {path}, which does not exist.")
    return path
