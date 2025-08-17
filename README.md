# Code Architecture Mapper (CAM)

A full-stack application that analyzes GitHub repositories and generates comprehensive architecture documentation, visualizations, and metrics. Built with Python FastAPI backend and TypeScript Next.js frontend.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose (for backend development)
- Node.js 18+ (for frontend development)
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Local Development Setup

1. **Clone and configure**
   ```bash
   git clone <repository-url>
   cd code-architecture-mapper
   ```

2. **Start backend with Docker**
   ```bash
   cd backend
   echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
   docker-compose up --build
   ```

3. **Start frontend locally**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Usage
1. Open http://localhost:3000
2. Enter a GitHub repository URL
3. Click "Analyze Repository"
4. Explore results across different tabs
5. Download reports and diagrams as needed

## 🌐 Deployment Strategy

This project is designed for modern cloud deployment with independent services:

- **Frontend**: Deploy to [Vercel](https://vercel.com) (recommended)
- **Backend**: Deploy to [Render](https://render.com) using Docker from `/backend` folder
- **Database**: PostgreSQL on Render or any cloud PostgreSQL provider

### Deploy Frontend to Vercel
```bash
cd frontend
vercel --prod
# Set NEXT_PUBLIC_API_URL to your deployed backend URL
```

### Deploy Backend to Render
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. **Set Root Directory to `backend`** (important!)
4. Use Docker environment
5. Set environment variables (GEMINI_API_KEY, DATABASE_URL, etc.)
6. Add PostgreSQL add-on
7. Deploy automatically on git push

## 🏗️ Architecture Overview

### Backend (Python FastAPI) - `/backend`
- **Self-contained deployment** with own docker-compose.yml
- **Repository analysis** for Python, TypeScript, and JavaScript codebases
- **LLM integration** with Google Gemini for architecture documentation
- **Graph analysis** using NetworkX for dependency mapping
- **PostgreSQL database** for persistent storage
- **Dockerized deployment** ready for cloud platforms

### Frontend (TypeScript Next.js) - `/frontend`
- **Modern React application** with responsive design
- **Tabbed interface** with four sections:
  - **Overview**: AI-generated architecture documentation
  - **Components**: Placeholder for future component analysis
  - **Diagrams**: Interactive Mermaid diagrams
  - **Files**: Sortable table of file metrics
- **Environment-aware API calls** (localhost for dev, cloud for prod)
- **Vercel-optimized** for seamless deployment

## 📁 Project Structure

```
code-architecture-mapper/
├── backend/                    # Self-contained Python FastAPI backend
│   ├── app.py                 # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── Dockerfile             # Backend container configuration
│   ├── docker-compose.yml     # Backend + PostgreSQL orchestration
│   ├── requirements.txt       # Python dependencies
│   ├── README.md              # Backend-specific documentation
│   ├── database/              # Database models and connection
│   ├── migrations/            # Database migrations
│   ├── routes/                # API endpoints
│   ├── services/              # Business logic
│   ├── parsing/               # Code parsing utilities
│   ├── graphing/              # Graph analysis and Mermaid generation
│   ├── llm/                   # LLM integration
│   ├── storage/               # Data access layer
│   └── utils/                 # Utilities
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js app router
│   │   ├── components/        # React components
│   │   ├── lib/               # Client libraries
│   │   └── types/             # TypeScript types
│   └── package.json           # Node.js dependencies
├── .gitignore                 # Git ignore patterns
└── README.md                  # This file
```

## 🔧 Development Setup

### Backend Development (Self-contained)

```bash
cd backend

# Create environment file
echo "GEMINI_API_KEY=your_key_here" > .env

# Start backend services
docker-compose up --build

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Stop services
docker-compose down
```

### Frontend Development (Local)

```bash
cd frontend

# Install and start
npm install
npm run dev

# Build for production
npm run build
npm start
```

### Alternative: Manual Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY=your_api_key_here
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/repo_architect

# Run migrations (ensure PostgreSQL is running)
psql -U postgres -d repo_architect -f migrations/001_initial_schema.sql

# Start backend
uvicorn backend.app:app --reload --port 8000
```

## 🌍 Environment Configuration

### Backend Development (backend/.env)
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (defaults shown)
GEMINI_MODEL=gemini-1.5-flash
TOP_FILES=40
COMPONENT_COUNT=8
CHUNK_SIZE_CHARS=1400
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/repo_architect
WORK_DIR=/tmp/repo-architect
SQL_DEBUG=false
```

### Production Environment Variables

**Backend (Render):**
- `GEMINI_API_KEY` (required)
- `DATABASE_URL` (auto-provided by Render PostgreSQL)
- `GEMINI_MODEL`, `TOP_FILES`, etc. (optional)
- **Root Directory**: Set to `backend`

**Frontend (Vercel):**
- `NEXT_PUBLIC_API_URL` (your deployed backend URL)

## 🗄️ Database Schema

PostgreSQL with core tables:
- **analyses**: Repository analysis results and metadata
- **files**: Individual file metrics and centrality data  
- **examples**: Example repositories

Database is automatically initialized using `backend/migrations/001_initial_schema.sql`.

## 📊 Analysis Pipeline

1. **Repository Cloning**: Shallow clone of target repository
2. **File Scanning**: Identifies supported language files
3. **Import Parsing**: Extracts dependencies using AST and regex
4. **Graph Construction**: Builds dependency graph with NetworkX
5. **Metrics Calculation**: Computes centrality and dependency metrics
6. **LLM Documentation**: Generates architecture overview with Gemini
7. **Diagram Generation**: Creates Mermaid diagrams
8. **Database Storage**: Persists results in PostgreSQL

## 🔗 API Endpoints

- `POST /api/analyze` - Start repository analysis
- `GET /api/analysis/{id}` - Get analysis results
- `GET /api/examples` - List example repositories
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation

## 🎯 Key Features

### Current Features
- ✅ **Repository Analysis**: Python, TypeScript, and JavaScript codebases
- ✅ **AI Documentation**: Generated architecture overviews
- ✅ **Interactive Diagrams**: Mermaid visualizations
- ✅ **File Metrics**: Centrality and dependency analysis
- ✅ **Download Options**: Export documentation and diagrams
- ✅ **Independent Deployment**: Backend and frontend deploy separately
- ✅ **PostgreSQL Storage**: Persistent data storage

### Future Enhancements
- 🔄 **Component Analysis**: Architectural component extraction
- 🔄 **Async Processing**: Background job processing
- 🔄 **Authentication**: User accounts and analysis history
- 🔄 **Multiple Languages**: Support for more programming languages
- 🔄 **CI/CD Integration**: Automated analysis in pipelines

## 🧪 Testing

**Backend tests:**
```bash
cd backend
python -m pytest
```

**Frontend tests:**
```bash
cd frontend
npm test
```

## 📚 Dependencies

### Backend
- FastAPI 0.111.0 (Web framework)
- SQLAlchemy 2.0.23 (ORM)
- PostgreSQL via psycopg2-binary (Database)
- NetworkX 3.3 (Graph analysis)
- Google Generative AI 0.7.2 (LLM integration)

### Frontend
- Next.js 15 (React framework)
- TypeScript (Type safety)
- Tailwind CSS (Styling)
- Mermaid (Diagram rendering)
- React Markdown (Content rendering)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🆘 Troubleshooting

### Development Issues

**Backend not starting:**
- Ensure Docker is running
- Check if port 8000 is available
- Verify .env file exists in backend/ folder with GEMINI_API_KEY

**Database connection errors:**
- Wait for PostgreSQL to fully start (check `docker-compose logs postgres`)
- Verify DATABASE_URL format

**Frontend API errors:**
- Ensure backend is running on port 8000
- Check browser network tab for CORS issues

### Deployment Issues

**Render deployment fails:**
- Ensure Root Directory is set to `backend`
- Check environment variables are set
- Verify DATABASE_URL is properly configured
- Check build logs for missing dependencies

**Vercel deployment fails:**
- Ensure NEXT_PUBLIC_API_URL is set correctly
- Check if API endpoints are accessible
- Verify build succeeds locally

### Getting Help

- Check existing [Issues](../../issues)
- Create a new issue with:
  - Clear description of the problem
  - Steps to reproduce
  - Environment details
  - Error logs

---

**Ready to analyze repositories and create beautiful architecture documentation!** 🎉 