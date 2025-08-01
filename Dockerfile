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


# Dockerfile

FROM python:3.11-slim

# Install system packages
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Collect static files (optional)
RUN python manage.py collectstatic --noinput

# Run gunicorn server
CMD ["gunicorn", "passport_oct.wsgi:application", "--bind", "0.0.0.0:8000"]
