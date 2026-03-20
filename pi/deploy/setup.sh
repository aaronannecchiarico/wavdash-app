#!/usr/bin/env bash
# Run this on the Raspberry Pi to set up both services.
# Assumes code has been synced to ~/wavdash/ via `make pi-sync`
# and the shared venv at ~/venv/ already has dependencies installed.
set -euo pipefail

WAVDASH_DIR="$HOME/wavdash"
VENV_DIR="$HOME/env"
STEMS_DIR="$HOME/wavdash-stems"
DEPLOY_DIR="$WAVDASH_DIR/deploy"

echo "=== WavDash Stem Mixer Setup ==="

# Create stems directory
mkdir -p "$STEMS_DIR/songs"
echo "Created $STEMS_DIR"

# Install Python dependencies into shared venv
echo "Installing dependencies into $VENV_DIR..."
"$VENV_DIR/bin/pip" install -r "$WAVDASH_DIR/receiver/requirements.txt"
"$VENV_DIR/bin/pip" install -r "$WAVDASH_DIR/player/requirements.txt"

# Install systemd services
echo "Installing systemd services..."
sudo cp "$DEPLOY_DIR/wavdash-receiver.service" /etc/systemd/system/
sudo cp "$DEPLOY_DIR/wavdash-player.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wavdash-receiver wavdash-player
sudo systemctl start wavdash-receiver
sudo systemctl start wavdash-player

echo ""
echo "=== Setup complete ==="
echo "Receiver: http://$(hostname -I | awk '{print $1}'):9000"
echo "Stems dir: $STEMS_DIR"
echo ""
echo "Check status:"
echo "  sudo systemctl status wavdash-receiver"
echo "  sudo systemctl status wavdash-player"
