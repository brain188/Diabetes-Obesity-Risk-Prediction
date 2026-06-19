# Alembic Migrations

This directory contains database migration files for the Intelligent DSS application.

## Quick Start

### Create a new migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description_of_changes"

# Create an empty migration
alembic revision -m "description_of_changes"

# APPLY MIGRATIONS

# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade +1
alembic upgrade <revision_id>

# Downgrade to a specific version
alembic downgrade -1
alembic downgrade <revision_id>


# CHECK MIGRATION STATUS

# Show current revision
alembic current

# Show migration history
alembic history


# COMMON COMMANDS

# Initialize Alembic (first time)
alembic init alembic

# Create a new migration
alembic revision --autogenerate -m "add_patient_table"

# Upgrade to latest
alembic upgrade head

# Downgrade by one
alembic downgrade -1

# Show current version
alembic current

# Show history
alembic history


# MIGRATION COMMANDS

# Create initial migration
alembic revision --autogenerate -m "initial_schema"

# Apply all migrations
alembic upgrade head

# Check current version
alembic current

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>