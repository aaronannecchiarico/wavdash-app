# WavDash VPS Provisioning Runbook

One-time setup for the Hetzner production server.

## Prerequisites

- Hetzner Cloud account
- Cloudflare account (with wavdash.com added)
- GitHub repo access (for deploy key)
- Local SSH key pair for the deploy user

## Step 1: Provision Hetzner VPS

1. Log into Hetzner Cloud Console
2. Create server:
   - **Location:** Ashburn, VA (or closest to your users)
   - **Image:** Ubuntu 24.04
   - **Type:** CX32 (4 vCPU, 8GB RAM, 80GB disk)
   - **SSH Key:** Add your public key
   - **Name:** `wavdash-prod`
3. Note the public IP address: `<VPS_IP>`

## Step 2: Initial Server Setup

SSH in as root:

```bash
ssh root@<VPS_IP>
```

Create deploy user and lock down SSH:

```bash
# Create deploy user
adduser --disabled-password --gecos "" deploy
usermod -aG sudo deploy

# Set up SSH key for deploy user
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Disable root login and password auth
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
```

## Step 3: Install Docker

```bash
# As deploy user
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy

# Log out and back in for group change
exit
```

SSH back in as deploy:

```bash
ssh deploy@<VPS_IP>
docker --version  # Verify
```

## Step 4: Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
```

## Step 5: Configure Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

## Step 6: Cloudflare Origin Certificate

1. In Cloudflare dashboard -> SSL/TLS -> Origin Server
2. Click "Create Certificate"
3. Hostnames: `*.wavdash.com, wavdash.com`
4. Validity: 15 years
5. Key format: PEM
6. Copy the certificate and private key

Install on VPS:

```bash
sudo mkdir -p /etc/ssl/cloudflare

# Paste the certificate
sudo nano /etc/ssl/cloudflare/wavdash.com.pem

# Paste the private key
sudo nano /etc/ssl/cloudflare/wavdash.com.key

sudo chmod 600 /etc/ssl/cloudflare/wavdash.com.key
```

## Step 7: Configure Nginx

```bash
# Clone repo first (Step 8), then symlink configs:
sudo ln -sf /opt/wavdash/deploy/nginx/wavdash.com.conf /etc/nginx/sites-enabled/
sudo ln -sf /opt/wavdash/deploy/nginx/app.wavdash.com.conf /etc/nginx/sites-enabled/
sudo ln -sf /opt/wavdash/deploy/nginx/ws.wavdash.com.conf /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## Step 8: Clone Repository

```bash
# Generate deploy key (or use existing)
ssh-keygen -t ed25519 -f ~/.ssh/wavdash_deploy -N ""
cat ~/.ssh/wavdash_deploy.pub
# Add this public key as a Deploy Key in GitHub repo settings (read-only)

# Clone
sudo mkdir -p /opt/wavdash
sudo chown deploy:deploy /opt/wavdash
GIT_SSH_COMMAND="ssh -i ~/.ssh/wavdash_deploy" git clone git@github.com:<org>/wavdash-monorepo.git /opt/wavdash

# Configure git to use deploy key
git config --global core.sshCommand "ssh -i ~/.ssh/wavdash_deploy"
```

## Step 9: Create Production .env

```bash
cd /opt/wavdash
cp .env.production.example .env
nano .env  # Fill in all values
```

Required values to fill in:
- `APP_KEY` — generate with `docker run --rm -it wavdash_app php artisan key:generate --show` (after first build)
- `DB_PASSWORD` — generate a strong password
- `R2_*` — copy from your Cloudflare R2 dashboard
- `REVERB_*` — copy from `app/.env` or generate new ones
- `SUPER_USER_PASSWORD` — strong admin password
- `ADMIN_ALLOWED_IPS` — your home/office IP

## Step 10: Build and Start

```bash
cd /opt/wavdash
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Generate APP_KEY if you haven't yet
docker exec wavdash_app php artisan key:generate --show
# Add the key to .env, then restart:
# docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Run migrations and seed
docker exec wavdash_app php artisan migrate --force
docker exec wavdash_app php artisan db:seed --force
```

## Step 11: Configure Cloudflare DNS

1. In Vercel: change wavdash.com nameservers to Cloudflare's (shown in Cloudflare dashboard)
2. In Cloudflare dashboard -> DNS:
   - A record: `wavdash.com` -> `<VPS_IP>` (Proxied)
   - A record: `app` -> `<VPS_IP>` (Proxied)
   - A record: `ws` -> `<VPS_IP>` (Proxied)
3. SSL/TLS -> set to "Full (strict)"
4. Wait for DNS propagation (usually < 5 minutes with Cloudflare)

## Step 12: Configure GitHub Secrets

In GitHub repo -> Settings -> Secrets and variables -> Actions:

| Secret | Value |
|--------|-------|
| `VPS_HOST` | `<VPS_IP>` |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | Contents of the deploy SSH private key |
| `PROD_ENV_FILE` | Contents of `/opt/wavdash/.env` |

Also create a GitHub Environment called `production` (Settings -> Environments) for the deploy job.

## Step 13: Verify

```bash
# On VPS — check all containers
docker ps

# Health checks
curl -s http://127.0.0.1:8000/up
curl -s http://127.0.0.1:8001/health
curl -s http://127.0.0.1:4321

# From your machine — check public URLs
curl -s https://wavdash.com
curl -s https://app.wavdash.com/up
```

## Maintenance

### View logs
```bash
cd /opt/wavdash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### Manual deploy
```bash
cd /opt/wavdash
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker exec wavdash_app php artisan migrate --force
```

### Rollback
```bash
cd /opt/wavdash
git log --oneline -5  # Find the commit to roll back to
git checkout <sha>
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Database backup (manual)
```bash
docker exec wavdash_mysql mysqldump -u wavdash -p wavdash > /tmp/wavdash_backup_$(date +%Y%m%d).sql
```
