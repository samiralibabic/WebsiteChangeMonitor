FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP main.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV PORT 5002

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5002

CMD ["sh", "-c", "flask db upgrade && gunicorn --bind 0.0.0.0:5001 main:app"]