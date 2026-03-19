#!/usr/bin/env bash
# Run this on the Raspberry Pi to set up both services.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STEMS_DIR="$HOME/wavdash-stems"

echo "=== WavDash Stem Mixer Setup ==="

# Create stems directory
mkdir -p "$STEMS_DIR/songs"
echo "Created $STEMS_DIR"

# Set up receiver venv
echo "Setting up receiver..."
cd "$REPO_DIR/receiver"
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Set up player venv
echo "Setting up player..."
cd "$REPO_DIR/player"
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Install systemd services
echo "Installing systemd services..."
sudo cp "$REPO_DIR/deploy/wavdash-receiver.service" /etc/systemd/system/
sudo cp "$REPO_DIR/deploy/wavdash-player.service" /etc/systemd/system/
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
