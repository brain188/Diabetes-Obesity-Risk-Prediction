# Docker entrypoint for the Intelligent DSS backend.

set -e

echo "============================================================"
echo "  Intelligent DSS Backend — Starting"
echo "============================================================"

# Wait for Supabase / remote PostgreSQL
# Extract host and port from DATABASE_URL
if [ -n "$DATABASE_URL" ]; then
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:/?]*\).*|\1|p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    DB_PORT=${DB_PORT:-5432}

    echo "Waiting for database at $DB_HOST:$DB_PORT ..."
    max_retries=30
    retries=0
    until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
        retries=$((retries + 1))
        if [ $retries -ge $max_retries ]; then
            echo "ERROR: Database not reachable after $max_retries attempts. Exiting."
            exit 1
        fi
        echo "  Attempt $retries/$max_retries — retrying in 2s..."
        sleep 2
    done
    echo "Database is reachable."
else
    echo "WARNING: DATABASE_URL not set — skipping DB readiness check."
fi

# ── Database table creation ───────────────────────────────────────────────────
# We use SQLAlchemy's create_all() at startup (in main.py lifespan),
# NOT Alembic migrations. No migration command needed here.
echo "Database tables will be created automatically at application startup."

# ── Start the application ─────────────────────────────────────────────────────
echo "Starting FastAPI application..."
echo "============================================================"
exec "$@"