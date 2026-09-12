RAZVITON WEB READY

Local Windows:
1. cd <project>\backend
2. D:\PythonPortable\python.exe -m pip install -r requirements.txt
3. D:\PythonPortable\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
4. Open http://127.0.0.1:8010/

Internet:
- Project contains render.yaml for a Python/FastAPI web service.
- After temporary URL passes, connect razviton.com in the hosting dashboard.
- Do not enable token sale/payment/wallet.
- Production cookie security is enabled by RAZVITON_COOKIE_SECURE=1.

Important:
SQLite is suitable for the current prototype/login stage. Before substantial public traffic,
move auth data to a managed persistent database (e.g. PostgreSQL) and add email verification.
