# codabench-loadtest

[![CI](https://github.com/SebanDan/codabench-loadtest/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SebanDan/codabench-loadtest/actions/workflows/ci.yml) [![Python versions](https://img.shields.io/badge/python-3.13-blue)](https://docs.python.org/3/whatsnew/)

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

```bash
git clone https://github.com/SebanDan/codabench-loadtest.git
cd codabench-loadtest
cp .github/env/.env.example local.env
cp locust.example.conf locust.conf
```

*Note: As the locust test will generate assets on the platform it is required to provide a valid admin username and password in the `.env` file*

Then run :

```bash
uv run locust
```

### How to manage the bundles ?

The assets used to simulate the competition and the submissions are located in the `/data` folder, feel free to add new sassets and modify the configuration file accordingly.

The submission bundle are located in the `/data/submissions` folder. When lauching the test, this folder will be loaded to generate a `SubmissionPool`. This `SubmissionPool` can be used to manage the bundle differently according to the task before applying the submission.

### Generated assets

When running the locustfile and running the tests, several assets while be gererated on the platform.
Using the competition bundle, locust will generate a new competition and a pool of users. The pool of user will leverage the parameter `users` in the `locust.conf` file and create the same amount on the platform. When running a scenario, locust will authenticate as one of the user in the pool to run the tasks.

At the end of the test, the platform will be cleared by deleting the previously users and the competition.

### The scenarios

This tool support two types of users that answers different scenarios.

1. The smoke test user

This user is used to ensure that locust is working properly. The main task is the consultation of main pages.

2. The submitter user

This user is used to create different kind of submission on the platform by running different tasks.

***Note***: *All the submission task select randomly a submission bundle available in the submission pool allowing all the task to submit classical or heavy compute submission.*

- **submit_task**: This task select a submission bundle available in the submission pool and submit it to the competition
- **clumsy_submit_task**: This task select a submission bundle, submit it, cancel it, lauch a new submission and re-run the previously submitted bundle.
- **heavy_submit_task**: This task select a submission bundle and expand it content by 1Go before submitting it.

### Reports

At the end of the locust tests, the execution reports can be found in the `/reports` folder. This can be changed in the `pyproject.toml` file.
