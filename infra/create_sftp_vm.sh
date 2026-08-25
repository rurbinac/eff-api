#!/usr/bin/env bash
# =============================================================================
# create_sftp_vm.sh
# Creates the EFF SFTP VM that receives OPTA XML feeds and writes them to GCS.
#
# Run this ONCE from your local machine (gcloud must be authenticated).
# After it completes, SSH into the VM and run sftp_setup.sh.
# =============================================================================
set -euo pipefail

PROJECT="sublime-scion-499902-m5"
REGION="us-central1"
ZONE="us-central1-a"
VM_NAME="eff-sftp"
BUCKET="eff-xml-feeds"
SA_NAME="sftp-gcs"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"

echo "==> [1/5] Creating service account ${SA_EMAIL} ..."
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="EFF SFTP — GCS feed writer" \
  --project="$PROJECT" 2>/dev/null || echo "  (already exists, skipping)"

echo "==> [2/5] Granting objectAdmin on gs://${BUCKET} ..."
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin" \
  --project="$PROJECT"

echo "==> [3/5] Creating VM ${VM_NAME} (e2-micro, Debian 12) ..."
gcloud compute instances create "$VM_NAME" \
  --project="$PROJECT" \
  --zone="$ZONE" \
  --machine-type="e2-micro" \
  --image-family="debian-12" \
  --image-project="debian-cloud" \
  --service-account="${SA_EMAIL}" \
  --scopes="cloud-platform" \
  --tags="sftp-server" \
  --boot-disk-size="10GB"

echo "==> [4/5] Creating firewall rule (allow TCP 22 to sftp-server tag) ..."
gcloud compute firewall-rules create "allow-sftp" \
  --project="$PROJECT" \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:22 \
  --target-tags="sftp-server" \
  --description="Allow SFTP from anywhere" 2>/dev/null || echo "  (already exists, skipping)"

echo "==> [5/5] Getting external IP ..."
EXTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" \
  --project="$PROJECT" \
  --zone="$ZONE" \
  --format="get(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo "============================================================"
echo "  VM created:  ${VM_NAME}"
echo "  External IP: ${EXTERNAL_IP}"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Copy the setup script to the VM:"
echo "       gcloud compute scp infra/sftp_setup.sh ${VM_NAME}:~ --zone=${ZONE} --project=${PROJECT}"
echo ""
echo "  2. SSH into the VM:"
echo "       gcloud compute ssh ${VM_NAME} --zone=${ZONE} --project=${PROJECT}"
echo ""
echo "  3. On the VM, run (choose a strong password for OPTA):"
echo "       sudo bash ~/sftp_setup.sh <opta-password>"
echo ""
echo "  4. Give OPTA:"
echo "       Host:     ${EXTERNAL_IP}"
echo "       Port:     22"
echo "       User:     opta"
echo "       Password: <the password you chose>"
echo "       Path:     /feeds"
