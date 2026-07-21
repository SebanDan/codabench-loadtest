# codabench-loadtest

[![CI](https://github.com/SebanDan/codabench-loadtest/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SebanDan/codabench-loadtest/actions/workflows/ci.yml)

This repository provides load testing scenarios for the codabench platform based on locust.

## Prerequisites

- [Python 3.13](https://www.python.org/downloads/release/python-3130/) installed
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed
- Install all the dependencies in a virtual environment using `uv sync`
- Requires an admin account on the codabench instance to run the tests

## Project structure

```markdown
codabench-loadtest/
├── codabench_loadtest/
│   ├── locustfile.py            # Entrypoint for the locust tests
│   ├── common/
│   │   ├── api_client.py        # Client dedicated for admin task
│   │   ├── config.py            # Classe used for configuration validation
│   │   └── environment_setup.py # Orchestrate the environment setup (creates the competition and the users)
│   └── scenarios/
│       ├── utils.py             # Helpers (auth, validation de bundle...)
│       └── users/
│           ├── __init__.py
│           ├── smoke_user.py     # Smoke test scenario
│           ├── submitter_user.py # Submission scenario
│           └── clumsy_user.py    # Scenario submit + cancel + re-run
├── data/                        # Competition and submission bundles
├── locust.conf                  # Config Locust (CLI)
├── pyproject.toml
```

## Usage

To run the locust tests, setup your `locust.conf` as well as you `.env` file. 
There is a configuration for locust in the `pyproject.toml` but it do not need to be changed.

Then run :

```bash
uv run locust
```

### How to change the bundles

The assets used to simulate the competition and the submissions are located in the `/data` folder, feel free to add new sassets and modify the configuration file accordingly.

### The scenarios

...
