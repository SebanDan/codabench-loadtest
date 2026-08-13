---
title: What an actual load test can finds out?
parent: Deploying on the cloud
nav_order: 4
---

In this section we will detail the findings of a real load-test. This test was conducted on our own codabench platform deployed with the infrastructure detail on the ![Deploy codabench on AWS]({{ '/cloud/aws/codabench.md' | relative_url }}) section.

It used the following locust configuration:

headless = true
users = 300
spawn-rate = 10
run-time = 30m
tags = ["normal", "clumsy"]
competitions = ["EGG2025"]

## Findings

### CPU / GPU Usage

During the test, the CPU usage was at 100% for each container create by the worker while only one GPU was used at around 40%.
To mitigate this issue, be sure to explicitly set the number of cpu available in the `docker-compose.yml` worker file and indicate the GPU available for each worker.

Voici la configuration docker utilisée positionnant 2 worker:

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
  shm_size: '1024gb'
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

### Codabench Database: Postgres maximum connection limit

During the run we observed the following error:

`connection to server at "db" (x.x.x.xz), port 5432 failed: FATAL:  sorry, too many clients already`

Resulting in an `Error 500` page displayed on the codabench website.

In order to fix this issue, we increased the value of `max_connections` in the postgres configuration file on the codabench instance.

***Note: Depending on the number of concurrent user, this issue might still appear.***

### Codabench Front: Competition missing

During the loadtesting, the competition we were testing could not be reach from the front page. Displaying an `Error 500` message when clicked. This was caused by a bad link with a mission `/` at the end of the URL.

When reached from the search field, the link was correct and the competition could be accessed.
