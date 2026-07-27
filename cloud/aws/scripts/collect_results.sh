#!/bin/bash
set -euo pipefail

# Collect Locust CSV results from all regions into S3, then download locally.
#
# Usage:
#   ./scripts/collect_results.sh <run-name>
#
# Example:
#   ./scripts/collect_results.sh 2026-07-24_peak-test
#
# Prerequisites:
#   - AWS CLI configured with the codabench profile
#   - SSM access to remote instances
#   - Run from the repo root on the Locust master (Paris)

RUN_NAME="${1:?Usage: $0 <run-name>}"
BUCKET="${RESULTS_BUCKET:-codabench-loadtest-results}"
# AWS CLI profile — override with AWS_PROFILE env var if yours differs (e.g. AWS_PROFILE=default)
PROFILE="${AWS_PROFILE:-codabench}"
LOCAL_DIR="runs/${RUN_NAME}"

echo "=== Collecting results for run: ${RUN_NAME} ==="

# --- Step 1: Upload Paris results to S3 ---
echo "[paris] Uploading local CSV results to S3..."
aws s3 cp runs/ "s3://${BUCKET}/paris/${RUN_NAME}/" \
  --recursive --exclude "*" --include "*.csv" \
  --profile "${PROFILE}" 2>/dev/null || echo "[paris] No local CSV files found"

# --- Step 2: Trigger remote instances to push their results to S3 ---
for REGION in us-east ap-southeast; do
  echo "[${REGION}] Sending SSM command to upload results..."

  INSTANCE_IDS=$(aws ec2 describe-instances \
    --profile "${PROFILE}" \
    --region "$(echo "${REGION}" | sed 's/us-east/us-east-1/;s/ap-southeast/ap-southeast-1/')" \
    --filters \
      "Name=tag:Role,Values=locust-worker-remote" \
      "Name=tag:Region,Values=${REGION}" \
      "Name=instance-state-name,Values=running" \
    --query "Reservations[].Instances[].InstanceId" \
    --output text)

  if [ -z "${INSTANCE_IDS}" ]; then
    echo "[${REGION}] No running instances found, skipping."
    continue
  fi

  AWS_REGION="$(echo "${REGION}" | sed 's/us-east/us-east-1/;s/ap-southeast/ap-southeast-1/')"

  aws ssm send-command \
    --profile "${PROFILE}" \
    --region "${AWS_REGION}" \
    --instance-ids ${INSTANCE_IDS} \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[
      'cd /opt/codabench-loadtest',
      'aws s3 cp runs/ s3://${BUCKET}/${REGION}/${RUN_NAME}/ --recursive --exclude \"*\" --include \"*.csv\"'
    ]" \
    --comment "Collect Locust results for ${RUN_NAME}" \
    --output text > /dev/null

  echo "[${REGION}] SSM command sent to: ${INSTANCE_IDS}"
done

# --- Step 3: Wait for uploads, then download everything locally ---
echo ""
echo "Waiting 30s for remote uploads to complete..."
sleep 30

mkdir -p "${LOCAL_DIR}"

for REGION in paris us-east ap-southeast; do
  echo "[${REGION}] Downloading from S3..."
  mkdir -p "${LOCAL_DIR}/${REGION}"
  aws s3 cp "s3://${BUCKET}/${REGION}/${RUN_NAME}/" "${LOCAL_DIR}/${REGION}/" \
    --recursive --profile "${PROFILE}" 2>/dev/null || echo "[${REGION}] No results in S3"
done

echo ""
echo "=== Results collected in ${LOCAL_DIR}/ ==="
find "${LOCAL_DIR}" -name "*.csv" | sort

echo ""
echo "To generate the report:"
echo "  python reports/generate_report.py --regions paris,us-east,ap-southeast --run ${RUN_NAME}"
