# Deploying

## Dokku

### Setting up the server

See [DOKKU.md](DOKKU.md).

### Pushing to production

```
git remote add dokku dokku@enter.robocupjunior.org.au:rcja-registration
git push dokku production:master # Deploy the production branch
```

## Heroku

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Staging is auto deployed from the `master` branch. Demo is auto deployed from the `demo` branch.

### Manual Deploy
```
# Setup
heroku login
heroku git:remote --app=rcja-registration-staging --remote=staging
heroku git:remote --app=rcja-registration-demo --remote=demo
git config heroku.remote staging

git push -f <staging/demo> <branch>:master
```

## Docker-Compose

1. Install [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-using-the-convenience-script) and [Docker-Compose](https://docs.docker.com/compose/install/)
2. Clone this repo and change to the directory
3. Start the server

Set the `SECRET_KEY` environment variable to a long random string.
```
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d
```
4. After upgrading the code version/on first install run
```
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d --build

docker-compose -f docker-compose.yml -f docker-compose.production.yml exec web manage.py migrate
```
5. On first install run
```
docker-compose -f docker-compose.yml -f docker-compose.production.yml exec web manage.py createsuperuser
```
