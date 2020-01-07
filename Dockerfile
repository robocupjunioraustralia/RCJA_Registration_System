FROM python:3.8
EXPOSE 80

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY rcjaRegistration /app
WORKDIR /app
CMD ["/usr/local/bin/python", "/app/manage.py", "runserver", "0.0.0.0:80"]