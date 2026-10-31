# Hostinger VPS deployment (Ubuntu)

Yes. CricutGen needs a Hostinger **VPS** because it runs Python and installs native/image-processing libraries. Hostinger's Web and Cloud hosting plans do not support Python apps that need root-level dependency installation. See [Hostinger's Python support note](https://support.hostinger.com/en/articles/3648030-is-python-supported-at-hostinger).

This guide assumes an Ubuntu 24.04 VPS, a domain pointed to its IP, and SSH access. To open the terminal in Hostinger, go to **hPanel → VPS → Manage → Overview → Web Console**; it opens in a new browser tab. If the tab does not open, allow pop-ups for `hpanel.hostinger.com`. Keep the OpenAI API key private; never put it in browser code or commit `.env`.

## 1. Point your domain to the VPS

In Hostinger DNS, add an `A` record for your chosen hostname (for example, `cut.example.com`) pointing to your VPS IPv4 address. Allow time for DNS to update. In Hostinger's VPS firewall, allow inbound SSH, HTTP (80), and HTTPS (443).

## 2. Install server packages

SSH into the VPS, then run:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential nginx certbot python3-certbot-nginx
sudo adduser --system --group --home /opt/cricutgen cricutgen
sudo mkdir -p /opt/cricutgen
sudo chown -R cricutgen:cricutgen /opt/cricutgen
```

Upload the project files (including `app/` and `requirements.txt`) by SFTP into a folder in your SSH user home, such as `cricutgen-upload`. Then copy the files into the app folder and set ownership (replace `YOUR_SSH_USER` with your SSH login name):

```bash
sudo cp -a /home/YOUR_SSH_USER/cricutgen-upload/. /opt/cricutgen/
sudo chown -R cricutgen:cricutgen /opt/cricutgen
```

Do not upload `.env` from your computer; create it directly on the VPS in the next step.

## 3. Install the app and set its API key

```bash
sudo -u cricutgen bash
cd /opt/cricutgen
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
nano .env
```

Put these lines in `.env`, replacing the example with your own OpenAI API key:

```dotenv
OPENAI_API_KEY=your_openai_api_key
OUTPUT_DIR=/opt/cricutgen/app/output
```

Save and close nano (`Ctrl+O`, Enter, `Ctrl+X`), then leave the `cricutgen` shell with `exit`.

## 4. Run it as a system service

Create the service file:

```bash
sudo nano /etc/systemd/system/cricutgen.service
```

Paste this configuration:

```ini
[Unit]
Description=CricutGen web app
After=network.target

[Service]
User=cricutgen
Group=cricutgen
WorkingDirectory=/opt/cricutgen
EnvironmentFile=/opt/cricutgen/.env
ExecStart=/opt/cricutgen/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Start the service and check it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cricutgen
sudo systemctl status cricutgen
```

## 5. Put Nginx and HTTPS in front

Create an Nginx site, replacing `cut.example.com` with your hostname:

```bash
sudo nano /etc/nginx/sites-available/cricutgen
```

Paste:

```nginx
server {
    listen 80;
    server_name cut.example.com;

    client_max_body_size 10m;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 180s;
    }
}
```

Enable the site and request a free Let's Encrypt certificate:

```bash
sudo ln -s /etc/nginx/sites-available/cricutgen /etc/nginx/sites-enabled/cricutgen
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d cut.example.com
```

Open `https://cut.example.com` to use the app.

## Useful maintenance commands

```bash
sudo systemctl restart cricutgen
sudo journalctl -u cricutgen -f
```

After uploading code updates, reinstall dependencies if `requirements.txt` changed, then restart the service. Generated SVGs and previews are stored in `/opt/cricutgen/app/output`; include that folder in your backups. Image generation requires an OpenAI API key with image generation access and incurs OpenAI API charges.

The app keeps active job status in memory, so use one Uvicorn worker as shown. Restarting the service clears active job status, though already generated files remain on disk.


