![](https://github.com/MelbourneHighSchoolRobotics/RCJA_Registration_System/workflows/Django%20Build%20Tests/badge.svg
)
[![codecov](https://codecov.io/gh/MelbourneHighSchoolRobotics/RCJA_Registration_System/branch/master/graph/badge.svg?token=TGG6NwrrJw)](https://codecov.io/gh/MelbourneHighSchoolRobotics/RCJA_Registration_System)


RCJA_Registration_System

Development getting started:

1. Setup a virtual env

py -m venv env

2. Activate virtual env

.\env\Scripts\activate

3. Install requirements

pip install -r requirements.txt

4. Initialise django

python manage.py migrate
python manage.py createsuperuser

5. Run server

python manage.py runserver

CI Instructions:

CI is currently provided by github actions. To see if tests pass, you can look at the actions menu (next to the pull requests button), or the little cross or tick next to your commit. Code coverage is visible in the action, or, you can look at the coverage report at codecov.
