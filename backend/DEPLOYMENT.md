# Deployment Guide

This guide covers both local development and production deployment options.

## Environment Setup

1. **Copy environment template:**
   ```bash
   cp env.example .env
   ```

2. **Fill in your environment variables:**
   ```env
   # For local development
   DATABASE_URL=postgresql://postgres:postgres@postgres:5432/repo_architect
   
   # For production (Supabase example)
   DATABASE_URL=postgresql://username:password@hostname:5432/database_name
   
   GEMINI_API_KEY=your_actual_gemini_api_key
   ```

## Local Development

Use the local Docker Compose with PostgreSQL container:

```bash
# Start local development environment
docker-compose -f docker-compose.local.yml up --build

# Stop environment
docker-compose -f docker-compose.local.yml down
```

**What this includes:**
- PostgreSQL container with persistent data
- Backend API with hot reloading
- Automatic database initialization
- Fixture loading

## Production Deployment

### Option 1: Render Web Service (Recommended)

1. **Connect your GitHub repository to Render**

2. **Create a new Web Service with these settings:**
   - **Runtime:** Docker
   - **Dockerfile Path:** `backend/Dockerfile` (default)
   - **Port:** 8000

3. **Set Environment Variables in Render:**
   ```
   DATABASE_URL=your_supabase_or_external_db_url
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-1.5-flash
   TOP_FILES=40
   COMPONENT_COUNT=8
   SQL_DEBUG=false
   DEBUG=false
   ```

4. **Deploy:** Render will automatically build and deploy

### Option 2: Docker Compose Production

For VPS or self-hosted deployment:

```bash
# Production deployment (external database) - uses default files
docker-compose up --build -d
```

**Requirements:**
- External PostgreSQL database (Supabase, AWS RDS, etc.)
- Environment variables configured
- Database URL accessible from deployment server

## Database Setup

### For Supabase:

1. **Create a new project** on [Supabase](https://supabase.com)

2. **Get your connection string:**
   - Go to Settings → Database
   - Copy the "Connection pooling" URL (recommended for production)
   - Format: `postgresql://postgres.xxxx:[PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres`

3. **Set as DATABASE_URL** in your environment

### For other cloud providers:

- **AWS RDS:** Use the endpoint from RDS console
- **Google Cloud SQL:** Use the connection string from Cloud Console
- **Azure PostgreSQL:** Use the server name from Azure portal

## File Structure

```
backend/
├── docker-compose.yml         # Production with external DB (DEFAULT)
├── docker-compose.local.yml   # Local development with PostgreSQL
├── Dockerfile                 # Production Docker image (DEFAULT)
├── Dockerfile.local          # Local development Docker image
├── scripts/
│   ├── startup.sh            # Local development startup
│   └── startup.prod.sh       # Production startup
└── env.example               # Environment template
```

## Troubleshooting

### Database Connection Issues:

1. **Verify DATABASE_URL format:**
   ```
   postgresql://username:password@host:port/database_name
   ```

2. **Check firewall/security groups** allow connections on PostgreSQL port

3. **For Supabase:** Ensure you're using the pooler URL for production

### Application Startup Issues:

1. **Check logs:**
   ```bash
   # Docker Compose
   docker-compose logs backend
   
   # Render
   View logs in Render dashboard
   ```

2. **Common fixes:**
   - Verify all environment variables are set
   - Ensure database is accessible
   - Check GEMINI_API_KEY is valid

## Health Checks

Once deployed, verify these endpoints:

- **Health Check:** `GET /health`
- **API Status:** `GET /`
- **Examples:** `GET /api/examples`

## Scaling Considerations

For high-traffic production use:

1. **Database:** Use connection pooling (Supabase includes this)
2. **Storage:** Consider cloud storage for git repos instead of local volumes
3. **Caching:** Add Redis for caching analysis results
4. **Load Balancing:** Use multiple backend instances behind a load balancer
