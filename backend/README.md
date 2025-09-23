# Code Architecture Mapper - Backend

FastAPI backend service for analyzing GitHub repositories and generating architecture documentation using Google Gemini AI.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Local Development

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd code-architecture-mapper/backend
   
   # Create environment file
   echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
   ```

2. **Start services**
   ```bash
   docker-compose up --build
   ```

3. **Access the API**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 🌐 Deployment

### Deploy to Render

1. **Connect Repository**: Link your GitHub repository to Render
2. **Create Web Service**: Choose "Docker" environment
3. **Set Root Directory**: Set to `backend` (important!)
4. **Environment Variables**: 
   - `GEMINI_API_KEY` (required)
   - `DATABASE_URL` (auto-provided by PostgreSQL add-on)
5. **Add PostgreSQL**: Enable PostgreSQL add-on
6. **Deploy**: Auto-deploys on git push

### Deploy to Railway/Heroku

Similar setup - ensure the root directory is set to `backend` folder.

## 🔧 Environment Variables

### Required
- `GEMINI_API_KEY` - Your Google Gemini API key

### Optional (with defaults)
- `GEMINI_MODEL=gemini-1.5-flash`
- `TOP_FILES=40`
- `COMPONENT_COUNT=8` 
- `CHUNK_SIZE_CHARS=1400`
- `WORK_DIR=/tmp/repo-architect`
- `SQL_DEBUG=false`

### Database
- `DATABASE_URL` - PostgreSQL connection string (auto-provided by hosting platforms)

## 📊 API Endpoints

- `POST /api/analyze` - Start repository analysis
- `GET /api/analysis/{id}` - Get analysis results  
- `GET /api/examples` - List example repositories
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation

## 🗄️ Database

Uses PostgreSQL with automatic schema initialization via `migrations/001_initial_schema.sql`.

**Tables:**
- `analyses` - Repository analysis results
- `files` - File metrics and centrality data
- `examples` - Example repositories

## 🛠️ Development

### Local Development with Docker
```bash
# Start services
docker-compose up --build

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Access database
docker-compose exec postgres psql -U postgres -d repo_architect

# Stop services
docker-compose down
```

### Manual Setup (Alternative)
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY=your_key
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/repo_architect

# Run migrations
psql -U postgres -d repo_architect -f migrations/001_initial_schema.sql

# Start server
uvicorn backend.app:app --reload --port 8000
```

## 🧪 Testing

```bash
# Run tests
python -m pytest

# Test API endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/encode/uvicorn"}'
```

## 📚 Dependencies

- FastAPI 0.111.0 - Web framework
- SQLAlchemy 2.0.23 - ORM
- psycopg2-binary 2.9.9 - PostgreSQL adapter
- NetworkX 3.3 - Graph analysis
- google-generativeai 0.7.2 - Gemini AI
- GitPython 3.1.43 - Git operations

## 🏗️ Architecture

```
backend/
├── app.py                 # FastAPI application
├── config.py             # Configuration
├── Dockerfile            # Container definition
├── docker-compose.yml    # Local development
├── requirements.txt      # Dependencies
├── database/             # SQLAlchemy models
├── migrations/           # Database schema
├── routes/               # API endpoints
├── services/             # Business logic
├── parsing/              # Code analysis
├── graphing/             # Graph generation
├── llm/                  # AI integration
├── storage/              # Data access
└── utils/                # Utilities
```

## 🔄 CI/CD

The backend is designed for automatic deployment:

1. **Push to main branch**
2. **Hosting platform detects changes**
3. **Builds Docker container**  
4. **Deploys automatically**
5. **Database migrations run on startup**

## 🆘 Troubleshooting

### Common Issues

**Build fails:**
- Check all dependencies in requirements.txt
- Verify Dockerfile syntax
- Ensure Python version compatibility

**Database connection errors:**
- Verify DATABASE_URL format
- Check PostgreSQL service is running
- Wait for database to be ready (health check)

**API key errors:**
- Verify GEMINI_API_KEY is set correctly
- Check API quota and billing status
- Test key with direct Gemini API call

### Performance

**Large repositories:**
- Analysis may take 1-5 minutes
- Consider implementing timeout handling
- Monitor memory usage for very large repos

**Rate limiting:**
- Gemini API has rate limits
- Implement exponential backoff
- Consider request queuing for high load

---

**Ready for deployment!** 🚀 