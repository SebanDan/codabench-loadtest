#!/bin/bash
set -euo pipefail

# Launch a Locust test across all regions via SSM.
#
# This script:
#   1. Pulls the latest code on all instances (master + workers)
#   2. Restarts Locust master and Paris workers with the requested parameters
#   3. Starts headless runs on remote regions (US East, Asia Pacific)
#
# Usage:
#   ./scripts/run_test.sh [OPTIONS]
#
# Options:
#   --tags TAG          Locust tags to include (normal, clumsy, heavy). Default: normal
#   --users N           Number of simulated users. Default: 10
#   --spawn-rate N      Users spawned per second. Default: 1
#   --duration TIME     Test duration (e.g. 5m, 1h). Default: 10m
#   --run-name NAME     Name for this run (used in CSV filenames). Default: timestamp
#   --env ENV           Environment file (local or prod). Default: prod
#   --skip-pull         Skip git pull on instances
#   --paris-only        Only run in Paris (skip remote regions)
#   --branch BRANCH     Git branch to checkout before pulling. Default: current branch
#
# Prerequisites:
#   - AWS CLI configured with the codabench profile
#   - Terraform deployed (infra/load-generators)
#   - Run from the repo root

# AWS CLI profile — override with AWS_PROFILE env var if yours differs (e.g. AWS_PROFILE=default)
PROFILE="${AWS_PROFILE:-codabench}"
TF_DIR="infra/load-generators"

# --- Defaults ---
TAGS="normal"
USERS=10
SPAWN_RATE=1
DURATION="10m"
RUN_NAME="$(date +%Y-%m-%d_%H%M%S)"
ENV="prod"
SKIP_PULL=false
PARIS_ONLY=false
BRANCH=""

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case $1 in
    --tags)        TAGS="$2"; shift 2 ;;
    --users)       USERS="$2"; shift 2 ;;
    --spawn-rate)  SPAWN_RATE="$2"; shift 2 ;;
    --duration)    DURATION="$2"; shift 2 ;;
    --run-name)    RUN_NAME="$2"; shift 2 ;;
    --env)         ENV="$2"; shift 2 ;;
    --skip-pull)   SKIP_PULL=true; shift ;;
    --paris-only)  PARIS_ONLY=true; shift ;;
    --branch)      BRANCH="$2"; shift 2 ;;
    -h|--help)
      sed -n '3,/^$/p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# --- Resolve Terraform outputs ---
echo "=== Reading Terraform outputs ==="
MASTER_ID=$(terraform -chdir="$TF_DIR" output -raw paris_locust_master_id)
ALB_DNS=$(terraform -chdir="$TF_DIR" output -raw codabench_alb_dns)

echo "  Master:   ${MASTER_ID}"
echo "  ALB:      ${ALB_DNS}"
echo "  Tags:     ${TAGS}"
echo "  Users:    ${USERS}"
echo "  Duration: ${DURATION}"
echo "  Run:      ${RUN_NAME}"
echo ""

# --- Helper: send SSM command and wait ---
ssm_run() {
  local instance_id="$1"
  local region="$2"
  local comment="$3"
  shift 3
  local commands="$*"

  local cmd_id
  cmd_id=$(aws ssm send-command \
    --profile "${PROFILE}" \
    --region "${region}" \
    --instance-ids "${instance_id}" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"${commands}\"]" \
    --comment "${comment}" \
    --timeout-seconds 60 \
    --query "Command.CommandId" \
    --output text)

  echo "  Sent command ${cmd_id} to ${instance_id} (${comment})"
}

ssm_run_and_wait() {
  local instance_id="$1"
  local region="$2"
  local comment="$3"
  shift 3
  local commands="$*"

  local cmd_id
  cmd_id=$(aws ssm send-command \
    --profile "${PROFILE}" \
    --region "${region}" \
    --instance-ids "${instance_id}" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"${commands}\"]" \
    --comment "${comment}" \
    --timeout-seconds 120 \
    --query "Command.CommandId" \
    --output text)

  echo "  Waiting for command ${cmd_id} on ${instance_id}..."
  aws ssm wait command-executed \
    --profile "${PROFILE}" \
    --region "${region}" \
    --command-id "${cmd_id}" \
    --instance-id "${instance_id}" 2>/dev/null || true
}

# --- Helper: get instance IDs from ASG ---
get_asg_instances() {
  local asg_name="$1"
  local region="$2"

  aws autoscaling describe-auto-scaling-groups \
    --profile "${PROFILE}" \
    --region "${region}" \
    --auto-scaling-group-names "${asg_name}" \
    --query "AutoScalingGroups[0].Instances[?LifecycleState=='InService'].InstanceId" \
    --output text
}

# --- Step 1: Git pull on all instances ---
if [ "${SKIP_PULL}" = false ]; then
  echo "=== Pulling latest code ==="

  GIT_CMD="cd /opt/codabench-loadtest"
  if [ -n "${BRANCH}" ]; then
    GIT_CMD="${GIT_CMD} && git fetch origin && git checkout ${BRANCH} && git pull origin ${BRANCH}"
  else
    GIT_CMD="${GIT_CMD} && git pull"
  fi
  GIT_CMD="${GIT_CMD} && /root/.local/bin/uv sync"

  ssm_run_and_wait "${MASTER_ID}" "eu-west-1" "git-pull-master" "${GIT_CMD}"

  PARIS_ASG=$(terraform -chdir="$TF_DIR" output -raw paris_workers_asg)
  PARIS_WORKERS=$(get_asg_instances "${PARIS_ASG}" "eu-west-1")

  for wid in ${PARIS_WORKERS}; do
    ssm_run_and_wait "${wid}" "eu-west-1" "git-pull-worker" "${GIT_CMD}"
  done

  echo "  Done."
  echo ""
fi

# --- Step 2: Stop any running Locust processes ---
echo "=== Stopping existing Locust processes ==="
KILL_CMD="pkill -f 'locust' || true"

ssm_run "${MASTER_ID}" "eu-west-1" "stop-locust-master" "${KILL_CMD}"

PARIS_ASG=$(terraform -chdir="$TF_DIR" output -raw paris_workers_asg)
PARIS_WORKERS=$(get_asg_instances "${PARIS_ASG}" "eu-west-1")
for wid in ${PARIS_WORKERS}; do
  ssm_run "${wid}" "eu-west-1" "stop-locust-worker" "${KILL_CMD}"
done

sleep 3
echo "  Done."
echo ""

# --- Step 3: Start Locust master ---
echo "=== Starting Locust master ==="
MASTER_CMD="cd /opt/codabench-loadtest && /root/.local/bin/uv run locust \
  -f codabench_loadtest/locustfile.py \
  --master \
  --tags ${TAGS} \
  --env ${ENV} \
  --host http://${ALB_DNS} \
  --expect-workers \$(echo '${PARIS_WORKERS}' | wc -w | tr -d ' ') \
  --csv runs/${RUN_NAME}_paris \
  &>> /var/log/locust.log &"

ssm_run "${MASTER_ID}" "eu-west-1" "start-locust-master" "${MASTER_CMD}"
sleep 2
echo "  Done."
echo ""

# --- Step 4: Start Paris workers ---
echo "=== Starting Paris workers ==="
for wid in ${PARIS_WORKERS}; do
  MASTER_IP=$(terraform -chdir="$TF_DIR" output -raw paris_locust_master_ip)
  WORKER_CMD="cd /opt/codabench-loadtest && /root/.local/bin/uv run locust \
    -f codabench_loadtest/locustfile.py \
    --worker \
    --master-host ${MASTER_IP} \
    --tags ${TAGS} \
    --env ${ENV} \
    --host http://${ALB_DNS} \
    &>> /var/log/locust.log &"

  ssm_run "${wid}" "eu-west-1" "start-locust-worker" "${WORKER_CMD}"
done
echo "  Done."
echo ""

# --- Step 5: Start remote regions (headless, independent) ---
if [ "${PARIS_ONLY}" = false ]; then
  echo "=== Starting remote regions ==="

  for REGION_PAIR in "us-east-1:us_east" "ap-southeast-1:ap_southeast"; do
    AWS_REGION="${REGION_PAIR%%:*}"
    TF_KEY="${REGION_PAIR##*:}"
    SHORT_NAME="${TF_KEY//_/-}"

    REMOTE_ASG=$(terraform -chdir="$TF_DIR" output -raw "${TF_KEY}_workers_asg")
    REMOTE_WORKERS=$(get_asg_instances "${REMOTE_ASG}" "${AWS_REGION}")

    if [ -z "${REMOTE_WORKERS}" ]; then
      echo "  [${SHORT_NAME}] No running instances, skipping."
      continue
    fi

    for wid in ${REMOTE_WORKERS}; do
      if [ "${SKIP_PULL}" = false ]; then
        GIT_CMD="cd /opt/codabench-loadtest && git pull && /root/.local/bin/uv sync"
        ssm_run_and_wait "${wid}" "${AWS_REGION}" "git-pull-${SHORT_NAME}" "${GIT_CMD}"
      fi

      REMOTE_CMD="cd /opt/codabench-loadtest && pkill -f 'locust' || true && sleep 2 && /root/.local/bin/uv run locust \
        -f codabench_loadtest/locustfile.py \
        --host http://${ALB_DNS} \
        --headless \
        --tags ${TAGS} \
        --env ${ENV} \
        --users ${USERS} \
        --spawn-rate ${SPAWN_RATE} \
        --run-time ${DURATION} \
        --csv runs/${RUN_NAME}_${SHORT_NAME} \
        &>> /var/log/locust.log &"

      ssm_run "${wid}" "${AWS_REGION}" "start-locust-${SHORT_NAME}" "${REMOTE_CMD}"
    done

    echo "  [${SHORT_NAME}] Started on: ${REMOTE_WORKERS}"
  done
  echo ""
fi

# --- Done ---
echo "=== Test launched ==="
echo ""
echo "Paris master UI (via SSM port forwarding):"
echo "  aws ssm start-session \\"
echo "    --target ${MASTER_ID} \\"
echo "    --document-name AWS-StartPortForwardingSession \\"
echo "    --parameters '{\"portNumber\":[\"8089\"],\"localPortNumber\":[\"8089\"]}' \\"
echo "    --profile ${PROFILE}"
echo ""
echo "  Then open http://localhost:8089"
echo "  Configure: ${USERS} users, spawn rate ${SPAWN_RATE}, duration ${DURATION}"
echo ""
echo "Collect results when done:"
echo "  ./scripts/collect_results.sh ${RUN_NAME}"
