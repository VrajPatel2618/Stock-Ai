# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# Run migrations, collect static, and start gunicorn respecting the PORT env variable
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn stockai.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2"]
