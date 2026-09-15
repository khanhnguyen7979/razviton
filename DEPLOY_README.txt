RAZVITON WEB READY

Local Windows:
RELEASE: public-information site with warnings; see RELEASE_READINESS.md.
Full member-service readiness remains blocked on durable storage and privacy information.
RAZVITON_REGISTRATION_ENABLED=0 on Render; set 1 only after those gates are verified.
Served frontend is public/, NOT the HTML copies at repository root.
Auth requires FastAPI; do not serve the repository root with a static server.
RAZVITON_DATA_DIR optionally sets SQLite storage; default is backend/data.
Render's default filesystem is ephemeral: decide durable storage and verify
backup/restore before accepting real registrations. No paid resource was created.
RAZVITON_COOKIE_SECURE=1 for HTTPS production; 0 only for local HTTP testing.
Debug docs are disabled. /health checks database access.
Run tests only against localhost with a separate temporary RAZVITON_DATA_DIR.

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

