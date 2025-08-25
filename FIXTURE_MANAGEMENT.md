# Fixture Management Guide

This guide explains how to manage example fixtures for the Code Architecture Mapper application.

## Overview

Fixtures are example analyses that are preloaded into the database to demonstrate the application's capabilities. As of the latest update, fixture loading has been separated from the main application startup to provide more flexibility and reduce deployment complexity.

## Architecture Changes

### Before
- Fixtures were automatically loaded during Docker container startup
- Application startup was dependent on successful fixture loading
- Database connectivity issues could prevent app startup

### After
- Fixtures are loaded manually using a standalone script
- Application starts independently of fixture status
- Database connectivity is optional for app startup
- More control over when and how fixtures are loaded

## Manual Fixture Management

### Standalone Fixture Sync Script

Use the `sync_fixtures_standalone.py` script to manage fixtures:

```bash
# Basic usage - sync fixtures to database
python backend/sync_fixtures_standalone.py

# Check fixture validity only (no database required)
python backend/sync_fixtures_standalone.py --check-only

# Verbose output
python backend/sync_fixtures_standalone.py --verbose

# Custom fixtures directory
python backend/sync_fixtures_standalone.py --fixtures-dir /path/to/fixtures

# Show help
python backend/sync_fixtures_standalone.py --help
```

### Environment Configuration

The script reads database configuration from environment variables:

```bash
# Required environment variable
export DATABASE_URL="postgresql://user:password@host:port/database"

# Run the sync
python backend/sync_fixtures_standalone.py
```

### Using .env File

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/repo_architect
```

The script will automatically load variables from the `.env` file if `python-dotenv` is available.

## Docker Deployment Workflow

### 1. Start the Application
```bash
# Start the application containers
docker-compose up -d

# Application is now running without fixtures
```

### 2. Load Fixtures (Separate Step)
```bash
# Option A: Run sync script from host machine
DATABASE_URL="postgresql://user:pass@localhost:5432/dbname" \
python backend/sync_fixtures_standalone.py

# Option B: Run sync script inside Docker container
docker-compose exec backend python sync_fixtures_standalone.py

# Option C: Run as one-time container
docker-compose run --rm backend python sync_fixtures_standalone.py
```

## Development Workflow

### Local Development
```bash
# 1. Start the backend server
cd backend
uvicorn app:app --reload

# 2. In another terminal, load fixtures
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/repo_architect" \
python sync_fixtures_standalone.py
```

### Validation Only
```bash
# Check if fixture files are valid without database
python backend/sync_fixtures_standalone.py --check-only
```

## CI/CD Integration

### Example GitHub Actions
```yaml
- name: Load Fixtures
  run: |
    docker-compose up -d database
    sleep 10  # Wait for database
    DATABASE_URL="${{ secrets.DATABASE_URL }}" \
    python backend/sync_fixtures_standalone.py
```

### Example Docker Compose Override
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  fixture-loader:
    build: ./backend
    depends_on:
      - database
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@database:5432/repo_architect
    command: python sync_fixtures_standalone.py
    profiles: ["fixtures"]
```

Run with: `docker-compose --profile fixtures up fixture-loader`

## Fixture File Structure

Fixture files are located in `backend/fixtures/examples/` and must follow this structure:

```json
{
  "example": {
    "name": "Example Name",
    "repo_url": "https://github.com/owner/repo",
    "status": "complete",
    // ... other analysis fields
  }
}
```

Required fields:
- `name`: Human-readable name for the dropdown
- `repo_url`: Repository URL
- `status`: Analysis status (usually "complete")

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   ```bash
   # Ensure PYTHONPATH is set correctly
   PYTHONPATH=/path/to/project python backend/sync_fixtures_standalone.py
   ```

2. **Database Connection Errors**
   ```bash
   # Verify DATABASE_URL format
   DATABASE_URL="postgresql://user:pass@host:port/db" python backend/sync_fixtures_standalone.py
   
   # Test database connectivity first
   python -c "import psycopg2; psycopg2.connect('postgresql://user:pass@host:port/db')"
   ```

3. **Fixture Validation Errors**
   ```bash
   # Check fixture structure without database
   python backend/sync_fixtures_standalone.py --check-only --verbose
   ```

### Debug Mode
```bash
# Enable verbose logging
python backend/sync_fixtures_standalone.py --verbose

# Check what environment variables are set
env | grep DATABASE_URL
```

## Migration from Old System

If you're migrating from the automatic fixture loading system:

1. **Update Dockerfile**: Remove fixture loading from `CMD`
2. **Update docker-compose.yml**: Remove fixture-related commands
3. **Update CI/CD**: Add separate fixture loading step
4. **Update documentation**: Inform team about manual fixture management

## Best Practices

1. **Validate First**: Always run `--check-only` before syncing to database
2. **Backup Database**: Before loading fixtures in production
3. **Environment Separation**: Use different fixtures for dev/staging/prod
4. **Version Control**: Keep fixture files in version control
5. **Documentation**: Update team documentation about fixture management

## Advanced Usage

### Custom Fixture Directory
```bash
python backend/sync_fixtures_standalone.py \
  --fixtures-dir /custom/path/to/fixtures
```

### Production Deployment
```bash
# Production-safe fixture loading
DATABASE_URL="${PROD_DATABASE_URL}" \
python backend/sync_fixtures_standalone.py \
  --verbose \
  2>&1 | tee fixture-sync.log
```

### Conditional Loading
```bash
# Only load if no examples exist
python -c "
import os
from backend.database.connection import SessionLocal
from backend.database.models import Example

session = SessionLocal()
count = session.query(Example).count()
session.close()

if count == 0:
    os.system('python backend/sync_fixtures_standalone.py')
else:
    print(f'Skipping fixture load - {count} examples already exist')
"
``` 