# AI Judge for Multi-Agent Systems

A comprehensive platform for evaluating and benchmarking AI agents across different tasks.

## 📋 Project Overview

AgentBench is an advanced evaluation platform that:
- **Registers AI agents** from different providers (OpenAI, Anthropic, local, etc.)
- **Creates evaluation tasks** with expected outputs
- **Runs evaluations** and measures multiple metrics:
  - Correctness (accuracy of responses)
  - Latency (execution time)
  - Cost (API usage)
  - Hallucination rates
  - Tool usage efficiency
  - Planning quality
  - Retry counts
  - Success rates
- **Displays results** in an interactive dashboard
- **Ranks agents** on a leaderboard

## 🚀 Quick Start

### Backend Setup

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Initialize database:**
   ```bash
   alembic upgrade head
   ```

4. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
agenticbench/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── agents.py       # Agent management endpoints
│   │   │   ├── tasks.py        # Task management endpoints
│   │   │   ├── evaluations.py  # Evaluation endpoints
│   │   │   ├── auth.py         # Authentication
│   │   │   ├── users.py        # User management
│   │   │   └── benchmarks.py   # Legacy benchmarks
│   │   ├── models/
│   │   │   ├── agent.py        # Agent model
│   │   │   ├── task.py         # Task model
│   │   │   ├── evaluation.py   # Evaluation & metrics models
│   │   │   ├── user.py         # User model
│   │   │   └── benchmark.py    # Benchmark model
│   │   ├── schemas/
│   │   │   ├── agent.py        # Agent schemas
│   │   │   ├── task.py         # Task schemas
│   │   │   └── evaluation.py   # Evaluation schemas
│   │   ├── services/
│   │   │   ├── agent_service.py      # Agent business logic
│   │   │   ├── task_service.py       # Task business logic
│   │   │   ├── evaluation_service.py # Evaluation logic & metrics
│   │   │   └── benchmark_service.py  # Legacy benchmark service
│   │   ├── db/
│   │   │   ├── database.py     # Database connection
│   │   │   ├── base.py         # SQLAlchemy base
│   │   │   └── dependencies.py # DB dependencies
│   │   ├── core/
│   │   │   ├── config.py       # Configuration
│   │   │   ├── security.py     # Security utilities
│   │   │   └── dependencies.py # Dependency injection
│   │   ├── middleware/         # Custom middleware
│   │   └── main.py             # FastAPI app
│   ├── alembic/                # Database migrations
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic.ini
│
└── frontend/
    ├── src/
    │   ├── api/
    │   │   ├── client.ts       # Axios client
    │   │   └── index.ts        # API endpoints
    │   ├── components/
    │   │   ├── Layout.tsx      # Main layout
    │   │   ├── Sidebar.tsx     # Navigation sidebar
    │   │   └── Navigation.tsx  # Top navigation
    │   ├── pages/
    │   │   ├── Dashboard.tsx   # Main dashboard
    │   │   ├── Tasks.tsx       # Task management
    │   │   ├── Agents.tsx      # Agent management
    │   │   ├── Evaluations.tsx # Run evaluations
    │   │   ├── Leaderboard.tsx # Agent rankings
    │   │   └── Login.tsx       # Authentication
    │   ├── styles/
    │   │   └── globals.css
    │   ├── App.tsx
    │   └── index.tsx
    ├── index.html
    ├── tailwind.config.js
    ├── vite.config.ts
    ├── tsconfig.json
    └── package.json
```

## 🔌 API Endpoints

### Agents
- `POST /agents/` - Register a new agent
- `GET /agents/` - List all agents
- `GET /agents/{id}` - Get agent details
- `PUT /agents/{id}` - Update agent
- `DELETE /agents/{id}` - Delete agent

### Tasks
- `POST /tasks/` - Create a new task
- `GET /tasks/` - List tasks (with optional filtering)
- `GET /tasks/{id}` - Get task details
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task
- `GET /tasks/categories/list` - Get all categories

### Evaluations
- `POST /evaluations/` - Create and run evaluation
- `GET /evaluations/` - List evaluations (with optional filtering)
- `GET /evaluations/{id}` - Get evaluation details
- `POST /evaluations/{id}/calculate-metrics` - Calculate evaluation metrics
- `GET /evaluations/leaderboard/agents` - Get agent leaderboard

## 📊 Evaluation Metrics

Each evaluation is scored on:
- **Correctness (40%)**: How accurate the response is
- **Hallucination (20%)**: Absence of false information
- **Tool Usage (20%)**: Efficiency of tool and API usage
- **Planning Quality (20%)**: Quality of reasoning and planning

Overall score is a weighted average of these metrics.

## 🔐 Authentication

- Register with email and password
- Login to get JWT token
- Token is stored in localStorage
- Include token in Authorization header for protected endpoints

## 🎯 Features

- ✅ Multi-agent support
- ✅ Task creation and management
- ✅ Automated evaluation runs
- ✅ Comprehensive metrics tracking
- ✅ Agent leaderboard/rankings
- ✅ Beautiful dashboard
- ✅ Real-time updates
- ✅ User authentication
- ✅ Task categories and difficulty levels

## 🛠️ Technologies

**Backend:**
- FastAPI
- SQLAlchemy ORM
- PostgreSQL
- Alembic (migrations)
- Pydantic (validation)
- Python-Jose (JWT)

**Frontend:**
- React 18 with TypeScript
- React Router
- Tailwind CSS
- Axios
- Recharts (visualizations)
- Lucide Icons

## 📝 Environment Variables

See `.env.example` for all required environment variables. Key ones:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `ALGORITHM`: JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
- `OPENAI_API_KEY`: OpenAI API key (if using OpenAI agents)

## 🚦 Running Everything

### Option 1: Separate Terminals

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or `venv\\Scripts\\activate` on Windows
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### Option 2: Docker

```bash
docker-compose up
```

## 📚 Usage Example

1. **Register an agent:**
   ```bash
   curl -X POST http://localhost:8000/agents/ \
     -H "Content-Type: application/json" \
     -d '{
       "name": "GPT-4",
       "description": "OpenAI GPT-4",
       "api_endpoint": "https://api.openai.com/v1/chat/completions",
       "api_key": "sk-..."
     }'
   ```

2. **Create a task:**
   ```bash
   curl -X POST http://localhost:8000/tasks/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Write REST API",
       "description": "Write a simple REST API",
       "prompt": "Write a simple REST API using Python and FastAPI",
       "expected_output": "from fastapi import FastAPI...",
       "category": "Code Generation",
       "difficulty": "medium"
     }'
   ```

3. **Run an evaluation:**
   ```bash
   curl -X POST http://localhost:8000/evaluations/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "task_id": 1,
       "agent_id": 1
     }'
   ```

## 🤝 Contributing

Pull requests are welcome! Please ensure:
- Code follows the existing style
- Tests are added for new features
- Documentation is updated

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For issues, please open a GitHub issue or contact the team.
