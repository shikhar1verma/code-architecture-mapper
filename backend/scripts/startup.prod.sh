#!/bin/bash

# Production startup script for Code Architecture Mapper Backend
# This script works with external databases (Supabase, etc.)

set -e

echo "🚀 Starting Code Architecture Mapper Backend (Production)..."

# Wait for external database to be ready
echo "⏳ Initializing database..."
cd /app && PYTHONPATH=/app python backend/db_setup.py init

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
python -c "
import time
import sys
import psycopg2
from backend.config import DATABASE_URL

print(f'🔗 Connecting to database...')

for attempt in range(30):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        print('✅ Database connection successful!')
        break
    except psycopg2.OperationalError as e:
        print(f'⏳ Database not ready yet (attempt {attempt + 1}/30), waiting...')
        print(f'   Error: {str(e)[:100]}...')
        time.sleep(2)
else:
    print('❌ Database connection failed after 30 attempts')
    sys.exit(1)
"

# Load fixtures (optional in production)
echo "📦 Loading example fixtures..."
cd /app && PYTHONPATH=/app python backend/scripts/sync_fixtures.py

if [ $? -eq 0 ]; then
    echo "✅ Fixtures loaded successfully!"
else
    echo "⚠️  Some fixtures failed to load, but continuing..."
fi

# Start the application
echo "🎯 Starting application server..."
exec uvicorn backend.app:app --host 0.0.0.0 --port 8000
