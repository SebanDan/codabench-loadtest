"""Launcher that runs Locust against the host defined in .github/env/<env>.env."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

from codabench_loadtest.scenarios import EnvironmentSetup
from codabench_loadtest.scenarios.common import Settings

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
ENV_DIR = ROOT_DIR / ".github" / "env"


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

    codabench_settings = Settings(_env_file=env_file)  # type: ignore[call-arg]
    environment = EnvironmentSetup(codabench_settings)
    result = environment.create_competition(
        bundle_path=DATA_DIR / codabench_settings.competition_bundle
    )
    competition_id = result.get("resulting_competition")
    environment.create_user_pools(size=2)
    print(competition_id)

    cmd = ["locust", "--host", codabench_settings.host, *locust_args]
    print(f"[{args.env}] launching: {' '.join(cmd)}", file=sys.stderr)
    subprocess.call(cmd, env=env)

    environment.codabench_client.delete_competition(int(competition_id))


if __name__ == "__main__":
    raise SystemExit(main())
