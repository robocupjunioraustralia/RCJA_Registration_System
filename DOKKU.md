# Installing Dokku

On the server:

```
# Install Dokku
# http://dokku.viewdocs.io/dokku/getting-started/installation/#1-install-dokku
wget https://raw.githubusercontent.com/dokku/dokku/v0.19.13/bootstrap.sh;
sudo DOKKU_TAG=v0.19.13 bash bootstrap.sh

# Go to the server url and setup via web installer. Disable virtual host mode. Add your ssh key to authorized_keys.

# Add alternate SSH keys
# Add login to the root user with .ssh/authorized_keys
# Add key to dokku user to allow deploys
echo "ssh-rsa ..." | sudo dokku ssh-keys:add <name>

# Install Dokku plugins
sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git
sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
dokku letsencrypt:cron-job --add
dokku config:set --global DOKKU_LETSENCRYPT_EMAIL=<your email>

# Configure Dokku options
dokku config:set --global DOKKU_RM_CONTAINER=1

# Create the app
dokku apps:create rcja-registration
dokku postgres:create rcja-registration-postgres
dokku postgres:link rcja-registration-postgres rcja-registration

# Substitute your values here
export RCJA_REGISTRATION_DOMAIN=enter.robocupjunior.org.au
dokku config:set --no-restart rcja-registration DEBUG=false PORT=80 ALLOWED_HOSTS=$RCJA_REGISTRATION_DOMAIN SECRET_KEY=<django secret key>

# Do a deploy (see DEPLOY.md)

# Configure the app
dokku domains:add rcja-registration $RCJA_REGISTRATION_DOMAIN
dokku proxy:ports-remove rcja-registration http:80:80
dokku proxy:ports-add rcja-registration http:80:8000
dokku proxy:ports-add rcja-registration https:443:8000
# Enable letsencrypt
dokku letsencrypt rcja-registration

# Generate a superuser
dokku run rcja-registration manage.py createsuperuser
```
