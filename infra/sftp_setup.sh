#!/usr/bin/env bash
# =============================================================================
# sftp_setup.sh
# Configures the EFF SFTP VM: installs gcsfuse, mounts gs://eff-xml-feeds,
# creates the 'opta' SFTP-only user, and sets up OpenSSH chroot.
#
# Run ON the VM as root after creation:
#   sudo bash ~/sftp_setup.sh <opta-password>
# =============================================================================
set -euo pipefail

BUCKET="eff-xml-feeds"
SFTP_USER="opta"
CHROOT_DIR="/srv/sftp"
FEEDS_DIR="${CHROOT_DIR}/feeds"

# ---------------------------------------------------------------------------
# 0. Require a password argument
# ---------------------------------------------------------------------------
if [[ $# -lt 1 ]]; then
  echo "Usage: sudo bash sftp_setup.sh <opta-password>"
  exit 1
fi
SFTP_PASS="$1"

# ---------------------------------------------------------------------------
# 1. Install gcsfuse
# ---------------------------------------------------------------------------
echo "==> [1/6] Installing gcsfuse ..."
CODENAME=$(lsb_release -cs)
echo "deb https://packages.cloud.google.com/apt gcsfuse-${CODENAME} main" \
  > /etc/apt/sources.list.d/gcsfuse.list
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | gpg --dearmor -o /etc/apt/trusted.gpg.d/cloud-google.gpg
apt-get update -q
apt-get install -y gcsfuse

# Allow non-root users to see FUSE mounts mounted by root
echo "user_allow_other" >> /etc/fuse.conf

# ---------------------------------------------------------------------------
# 2. Create chroot directory structure
# ---------------------------------------------------------------------------
echo "==> [2/6] Creating chroot structure ..."
mkdir -p "$FEEDS_DIR"
# sshd requires ChrootDirectory to be owned by root, not writable by others
chown root:root "$CHROOT_DIR"
chmod 755 "$CHROOT_DIR"
# opta user owns the feeds subdirectory (gcsfuse will present files as this owner)
chown root:root "$FEEDS_DIR"  # will be re-owned after useradd

# ---------------------------------------------------------------------------
# 3. Create the SFTP user
# ---------------------------------------------------------------------------
echo "==> [3/6] Creating user '${SFTP_USER}' ..."
useradd --no-create-home --shell /usr/sbin/nologin "$SFTP_USER" || \
  echo "  (user already exists, updating password)"
echo "${SFTP_USER}:${SFTP_PASS}" | chpasswd

# Now set feeds dir ownership to the new user
chown "${SFTP_USER}:${SFTP_USER}" "$FEEDS_DIR"
chmod 755 "$FEEDS_DIR"

OPTA_UID=$(id -u "$SFTP_USER")
OPTA_GID=$(id -g "$SFTP_USER")

# ---------------------------------------------------------------------------
# 4. Mount GCS bucket with gcsfuse
# ---------------------------------------------------------------------------
echo "==> [4/6] Mounting gs://${BUCKET} at ${FEEDS_DIR} ..."
gcsfuse \
  --uid="${OPTA_UID}" \
  --gid="${OPTA_GID}" \
  --file-mode=644 \
  --dir-mode=755 \
  -o allow_other \
  --implicit-dirs \
  "$BUCKET" "$FEEDS_DIR"

echo "  Mount OK. Contents:"
ls -la "$FEEDS_DIR"

# ---------------------------------------------------------------------------
# 5. systemd unit — remount on reboot
# ---------------------------------------------------------------------------
echo "==> [5/6] Installing gcsfuse systemd service ..."
cat > /etc/systemd/system/gcsfuse-sftp.service << EOF
[Unit]
Description=GCSFuse mount for OPTA SFTP feeds (gs://${BUCKET})
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
ExecStart=/usr/bin/gcsfuse \\
  --uid=${OPTA_UID} \\
  --gid=${OPTA_GID} \\
  --file-mode=644 \\
  --dir-mode=755 \\
  -o allow_other \\
  --implicit-dirs \\
  ${BUCKET} ${FEEDS_DIR}
ExecStop=/bin/fusermount -u ${FEEDS_DIR}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable gcsfuse-sftp
echo "  Service enabled."

# ---------------------------------------------------------------------------
# 6. Configure OpenSSH: SFTP-only chroot for 'opta'
# ---------------------------------------------------------------------------
echo "==> [6/6] Configuring sshd ..."

# Ensure PasswordAuthentication is not globally off (Debian 12 default is yes,
# but some cloud images disable it)
if grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config; then
  sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
fi

# Append Match block if not already present
if ! grep -q "Match User ${SFTP_USER}" /etc/ssh/sshd_config; then
  cat >> /etc/ssh/sshd_config << EOF

# SFTP-only chroot for OPTA feed uploads
Match User ${SFTP_USER}
    ForceCommand internal-sftp
    ChrootDirectory ${CHROOT_DIR}
    PasswordAuthentication yes
    PermitTunnel no
    AllowAgentForwarding no
    AllowTcpForwarding no
    X11Forwarding no
EOF
fi

sshd -t && systemctl restart sshd
echo "  sshd restarted OK."

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
EXTERNAL_IP=$(curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)

echo ""
echo "============================================================"
echo "  SFTP setup complete"
echo "============================================================"
echo "  Host:     ${EXTERNAL_IP}"
echo "  Port:     22"
echo "  User:     ${SFTP_USER}"
echo "  Password: ${SFTP_PASS}"
echo "  Path:     /feeds"
echo "============================================================"
echo ""
echo "Test with:"
echo "  sftp ${SFTP_USER}@${EXTERNAL_IP}"
echo "  sftp> ls /feeds"
