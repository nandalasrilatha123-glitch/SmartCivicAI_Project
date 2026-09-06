"""
One-off diagnostic: connects to the same Postgres DB the app uses and lists
every user row, so you can confirm the demo accounts actually exist.

Run from the backend/ folder with your venv active:
    python check_users.py
"""
from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print(f"Connected OK to: {settings.DATABASE_URL}\n")
    try:
        rows = conn.execute(text("SELECT email, role, is_active FROM users ORDER BY role;")).fetchall()
    except Exception as e:
        print(f"Query failed: {e}")
        print("\nThis usually means the 'users' table doesn't exist yet -> run:")
        print("  alembic upgrade head")
        print("  python -m app.seed")
        raise SystemExit(1)

    if not rows:
        print("The 'users' table exists but is EMPTY.")
        print("-> The seed script hasn't been run yet (or ran against a different DB). Run:")
        print("  python -m app.seed")
    else:
        print(f"Found {len(rows)} user(s):\n")
        for email, role, is_active in rows:
            print(f"  {email:40s} role={role:10s} active={is_active}")