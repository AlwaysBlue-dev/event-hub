# Use official Python image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (Railway uses 8000 by default)
EXPOSE 8000

# Run the app with Gunicorn
CMD ["gunicorn", "EventsHub.wsgi:application", "--bind", "0.0.0.0:8000"]
