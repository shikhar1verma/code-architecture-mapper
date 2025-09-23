# Docker Setup Guide

## File Organization

The Docker configuration has been organized with **production-first** approach:

### 🚀 **Production (Default)**
- **`Dockerfile`** - Production image (Render-ready)
- **`docker-compose.yml`** - External database (Supabase/Cloud)

### 🛠️ **Local Development**  
- **`Dockerfile.local`** - Development image with hot reloading
- **`docker-compose.local.yml`** - Includes PostgreSQL container

## Quick Start

### Local Development
```bash
# Start with local PostgreSQL container
docker-compose -f docker-compose.local.yml up --build

# Stop
docker-compose -f docker-compose.local.yml down
```

### Production Deployment
```bash
# Default files are production-ready
docker-compose up --build -d
```

### Render Deployment
Render will automatically use the default `Dockerfile` - no additional configuration needed!

## Environment Setup

1. **Copy environment template:**
   ```bash
   cp env.example .env
   ```

2. **Configure for your environment:**
   ```env
   # Local
   DATABASE_URL=postgresql://postgres:postgres@postgres:5432/repo_architect
   
   # Production  
   DATABASE_URL=your_supabase_or_cloud_db_url
   GEMINI_API_KEY=your_api_key
   ```

## Benefits of This Structure

✅ **Production-First**: Default files are production-ready  
✅ **Render Compatible**: No special configuration needed  
✅ **Clean Deployment**: Push to Git → Render deploys automatically  
✅ **Local Development**: Simple override with `.local` files  
✅ **No Confusion**: Clear separation between environments  

## Deployment Flow

1. **Develop Locally**: `docker-compose -f docker-compose.local.yml up`
2. **Push to Git**: Default files are production-ready
3. **Deploy on Render**: Uses `Dockerfile` and environment variables
4. **Scale**: Use `docker-compose.yml` for self-hosted production
