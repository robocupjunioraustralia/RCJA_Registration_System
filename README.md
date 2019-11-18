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


