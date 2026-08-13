# codabench-loadtest

[![Python versions](https://img.shields.io/badge/python-3.13-blue)](https://docs.python.org/3/whatsnew/) [![CI](https://github.com/SebanDan/codabench-loadtest/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SebanDan/codabench-loadtest/actions/workflows/ci.yml) [![Release](https://github.com/SebanDan/codabench-loadtest/actions/workflows/release.yml/badge.svg)](https://github.com/SebanDan/codabench-loadtest/actions/workflows/release.yml) [![Docs](https://img.shields.io/badge/docs-online-blue)](https://sebandan.github.io/codabench-loadtest/)

This repository provides load testing scenarios for the codabench platform based on [Locust](https://locust.io).

📖 The full documentation is available on [GitHub Pages](https://sebandan.github.io/codabench-loadtest/).

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
│   ├── clients/
│   │   ├── base_api_client.py        # Client dedicated for admin task
│   │   └── locust_api_client.py      # Client dedicated for locust monitoring
│   ├── monitors/
│   │   └── rabbitmq_monitor.py  # RabbitMQ queue depth/memory monitoring
│   ├── setup/
│   │   ├── config.py            # Classe used for configuration validation
│   │   └── environment_setup.py # Orchestrate the environment setup (creates the competition and the users)
│   └── scenarios/
│       └── users/
│           ├── smoke_user.py     # Smoke test scenario
│           ├── submitter_user.py # Submission scenario
│           └── clumsy_user.py    # Scenario submit + cancel + re-run
├── data/                        # Competition and submission bundles
├── .github/env/
│   ├── .env.example             # Template for environment variables
│   └── prod.env                 # Auto-generated on instances by user-data
├── cloud/aws/deploy/            # Terraform for Locust infra (3 regions)
├── cloud/aws/scripts/           # SSM-based test orchestration (run/stop/collect)
├── docs/                        # Methodology and steps
├── locust.conf                  # Config Locust (CLI)
```

## Usage

### Local Installation

```bash
git clone https://github.com/SebanDan/codabench-loadtest.git
cd codabench-loadtest
cp .github/env/.env.example .github/env/local.env
cp locust.example.conf locust.conf
```

Edit `.github/env/<env>.env` with your Codabench credentials.

*Note: As the locust test will need to generate assets on the platform it is required to provide a valid admin username and password in the `.env` file*

When running playright based scenario be sure to run the following command to setup playwright.

```bash
uv run playwright install
````

Then run the following command to execute locust with your configuration:

```bash
uv run locust --env local
```

In order to run a unique type of Scenario run locust with the user classe name. Alternatively, you can create a `user_config.json` file, as supported natively by Locust, more informations can be found on the [locust documentation](https://docs.locust.io/en/stable/configuration.html#configure-users-from-command-line)

```bash
uv run locut --config-users my_user_config.json
uv run locust SubmitterUser
```

### Docker installation (recommended)

This project provides a Dockerfile and a docker-compose.yml file that can be used to deploy the project on any platform.
To proceed, clone the repository and build the image:

```bash
docker compose build --no-cache
```

When you are ready run the container with the provided configuration.

***Note: The container will directly execute locust scenarios based on you configuration, so be sure to setup your environment files accordingly.***

```bash
docker compose up -d
```

This installation mode supports the `master` and `worker` capabilities from locust. The `docker-compose-multi-nodes.example.yml` provides an example to setup this properly.

### Environment variables & locust configuration

This tool can be configured through two configuration file.

**1. locust.conf:**

It supports the usual locust configuration variables documented on the [locust documentation](https://docs.locust.io/en/stable/configuration.html#configuration-file). On top of these, this tool exposes the following variables:

| Variable | Description | Default |
| --- | --- | --- |
| `env` | Name of the environment file to load at runtime (e.g. `local`, `prod`) | `local` |
| `competitions` | Space-separated list of competition names to test, matching the `<COMPETITION_NAME>` folders under `data/`. Omit to run all competitions found. | *(all)* |

**2. `<environment>`.env:**

This file will be loaded at runtime based on the `env` variable. It exposes the following variables:

| Variable | Description | Default | Required |
| --- | --- | --- | --- |
| `CODABENCH_HOST` | Target Codabench instance URL. It will override the host provided by locust| `http://localhost:8000` | Yes |
| `CODABENCH_CADDY_HOSTNAME` | Overrides the HTTP `Host` header when connecting via IP behind Caddy (e.g. `localhost` if Caddy's `DOMAIN_NAME` is `localhost`) | - | No |
| `CODABENCH_API_TOKEN` | API token for authentication (takes priority over username/password if set) | - | No* |
| `CODABENCH_USERNAME` | Username for authentication (used if no API token is set) | - | No* |
| `CODABENCH_PASSWORD` | Password for authentication (used if no API token is set) | - | No* |
| `CODABENCH_POLL_INTERVAL` | Delay (seconds) between submission status polls | `5.0` | No |
| `CODABENCH_POLL_TIMEOUT` | Max time (seconds) to wait for a submission to reach a terminal status | `3600.0` | No |
| `CODABENCH_MAX_RESPONSE_TIME_P95` | Performance threshold: max acceptable p95 response time (seconds) | `2.0` | No |
| `CODABENCH_MAX_ERROR_RATE` | Performance threshold: max acceptable error rate (0–1) | `0.01` | No |
| `CODABENCH_MINIO_ENDPOINT` | MinIO endpoint, for storage monitoring. Required even if MinIO isn't used, provide an empty string ("") in that case | `http://localhost:9000` | Yes |
| `CODABENCH_MINIO_ACCESS_KEY` | MinIO access key | - | No |
| `CODABENCH_MINIO_SECRET_KEY` | MinIO secret key | - | No |
| `CODABENCH_RABBITMQ_URL` | RabbitMQ management URL, for queue monitoring | `http://localhost:15672` | No |
| `CODABENCH_RABBITMQ_USER` | RabbitMQ username | `guest` | No |
| `CODABENCH_RABBITMQ_PASSWORD` | RabbitMQ password | - | No |

### How to manage the bundles ?

The assets used to simulate the competition and the submissions are located in the `/data` folder, feel free to add new sassets and modify the configuration file accordingly.

The **codabench-loadtest** tool supports multiple competition simulation at once.
When lauching the test, this folder will be loaded to generate a `CompetitionPool` that associate each bundle with its submissions, it expect the following `/data` folder structure to load properly and will perform bundle validation at runtime.

```markdown
codabench-loadtest/
├── data/
│   ├── <COMPETITION_1_NAME>
│   │   ├── <COMPETITION_BUNDLE>.zip
│   │   └── submissions/
│   │       ├── <SUBMISSION_EXAMPLE_1>.zip
│   │       └── <SUBMISSION_EXAMPLE_2>.zip
│   ├── <COMPETITION_2_NAME>/
│   │   ├── <COMPETITION_BUNDLE>.zip
│   │   └── submissions/
│   │       ├── <SUBMISSION_EXAMPLE_1>.zip
│   │       └── <SUBMISSION_EXAMPLE_2>.zip
```

***The submission bundles are located in the `/data/<competition_name>/submissions` folder.***

The `CompetitionPool` holds list of `Competition` objects each backed by a `SubmissionPool` that tracks its associated submissions. This `SubmissionPool` can be used to adapt the submission bundles differently per task before applying the submission (for example, generating a large file inside the `.zip` before sending it to the api).

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

3. The UIUser

This user is used to evaluate the codabench UI using `Playwright` and ensure the front is still responding. It can perfom submission to the competition through the UI, but as the `Playwright Browsers` are heavy it is not suited for heavy loadtesting.

### Reports

At the end of the locust tests, the execution reports can be found in the `/reports` folder. This can be changed in the `pyproject.toml` file.
