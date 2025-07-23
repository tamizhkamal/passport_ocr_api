# Passport-OCR

# Passport OCR Service

A Django-based service that extracts passport data using Tesseract and PassportEye OCR.

## Features

- Dual OCR Engine Support
- MRZ Extraction
- Dynamic Language Detection
- REST API Ready

## Setup

```bash
git clone https://github.com/CodeTez-Technologies/Passport-OCR-CT.git
cp .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
