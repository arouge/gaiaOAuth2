# Flask Application Deployment Guide with Nginx

This guide explains how to deploy your Flask application on a Linux server using Nginx as a reverse proxy server and Gunicorn as a WSGI server.

## Prerequisites

- A Linux machine (Ubuntu/Debian recommended)
- Python 3.8+ installed
- pip installed
- Root or sudo access
- A domain name pointing to your server (optional)

## 1. Server Preparation

### System Update

```bash
sudo apt update
sudo apt upgrade -y
```

### Installing Dependencies

```bash
sudo apt install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-venv nginx
```

## 2. Flask Application Setup

### Creating a Dedicated User (optional but recommended)

```bash
sudo useradd -m -s /bin/bash flaskapp
sudo su - flaskapp
```

### Cloning the Repository

```bash
git clone https://github.com/your-account/your-project.git
cd your-project
```

### Setting Up the Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### Testing the Application with Gunicorn

```bash
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

> Note: This test assumes your application has a `wsgi.py` file that imports the `app` object from your Flask application. If not, create a `wsgi.py` file with the following content:

```python
from my_application import app

if __name__ == "__main__":
    app.run()
```

## 3. Configuring Gunicorn as a systemd Service

### Creating the Gunicorn Service File

Exit the flaskapp user if you're using it, then create a systemd service file:

```bash
sudo nano /etc/systemd/system/flaskapp.service
```

Add the following content (adapt the paths according to your configuration):

```ini
[Unit]
Description=Gunicorn instance for your Flask application
After=network.target

[Service]
User=flaskapp
Group=www-data
WorkingDirectory=/home/flaskapp/your-project
Environment="PATH=/home/flaskapp/your-project/venv/bin"
ExecStart=/home/flaskapp/your-project/venv/bin/gunicorn --workers 3 --bind unix:flaskapp.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

### Starting and Enabling the Service

```bash
sudo systemctl start flaskapp
sudo systemctl enable flaskapp
sudo systemctl status flaskapp
```

## 4. Nginx Configuration

### Creating an Nginx Configuration File

```bash
sudo nano /etc/nginx/sites-available/flaskapp
```

Add the following configuration (adapt as needed):

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;  # Replace with your domain or server IP

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/flaskapp/your-project/flaskapp.sock;
    }

    location /static {
        alias /home/flaskapp/your-project/static;
    }
}
```

### Activating the Configuration

```bash
sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled
sudo nginx -t  # Syntax verification
sudo systemctl restart nginx
```

### Firewall Configuration (if enabled)

```bash
sudo ufw allow 'Nginx Full'
```

## 5. Securing with HTTPS (Let's Encrypt)

To secure your site with free HTTPS:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## 6. Updating the Application

To update your application:

```bash
sudo su - flaskapp
cd your-project
git pull
source venv/bin/activate
pip install -r requirements.txt
exit
sudo systemctl restart flaskapp
```

## 7. Troubleshooting

### Checking Logs

```bash
# Nginx Logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Gunicorn Logs
sudo journalctl -u flaskapp
```

### Common Issues

1. **Permissions**: Make sure file permissions are correct
   ```bash
   sudo chown -R flaskapp:www-data /home/flaskapp/your-project
   ```

2. **Socket**: Check that the Gunicorn socket is created and accessible
   ```bash
   ls -la /home/flaskapp/your-project/flaskapp.sock
   ```

3. **Firewall**: Verify that the necessary ports are open
   ```bash
   sudo ufw status
   ```

## Conclusion

Your Flask application is now deployed with Nginx as a reverse proxy and Gunicorn as a WSGI server. This configuration is robust and suitable for a production environment.

For any questions or issues, feel free to open an issue on GitHub.
