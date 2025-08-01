FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# 👇 Add system-level dependency for OpenCV (cv2)
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=passport_oct.settings

RUN mkdir -p /app/staticfiles
ENV STATIC_ROOT=/app/staticfiles
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "passport_oct.wsgi:application", "--bind", "0.0.0.0:8000"]
