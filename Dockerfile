# # Use official Python image
# FROM python:3.11-slim

# # Set work directory
# WORKDIR /app

# # Install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy rest of the code
# COPY . .

# # Expose port (FastAPI default is 8000)
# EXPOSE 8000

# # Run the app
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# Use official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory inside the container
WORKDIR /

# Copy project files
COPY . /

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y libgl1-mesa-glx


# Collect static files (if needed)
# RUN python manage.py collectstatic --noinput

# Expose the port that Django will run on
EXPOSE 8000

CMD ["gunicorn", "passport_oct.wsgi:application", "--workers", "1", "--threads", "1", "--bind", "0.0.0.0:8000"]
