# Database Setup & Migrations

Simple manual database management for Code Architecture Mapper.

## Quick Setup

### 1. First Time Setup

```bash
cd backend
python db_setup.py init
```

This will:
- Create the PostgreSQL database if it doesn't exist
- Run the initial schema migration (`001_initial_schema.sql`)
- Set up all tables, indexes, and sample data

### 2. For Docker

The database setup can be integrated with Docker startup. Add this to your application startup or Docker entrypoint:

```python
from db_setup import setup_database
setup_database()
```

## Manual Migrations

### Creating New Migrations

1. **Create a new SQL file** in `migrations/` directory:
   ```
   002_add_new_feature.sql
   003_modify_table.sql
   ```

2. **Apply the migration:**
   ```bash
   python db_setup.py run-migration 002_add_new_feature.sql
   ```

### Migration File Format

```sql
-- Description of what this migration does
-- Migration XXX: Brief title

-- Your SQL statements here
ALTER TABLE analyses ADD COLUMN new_field TEXT;
CREATE INDEX idx_analyses_new_field ON analyses(new_field);
```

## Available Commands

```bash
# Complete setup (recommended for first time)
python db_setup.py init

# Create database only (no tables)
python db_setup.py create-db

# Run specific migration file
python db_setup.py run-migration 002_add_feature.sql

# Run with no arguments (same as init)
python db_setup.py
```

## Database Configuration

Set the `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

Default: `postgresql://postgres:postgres@localhost:5432/repo_architect`

## Current Schema

The initial migration (`001_initial_schema.sql`) creates:

### Tables
- **`analyses`** - Repository analysis results
- **`files`** - Individual file metrics and data
- **`examples`** - Example repositories for demo

### Key Features
- UUID primary keys with auto-generation
- JSONB columns for flexible data storage
- Proper foreign key relationships with CASCADE deletes
- Indexes for performance
- Auto-updating `updated_at` timestamps
- Sample data for examples

## Adding New Migrations

1. **Manual approach** (recommended):
   - Create new `.sql` file with incremental number
   - Write your DDL statements
   - Run using `python db_setup.py run-migration filename.sql`

2. **For complex changes:**
   - Test on a copy of your data first
   - Consider rollback scripts if needed
   - Document the changes clearly

## Benefits of Manual Migrations

✅ **Simple & Fast** - No complex framework overhead  
✅ **Full Control** - Write exactly the SQL you need  
✅ **Easy Debugging** - Direct SQL, easy to troubleshoot  
✅ **Docker Friendly** - Easy to integrate with container startup  
✅ **Production Ready** - Direct execution, no migration state tracking  

## Docker Integration

Add to your `Dockerfile` or startup script:

```dockerfile
# In Dockerfile
COPY db_setup.py ./
RUN python db_setup.py init
```

Or in application startup:
```python
# In your main app
if __name__ == "__main__":
    from db_setup import setup_database
    setup_database()
    # Start your FastAPI app
``` 