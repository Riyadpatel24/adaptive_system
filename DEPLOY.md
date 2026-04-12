# 🚀 Deployment Guide — Adaptive System

This guide covers every step to go from zero to a running, production-ready deployment.

---

## Prerequisites

Make sure you have these installed on your server/machine:

| Tool | Version | Check |
|------|---------|-------|
| Docker | 24+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| Git | any | `git --version` |

> For cloud VMs (AWS EC2, GCP, Azure, DigitalOcean): a $5–10/month instance with 1 vCPU and 1GB RAM is enough for this project.

---

## Step 1 — Get the Code

```bash
git clone https://github.com/Riyadpatel24/adaptive_system.git
cd adaptive_system
```

---

## Step 2 — Create Your .env File

```bash
cp .env.example .env
```

Now open `.env` and fill in the values:

```bash
nano .env   # or: vim .env  /  code .env
```

**Minimum required changes:**

```env
API_KEY=replace_this_with_a_long_random_string
SIMULATION_MODE=false
TELEMETRY_MODE=synthetic
```

Generate a strong API key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 3 — Build and Start

```bash
docker compose up --build -d
```

- `--build` rebuilds the image with your latest code
- `-d` runs in the background (detached)

Check it started:
```bash
docker compose ps
docker compose logs -f adaptive-system
```

---

## Step 4 — Verify It's Running

```bash
# Health check (no auth needed)
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# System state (auth required)
curl http://localhost:8000/state \
  -H "X-API-Key: your_api_key_here"

# Interactive API docs
open http://localhost:8000/docs
```

---

## Step 5 — Open the Dashboard

Open `frontend/adaptive-system.html` in your browser.

> If you set an `API_KEY`, you need to add the header to the fetch calls in the HTML file.
> Search for `fetch(` in `frontend/adaptive-system.html` and add:
> ```js
> headers: { "X-API-Key": "your_api_key_here" }
> ```

---

## Step 6 (Optional) — HTTPS with Nginx

For production, put Nginx in front as a reverse proxy with SSL.

**Install Nginx + Certbot:**
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

**Create `/etc/nginx/sites-available/adaptive-system`:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Enable and get SSL:**
```bash
sudo ln -s /etc/nginx/sites-available/adaptive-system /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d yourdomain.com
```

---

## Step 7 (Optional) — Run Tests Before Deploying

```bash
# On your local machine before pushing
pip install -r requirements.txt pytest
pytest tests/test_core.py -v
```

---

## Common Commands

```bash
# View live logs
docker compose logs -f

# Stop the system
docker compose down

# Restart after code changes
docker compose up --build -d

# Shell into the running container
docker exec -it adaptive_system bash

# Check storage volume
docker volume inspect adaptive_system_adaptive_storage
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 already in use | Change `API_PORT` in `.env` |
| `curl` returns 403 | Check your `API_KEY` matches the header value |
| Dashboard shows no data | Confirm API is running: `curl localhost:8000/health` |
| Container keeps restarting | Run `docker compose logs adaptive-system` to see the error |
| `requirements.txt` install fails | Ensure Docker has internet access; check proxy settings |

---

## Cloud Deployment (Quick Reference)

### DigitalOcean Droplet
```bash
# On a fresh Ubuntu 22.04 droplet
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in, then:
git clone https://github.com/Riyadpatel24/adaptive_system.git
cd adaptive_system && cp .env.example .env
# Edit .env, then:
docker compose up --build -d
```

### AWS EC2
- Launch an Ubuntu 22.04 t2.micro or t3.small instance
- Open ports 22, 80, 443, 8000 in the Security Group
- SSH in and follow the same steps as DigitalOcean above

### Railway / Render
- Connect your GitHub repo
- Set all environment variables from `.env.example` in the dashboard
- Railway auto-detects the Dockerfile and deploys

