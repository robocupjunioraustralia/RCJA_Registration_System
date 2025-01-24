FROM python:3.13

WORKDIR /app

ENV PATH="${PATH}:/app"
ENV PORT=8000

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY app.json /app
COPY rcjaRegistration /app

RUN chmod +x /app/migrate-and-start.sh
CMD ["/app/migrate-and-start.sh"]
