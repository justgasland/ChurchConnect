# Use Python 3.11 as base
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && apt-get clean

# Copy dependency file first
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . /app/

# Run collectstatic (safe even if STATIC_ROOT isn't set yet)
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Default run command
CMD ["gunicorn", "ChurchConnect.wsgi:application", "--bind", "0.0.0.0:8000"]
