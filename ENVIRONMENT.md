# Environment Configuration

## Development Setup

### Local Development

Create a `.env` file in the **backend** directory for backend configuration:

```bash
cd backend
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
```

Environment variables for backend/.env:

```bash
# LLM Configuration (Required)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Analysis Configuration (Optional)
TOP_FILES=40
COMPONENT_COUNT=8
CHUNK_SIZE_CHARS=1400

# Database Configuration (auto-configured with Docker)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/repo_architect
SQL_DEBUG=false

# Git and Storage Configuration
WORK_DIR=/tmp/repo-architect
```

### Starting Services

```bash
# Backend (from backend directory)
cd backend
docker-compose up --build

# Frontend (from frontend directory)
cd frontend
npm install && npm run dev
```

### Alternative: Manual PostgreSQL Setup

If running PostgreSQL manually instead of Docker:

```bash
# In backend/.env file
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
TOP_FILES=40
COMPONENT_COUNT=8
CHUNK_SIZE_CHARS=1400
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/repo_architect
SQL_DEBUG=false
WORK_DIR=/tmp/repo-architect
```

## Production Deployment

### Backend (Render)

Set these environment variables in your Render service:

**Important**: Set **Root Directory** to `backend` in Render settings!

**Required:**
- `GEMINI_API_KEY` - Your Google Gemini API key
- `DATABASE_URL` - Auto-provided by Render PostgreSQL add-on

**Optional (with defaults):**
- `GEMINI_MODEL=gemini-1.5-flash`
- `TOP_FILES=40`
- `COMPONENT_COUNT=8`
- `CHUNK_SIZE_CHARS=1400`
- `WORK_DIR=/tmp/repo-architect`
- `SQL_DEBUG=false`

### Frontend (Vercel)

Set these environment variables in your Vercel project:

**Required:**
- `NEXT_PUBLIC_API_URL` - Your deployed backend URL (e.g., `https://your-app.onrender.com/api`)

Example Vercel environment variables:
```bash
NEXT_PUBLIC_API_URL=https://repo-architect-backend.onrender.com/api
```

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and set it as `GEMINI_API_KEY`

## Default Values

If not specified, the following defaults will be used:
- `GEMINI_MODEL`: `gemini-1.5-flash`
- `TOP_FILES`: `40`
- `COMPONENT_COUNT`: `8`
- `CHUNK_SIZE_CHARS`: `1400`
- `DATABASE_URL`: `postgresql://postgres:postgres@postgres:5432/repo_architect` (Docker)
- `WORK_DIR`: `/tmp/repo-architect`

## Database Setup

### Development
The PostgreSQL database is automatically initialized with Docker Compose using the migration file at `backend/migrations/001_initial_schema.sql`.

```bash
cd backend
docker-compose up --build
```

### Production
When deploying to Render:
1. Add a PostgreSQL add-on to your service
2. Set Root Directory to `backend`
3. The `DATABASE_URL` will be automatically provided
4. The database schema will be initialized on first run

## Quick Setup Checklist

### Development
- [ ] Docker and Docker Compose installed
- [ ] Navigate to backend directory: `cd backend`
- [ ] Create `.env` file with `GEMINI_API_KEY`
- [ ] Run `docker-compose up --build`
- [ ] Navigate to frontend directory: `cd ../frontend`
- [ ] Run `npm install && npm run dev`

### Production
- [ ] Backend deployed to Render with Docker
- [ ] **Root Directory set to `backend`** (crucial!)
- [ ] PostgreSQL add-on enabled on Render
- [ ] Environment variables set on Render
- [ ] Frontend deployed to Vercel
- [ ] `NEXT_PUBLIC_API_URL` set on Vercel

## Folder Structure

```
code-architecture-mapper/
├── backend/                # Self-contained backend
│   ├── .env               # Backend environment variables
│   ├── docker-compose.yml # Backend services
│   ├── Dockerfile         # Backend container
│   └── ...
├── frontend/              # Frontend application
│   └── ...
└── README.md             # Main documentation
``` 