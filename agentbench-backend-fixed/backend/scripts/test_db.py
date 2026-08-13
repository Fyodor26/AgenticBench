from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
print('DATABASE_URL=', DATABASE_URL)

if not DATABASE_URL:
    print('No DATABASE_URL found in environment.')
    raise SystemExit(1)

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print('Connected. Postgres version:', result.scalar())
except SQLAlchemyError as e:
    print('Connection failed:', e)
    raise
