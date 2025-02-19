# RCJA Registration System

![](https://github.com/robocupjunioraustralia/RCJA_Registration_System/actions/workflows/django-ci.yml/badge.svg
)[![codecov](https://codecov.io/gh/robocupjunioraustralia/RCJA_Registration_System/graph/badge.svg?token=TGG6NwrrJw)](https://codecov.io/gh/robocupjunioraustralia/RCJA_Registration_System)

## Development Getting Started

1. Install Docker and Docker Compose

2. Clone the repository
    - **Note for Windows:** Ensure `core.autocrlf` is set to `false` in git config before cloning to avoid line ending issues
        ```
        git config --global core.autocrlf false
        ``` 
    ```
    git clone https://github.com/robocupjunioraustralia/RCJA_Registration_System.git
    ```
3. Setup the ```.env``` file by creating a copy of ```.env.dev.sample``` and naming it ```.env```

4. Start the app
    ```
    docker-compose up -d
    ```

5. Initialise Django
    ```
    docker-compose exec web manage.py migrate
    docker-compose exec web manage.py collectstatic
    docker-compose exec web manage.py createsuperuser
    ```

## CI Instructions

CI is currently provided by github actions. To see if tests pass, you can look at the actions menu (next to the pull requests button), or the little cross or tick next to your commit. Code coverage is visible in the action, or, you can look at the coverage report at codecov.
