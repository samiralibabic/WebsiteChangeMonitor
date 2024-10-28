# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP main.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV PORT 5002

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Run database migrations
RUN flask db upgrade

# Make port 5002 available to the world outside this container
EXPOSE 5002

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "main:app"]
