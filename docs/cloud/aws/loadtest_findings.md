---
title: What an actual load test can finds out?
parent: Deploying on the cloud
nav_order: 4
---

In this section we will detail the findings of a real load-test. This test was conducted on our own codabench platform deployed with the infrastructure detail on the [Deploy codabench on AWS]({{ site.baseurl }}/cloud/aws/codabench') section.

It used the following locust configuration:

```.env
headless = true
users = 300
spawn-rate = 10
run-time = 30m
tags = ["normal", "clumsy"]
competitions = ["EGG2025"]
```

**We used a total of 8 worker containers on the same AWS EC2 p4d.24xlarge. Which means we were able to evaluate 8 submission at the same time.**

## Findings

Overall the platform seems to have the ability to sustain the load. However, our codabench platform configuration might not be optimal resulting in submissions taking a lot of time to be evaluated (~10-20min per submission) depending on the queue. We also observed some failure that we will address here.

During the load testing we used the following submission bundle types:

- Classical bundle: A bundle that fit & predict the model as expected 
- Heavy CPU load bundle: Apply the classical bundle computation and add the compute of PI to the 10_000_000 digits.

At the end of the several load-testing runs we observed a compute time of ~5min for the classical bundle.

### CPU / GPU Usage

During the test, the CPU usage was at 100% for each container create by the worker while only one GPU was used at around 40%.
To mitigate this issue, be sure to explicitly set the number of cpu available in the `docker-compose.yml` worker file and indicate the GPU available for each worker.

Here is the docker configuration used with 2 workers:

```yml
x-worker-base: &worker-base
  image: codalab/codabench-compute-worker:latest
  volumes:
    - /codabench:/codabench
    - /var/run/docker.sock:/var/run/docker.sock
  env_file:
    - .env
  environment:
    - CELERY_CONCURRENCY=1
  restart: unless-stopped
  logging:
    options:
      max-size: 50m
      max-file: 3
  shm_size: '128gb'
  cpus: "96.0"

services:
  worker-gpu-0:
    <<: *worker-base
    environment:
      - GPU_DEVICE=nvidia.com/gpu=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
              capabilities: [gpu]

  worker-gpu-1:
    <<: *worker-base
    environment:
      - GPU_DEVICE=nvidia.com/gpu=1
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']
              capabilities: [gpu]
```

***Note: At this point the bottleneck here is the CPU usage more that the GPU. So, we optimised the competition `ingestion_program` by replacing the `iterrows` statements by pandas vectorised computation.***

### Codabench Database: Postgres maximum connection limit

During the run we observed the following error:

`connection to server at "db" (x.x.x.x), port 5432 failed: FATAL:  sorry, too many clients already`

Resulting in an `Error 500` page displayed on the codabench website.

In order to fix this issue, we increased the value of `max_connections` in the postgres configuration file on the codabench instance.

***Note: Depending on the number of concurrent user, this issue might still appear.***

### Submission Failed

### Timeout

During the execution of long running submission that requires heavy CPU compute (here, the compute of PI), we observed several timeout from the worker. Raising the follow error message:

```bash
Soft time limit (1260s) exceeded for compute_worker_run[xxxx-xxxx-xxxx-xxxx]
2026-08-14 05:13:16.289 | ERROR    | compute_worker:_run_container_engine_cmd:980 - SoftTimeLimitExceeded()
```

To mitigate this issue, one should extend the soft time limit or allow more worker concurrency.

### Codabench Front: Competition missing

(Might not be related to the loudest but only the platform settings)

During the loadtesting, the competition we were testing could not be reach from the front page. Displaying an `Error 500` message when clicked. This was caused by a bad link with a mission `/` at the end of the URL.

When reached from the search field, the link was correct and the competition could be accessed.

### Reports

Here you can consult the reports gathered from several loadtest sessions.

***Note: As the locust runs stop after 30 minutes, all the submissions are not fully monitored. However, the submissions evaluated after the end of the locust process keep the same behaviour. (e.g what was failing before is still failing and so on)***

## Rapport v1 — 250 users, 10 spawn-rate, 30min

<iframe src="{{ site.baseurl }}/cloud/aws/execution_results/report-v1-250-10-30.html" 
        width="100%" height="800px" frameborder="0">
</iframe>

## Rapport v1 — 250 users, 10 spawn-rate, 30min

<iframe src="{{ site.baseurl }}/cloud/aws/execution_results/report-v2-250-10-30.html" 
        width="100%" height="800px" frameborder="0">
</iframe>

## Rapport: 300 users, 10 spawn-rate, 30min

<iframe src="{{ site.baseurl }}/cloud/aws/execution_results/report-v1-300-10-30.html" 
        width="100%" height="800px" frameborder="0">
</iframe>

## Rapport: 500 users, 10 spawn-rate, 30min

<iframe src="{{ site.baseurl }}/cloud/aws/execution_results/report-v1-500-10-30.html" 
        width="100%" height="800px" frameborder="0">
</iframe>