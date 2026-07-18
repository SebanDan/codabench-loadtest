"""Launcher that runs Locust against the host defined in .github/env/<env>.env."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
ENV_DIR = ROOT / ".github" / "env"
LOCUST_FILE = Path(__file__).resolve().parent / "scenarios" / "main.py"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Locust with the host from .github/env/<env>.env.",
    )
    parser.add_argument(
        "--env",
        default=os.environ.get("ENV", "dev"),
        help="Environment name matching .github/env/<env>.env (default: dev).",
    )
    args, locust_args = parser.parse_known_args()

    env_file = ENV_DIR / f"{args.env}.env"
    if not env_file.is_file():
        parser.error(f"Env file not found: {env_file}")

    env = os.environ.copy()
    env.update({k: v for k, v in dotenv_values(env_file).items() if v is not None})

    host = env.get("DJANGO_HOST")
    if not host:
        parser.error(f"DJANGO_HOST is not defined in {env_file}")

    cmd = ["locust", "-f", str(LOCUST_FILE), "--host", host, *locust_args]
    print(f"[{args.env}] launching: {' '.join(cmd)}", file=sys.stderr)
    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
