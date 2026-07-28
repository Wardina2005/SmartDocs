cd C:\xampp\htdocs\smartdocs\smartdocs-backend

python -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000

python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000