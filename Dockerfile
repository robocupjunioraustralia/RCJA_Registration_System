FROM python:3.13-slim

WORKDIR /app

ENV PATH="${PATH}:/app"
ENV PORT=8000

# To avoid python creating .pyc files and buffering output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY app.json /app
COPY rcjaRegistration /app

RUN chmod +x /app/migrate-and-start.sh
CMD ["/app/migrate-and-start.sh"]
