# SmartDocs Backend

## Overview
This backend provides OCR processing, document persistence, and reporting APIs for the SmartDocs frontend.

## Setup
1. Create a Python virtual environment:
   `python -m venv .venv`
2. Activate it and install dependencies:
   `pip install -r requirements.txt`
3. Start MySQL (XAMPP) and create the database `smartdocs_db`.
4. Run the backend:
   `uvicorn app:app --reload`

## API Endpoints
- POST /api/upload
- POST /api/scan
- POST /api/save
- GET /api/documents
- GET /api/dashboard
- GET /api/reports
- GET /api/activity

## Frontend Integration
The frontend should connect to `http://localhost:8000`.
