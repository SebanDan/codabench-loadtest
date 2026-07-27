#!/bin/bash
set -euo pipefail

# Stop all running Locust processes across all regions via SSM.
#
# Usage:
#   ./scripts/stop_test.sh [OPTIONS]
#
# Options:
#   --paris-only   Only stop Paris instances (skip remote regions)
#
# Prerequisites:
#   - AWS CLI configured with the codabench profile
#   - Terraform deployed (infra/load-generators)
#   - Run from the repo root

# AWS CLI profile — override with AWS_PROFILE env var if yours differs (e.g. AWS_PROFILE=default)
PROFILE="${AWS_PROFILE:-codabench}"
TF_DIR="infra/load-generators"
PARIS_ONLY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --paris-only) PARIS_ONLY=true; shift ;;
    -h|--help)
      sed -n '3,/^$/p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

ssm_run() {
  local instance_id="$1"
  local region="$2"
  local comment="$3"
  shift 3
  local commands="$*"

  aws ssm send-command \
    --profile "${PROFILE}" \
    --region "${region}" \
    --instance-ids "${instance_id}" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"${commands}\"]" \
    --comment "${comment}" \
    --timeout-seconds 30 \
    --output text > /dev/null

  echo "  Stopped Locust on ${instance_id}"
}

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

KILL_CMD="pkill -f 'locust' || true"

# --- Paris ---
echo "=== Stopping Paris ==="
MASTER_ID=$(terraform -chdir="$TF_DIR" output -raw paris_locust_master_id)
ssm_run "${MASTER_ID}" "eu-west-1" "stop-master" "${KILL_CMD}"

PARIS_ASG=$(terraform -chdir="$TF_DIR" output -raw paris_workers_asg)
PARIS_WORKERS=$(get_asg_instances "${PARIS_ASG}" "eu-west-1")
for wid in ${PARIS_WORKERS}; do
  ssm_run "${wid}" "eu-west-1" "stop-worker" "${KILL_CMD}"
done

# --- Remote regions ---
if [ "${PARIS_ONLY}" = false ]; then
  for REGION_PAIR in "us-east-1:us_east" "ap-southeast-1:ap_southeast"; do
    AWS_REGION="${REGION_PAIR%%:*}"
    TF_KEY="${REGION_PAIR##*:}"
    SHORT_NAME="${TF_KEY//_/-}"

    echo "=== Stopping ${SHORT_NAME} ==="

    REMOTE_ASG=$(terraform -chdir="$TF_DIR" output -raw "${TF_KEY}_workers_asg")
    REMOTE_WORKERS=$(get_asg_instances "${REMOTE_ASG}" "${AWS_REGION}")

    if [ -z "${REMOTE_WORKERS}" ]; then
      echo "  No running instances."
      continue
    fi

    for wid in ${REMOTE_WORKERS}; do
      ssm_run "${wid}" "${AWS_REGION}" "stop-${SHORT_NAME}" "${KILL_CMD}"
    done
  done
fi

echo ""
echo "=== All Locust processes stopped ==="
