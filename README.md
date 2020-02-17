# RCJA Registration System

![](https://github.com/MelbourneHighSchoolRobotics/RCJA_Registration_System/workflows/Django%20Build%20Tests/badge.svg
)
[![codecov](https://codecov.io/gh/MelbourneHighSchoolRobotics/RCJA_Registration_System/branch/master/graph/badge.svg?token=TGG6NwrrJw)](https://codecov.io/gh/MelbourneHighSchoolRobotics/RCJA_Registration_System)

## Development Getting Started

1. Install Docker and Docker Compose

2. Start the app

```
docker-compose up -d
```

3. Initialise Django

```
docker-compose exec web manage.py migrate
docker-compose exec web manage.py createsuperuser
```

## Deploying

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

### Using Docker Compose

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

## CI Instructions

CI is currently provided by github actions. To see if tests pass, you can look at the actions menu (next to the pull requests button), or the little cross or tick next to your commit. Code coverage is visible in the action, or, you can look at the coverage report at codecov.
