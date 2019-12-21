FROM python:3.8
EXPOSE 80
ENV PORT=80
ENV PATH="${PATH}:/app"

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY rcjaRegistration /app
WORKDIR /app
CMD ["/bin/sh", "-c", "/app/manage.py runserver 0.0.0.0:${PORT}"]
