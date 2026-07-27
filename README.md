# codabench-loadtest

[![CI](https://github.com/SebanDan/codabench-loadtest/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SebanDan/codabench-loadtest/actions/workflows/ci.yml) [![Python versions](https://img.shields.io/badge/python-3.13-blue)](https://docs.python.org/3/whatsnew/)

This repository provides load testing scenarios for the codabench platform based on [Locust](https://locust.io).

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
│   │   ├── rabbitmq_monitor.py  # RabbitMQ queue depth/memory monitoring
│   │   └── environment_setup.py # Orchestrate the environment setup (creates the competition and the users)
│   └── scenarios/
│       ├── utils.py             # Helpers (auth, validation de bundle...)
│       └── users/
│           ├── smoke_user.py     # Smoke test scenario
│           ├── submitter_user.py # Submission scenario
│           └── clumsy_user.py    # Scenario submit + cancel + re-run
├── data/                        # Competition and submission bundles
├── .github/env/
│   ├── .env.example             # Template for environment variables
│   └── prod.env                 # Auto-generated on instances by user-data
├── infra/load-generators/       # Terraform for Locust infra (3 regions)
├── scripts/                     # SSM-based test orchestration (run/stop/collect)
├── docs/                        # Test methodology and steps
├── locust.conf                  # Config Locust (CLI)
├── pyproject.toml
```

## AWS Infrastructure

The load-generator infrastructure is managed by Terraform in `infra/load-generators/`. It provisions Locust instances across 3 AWS regions (Paris, US East, Asia Pacific) to simulate geographically distributed users.

Credentials are stored in AWS SSM Parameter Store (no secrets in code):

| Parameter | Type |
|-----------|------|
| `/codabench-loadtest/rabbitmq-user` | String |
| `/codabench-loadtest/rabbitmq-password` | SecureString |
| `/codabench-loadtest/codabench-username` | String |
| `/codabench-loadtest/codabench-password` | SecureString |

Terraform reads these automatically and injects them into `.env` and `.github/env/prod.env` on each instance at boot. See `docs/test_steps.txt` for detailed test procedures.

## Usage

### Local development

```bash
git clone https://github.com/SebanDan/codabench-loadtest.git
cd codabench-loadtest
cp .github/env/.env.example .github/env/local.env
cp locust.example.conf locust.conf
```

Edit `.github/env/local.env` with your Codabench credentials, then:

```bash
uv run locust --env local
```

### On AWS instances

The `prod.env` file is auto-provisioned by user-data at boot. Just run:

```bash
uv run locust --env prod
```

Or use the orchestration scripts:

```bash
./scripts/run_test.sh --tags normal --users 50 --duration 10m
./scripts/stop_test.sh
./scripts/collect_results.sh <run-name>
```

*Note: As the locust test will generate assets on the platform it is required to provide a valid admin username and password in the env file.*

It is possible to filter on a specific user (for instance here the SmokeUser) by running.

```bash
uv run locust SmokeUser
```

### How to manage the bundles ?

The assets used to simulate the competition and the submissions are located in the `/data` folder, feel free to add new sassets and modify the configuration file accordingly.

The submission bundle are located in the `/data/submissions` folder. When lauching the test, this folder will be loaded to generate a `SubmissionPool`. This `SubmissionPool` can be used to manage the bundle differently according to the task before applying the submission.

### Generated assets

When running the locustfile and running the tests, several assets will be gererated on the platform.
Using the competition bundle, locust will generate a new competition and a pool of users. The pool of user will leverage the parameter `users` in the `locust.conf` file and create the same amount on the platform. When running a scenario, locust will authenticate as one of the user in the pool to run the tasks.

At the end of the test, the platform will be cleared by deleting the previously users and the competition.

### The scenarios

This tool support two types of users that answers different scenarios.

1. The smoke test user

This user is used to ensure that locust is working properly. The main task is the consultation of main pages.

2. The submitter user

This user is used to create different kind of submission on the platform by running different tasks.

***Note***: *All the submission task select randomly a submission bundle available in the submission pool allowing all the task to submit classical or heavy compute submission.*

- **submit_task**: This task select a submission bundle available in the submission pool and submit it to the competition. It can be filtered by using the `normal` tag.
- **clumsy_submit_task**: This task select a submission bundle, submit it, cancel it, lauch a new submission and re-run the previously submitted bundle. It can be filtered by using the `clumsy` tag.
- **heavy_submit_task**: This task select a submission bundle and expand it content by 1Go before submitting it. It can be filtered by using the `heavy` tag.

### Reports

At the end of the locust tests, the execution reports can be found in the `/reports` folder. This can be changed in the `pyproject.toml` file.
