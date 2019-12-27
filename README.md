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

Staging is automatically deployed from the `master` branch after [linking Heroku to GitHub](https://dashboard.heroku.com/apps/rcja-registration-staging/deploy/github).

```
heroku login
heroku git:remote --app=rcja-registration-staging --remote=staging
heroku git:remote --app=rcja-registration-demo --remote=production
git config heroku.remote staging

git push -f <staging/production> <branch>:master
```

## CI Instructions

CI is currently provided by github actions. To see if tests pass, you can look at the actions menu (next to the pull requests button), or the little cross or tick next to your commit. Code coverage is visible in the action, or, you can look at the coverage report at codecov.
