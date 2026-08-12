---
title: What an actual load test can finds out?
parent: Deploying on the cloud
nav_order: 4
---

In this section we will detail the findings of a real load-test. This test was conducted on our own codabench platform deployed with the infrastructure detail on the ![Deploy codabench on AWS]({{ '/cloud/aws/codabench.md' | relative_url }}) section.

It used the following locust configuration:

headless = true
users = 500
spawn-rate = 10
run-time = 1h
tags = ["normal", "clumsy"]
competitions = ["EGG2025"]

## Findings

### Codabench postgres maximum connection limit

During the run we observed the following error:

`connection to server at "db" (x.x.x.xz), port 5432 failed: FATAL:  sorry, too many clients already`

Resulting in an `Error 500` page displayed on the codabench website.

In order to fix this issue, we increased the value of `max_connections` in the postgres configuration file on the codabench instance.
