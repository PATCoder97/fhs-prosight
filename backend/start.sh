#!/bin/bash
# ============================================================================
# Entrypoint script cho FHS HR Backend
# - Kiểm tra kết nối database
# - Chạy migration (alembic upgrade head)
# - Start uvicorn server
# ============================================================================

set -e

echo "🚀 Starting FHS HR Backend..."

# ============================================================================
# 1. Kiểm tra biến môi trường
# ============================================================================
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    exit 1
fi

echo "✓ DATABASE_URL: $DATABASE_URL"

# ============================================================================
# 2. Chờ Database khả dụng
# ============================================================================
echo "⏳ Waiting for database to be ready..."

MAX_ATTEMPTS=30
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if python -c "
import asyncio
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_db():
    try:
        engine = create_async_engine('$DATABASE_URL', echo=False)
        async with engine.begin() as conn:
            result = await conn.execute(text('SELECT 1'))
            print('✓ Database is ready!')
            return True
    except Exception as e:
        print(f'⏳ Attempt {$ATTEMPT}/{$MAX_ATTEMPTS}: Database not ready yet...')
        return False
    finally:
        await engine.dispose()

asyncio.run(check_db())
" 2>/dev/null; then
        echo "✓ Database connected successfully!"
        break
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    sleep 2
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "❌ ERROR: Could not connect to database after $MAX_ATTEMPTS attempts"
    exit 1
fi

# ============================================================================
# 3. Chạy Migration (Alembic upgrade head)
# ============================================================================
echo ""
echo "📦 Running database migrations..."

cd /app

# Kiểm tra xem alembic.ini có tồn tại không
if [ ! -f "alembic.ini" ]; then
    echo "❌ ERROR: alembic.ini not found in /app"
    exit 1
fi

# Chạy migration
if alembic upgrade head; then
    echo "✓ Database migrations completed successfully!"
else
    echo "❌ ERROR: Database migration failed"
    exit 1
fi

# ============================================================================
# 4. Seed Database
# ============================================================================
echo ""
echo "🌱 Seeding database..."

cd /app

if python -c "
import asyncio
from app.database.session import AsyncSessionLocal
from app.database.seed import seed_database

async def run_seed():
    async with AsyncSessionLocal() as session:
        await seed_database(session)

asyncio.run(run_seed())
" 2>&1; then
    echo "✓ Database seeding completed successfully!"
else
    echo "⚠️  Database seeding failed (non-critical, continuing...)"
fi

# ============================================================================
# 5. Start Uvicorn Server
# ============================================================================
echo ""
echo "✓ All checks passed!"
echo "🌐 Starting Uvicorn server on 0.0.0.0:8001..."
echo ""

cd /app
exec uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level info
