# Guide de déploiement d'une application Flask avec Nginx

Ce guide vous explique comment déployer votre application Flask sur un serveur Linux utilisant Nginx comme serveur proxy inverse et Gunicorn comme serveur WSGI.

## Prérequis

- Une machine Linux (Ubuntu/Debian recommandé)
- Python 3.8+ installé
- pip installé
- Accès root ou sudo
- Un nom de domaine pointant vers votre serveur (optionnel)

## 1. Préparation du serveur

### Mise à jour du système

```bash
sudo apt update
sudo apt upgrade -y
```

### Installation des dépendances

```bash
sudo apt install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-venv nginx
```

## 2. Configuration de l'application Flask

### Création d'un utilisateur dédié (optionnel mais recommandé)

```bash
sudo useradd -m -s /bin/bash flaskapp
sudo su - flaskapp
```

### Clonage du dépôt

```bash
git clone https://github.com/votre-compte/votre-projet.git
cd votre-projet
```

### Configuration de l'environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### Test de l'application avec Gunicorn

```bash
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

> Note: Ce test suppose que votre application possède un fichier `wsgi.py` qui importe l'objet `app` de votre application Flask. Si ce n'est pas le cas, créez un fichier `wsgi.py` avec le contenu suivant:

```python
from mon_application import app

if __name__ == "__main__":
    app.run()
```

## 3. Configuration de Gunicorn comme service systemd

### Création du fichier de service Gunicorn

Quittez l'utilisateur flaskapp si vous l'utilisez, puis créez un fichier de service systemd:

```bash
sudo nano /etc/systemd/system/flaskapp.service
```

Ajoutez le contenu suivant (adaptez les chemins selon votre configuration):

```ini
[Unit]
Description=Gunicorn instance pour votre application Flask
After=network.target

[Service]
User=flaskapp
Group=www-data
WorkingDirectory=/home/flaskapp/votre-projet
Environment="PATH=/home/flaskapp/votre-projet/venv/bin"
ExecStart=/home/flaskapp/votre-projet/venv/bin/gunicorn --workers 3 --bind unix:flaskapp.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

### Démarrage et activation du service

```bash
sudo systemctl start flaskapp
sudo systemctl enable flaskapp
sudo systemctl status flaskapp
```

## 4. Configuration de Nginx

### Création d'un fichier de configuration Nginx

```bash
sudo nano /etc/nginx/sites-available/flaskapp
```

Ajoutez la configuration suivante (adaptez selon vos besoins):

```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;  # Remplacez par votre domaine ou l'IP du serveur

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/flaskapp/votre-projet/flaskapp.sock;
    }

    location /static {
        alias /home/flaskapp/votre-projet/static;
    }
}
```

### Activation de la configuration

```bash
sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled
sudo nginx -t  # Vérification de la syntaxe
sudo systemctl restart nginx
```

### Configuration du pare-feu (si activé)

```bash
sudo ufw allow 'Nginx Full'
```

## 5. Sécurisation avec HTTPS (Let's Encrypt)

Pour sécuriser votre site avec HTTPS gratuitement:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

## 6. Mise à jour de l'application

Pour mettre à jour votre application:

```bash
sudo su - flaskapp
cd votre-projet
git pull
source venv/bin/activate
pip install -r requirements.txt
exit
sudo systemctl restart flaskapp
```

## 7. Dépannage

### Vérifier les logs

```bash
# Logs Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Logs Gunicorn
sudo journalctl -u flaskapp
```

### Problèmes courants

1. **Permissions**: Assurez-vous que les permissions des fichiers sont correctes
   ```bash
   sudo chown -R flaskapp:www-data /home/flaskapp/votre-projet
   ```

2. **Socket**: Vérifiez que le socket Gunicorn est créé et accessible
   ```bash
   ls -la /home/flaskapp/votre-projet/flaskapp.sock
   ```

3. **Pare-feu**: Vérifiez que les ports nécessaires sont ouverts
   ```bash
   sudo ufw status
   ```

## Conclusion

Votre application Flask est maintenant déployée avec Nginx comme proxy inverse et Gunicorn comme serveur WSGI. Cette configuration est robuste et adaptée à un environnement de production.

Pour toute question ou problème, n'hésitez pas à ouvrir une issue sur GitHub.
