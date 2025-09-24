# AI Agents Platform

A modern FastAPI-based platform for creating, managing, and orchestrating AI agents. This repository provides a robust foundation for building AI agent systems with support for standalone agents and agent dependencies.

## 🚀 Features

- **Modern Architecture**: Clean separation of concerns with Repository, Service, and Controller layers
- **Agent Management**: Create, update, delete, and monitor AI agents
- **Agent Dependencies**: Support for agent-to-agent dependencies and orchestration
- **Execution Tracking**: Complete execution history and performance monitoring
- **Memory System**: Persistent memory storage for agents
- **Async Support**: Full async/await support for high performance
- **Database Integration**: PostgreSQL with SQLAlchemy ORM
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Logging**: Comprehensive logging with Loguru
- **Configuration**: Environment-based configuration management

## 📁 Project Structure

```
agents/
├── app/
│   ├── api/                    # API layer
│   │   └── v1/
│   │       ├── endpoints/      # API endpoints
│   │       └── api.py          # API router
│   ├── core/                  # Core functionality
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database setup
│   │   ├── logging.py         # Logging configuration
│   │   └── base.py            # Base classes
│   ├── models/                # Database models
│   ├── repositories/          # Data access layer
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic layer
│   └── main.py                # FastAPI application
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis (optional, for caching)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agents
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb agents_db
   
   # Initialize database tables
   python -m app.core.init_db
   ```

6. **Test the setup**
   ```bash
   python test_setup.py
   ```

7. **Run the application**
   ```bash
   # Option 1: Using the run script
   python run.py
   
   # Option 2: Direct module execution
   python -m app.main
   ```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

## 🔧 Configuration

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/agents_db

# API
API_V1_STR=/api/v1
PROJECT_NAME=AI Agents Platform
DEBUG=True

# AI Providers
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Agent Configuration
DEFAULT_AGENT_TIMEOUT=300
MAX_CONCURRENT_AGENTS=10
```

## 📚 API Usage

### Creating an Agent

```bash
curl -X POST "http://localhost:8000/api/v1/agents/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "text-summarizer",
    "description": "Summarizes long text documents",
    "agent_type": "llm",
    "config": {
      "model": "gpt-3.5-turbo",
      "max_tokens": 1000
    }
  }'
```

### Executing an Agent

```bash
curl -X POST "http://localhost:8000/api/v1/agents/{agent_id}/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-uuid",
    "input_data": {
      "text": "Your text to summarize here..."
    }
  }'
```

### Adding Agent Dependencies

```bash
curl -X POST "http://localhost:8000/api/v1/agents/{agent_id}/dependencies" \
  -H "Content-Type: application/json" \
  -d '{
    "depends_on_agent_id": "dependency-agent-uuid",
    "dependency_type": "required"
  }'
```

## 🏗️ Architecture

### Repository Layer
- Handles all database operations
- Provides clean abstraction over SQLAlchemy
- Supports async operations

### Service Layer
- Contains business logic
- Validates data and enforces rules
- Orchestrates multiple repositories

### Controller Layer (API Endpoints)
- Handles HTTP requests/responses
- Validates input/output schemas
- Manages error handling

### Agent System
- Base `AgentBase` class for custom agents
- Support for agent dependencies
- Memory management system
- Execution tracking and monitoring

## 🔌 Creating Custom Agents

To create a custom agent, inherit from `AgentBase`:

```python
from app.core.base import AgentBase

class CustomAgent(AgentBase):
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name, "Custom agent description")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Your agent logic here
        result = self.process_input(input_data)
        return {"output": result}
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        # Validate input data
        return "required_field" in input_data
    
    def process_input(self, data: Dict[str, Any]) -> str:
        # Your processing logic
        return "processed result"
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_agents.py
```

## 📊 Monitoring

The platform includes comprehensive logging and monitoring:

- **Request timing**: X-Process-Time header
- **Structured logging**: JSON format with Loguru
- **Error tracking**: Global exception handling
- **Health checks**: `/health` endpoint

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "app.main"]
```

### Environment Variables

Ensure all required environment variables are set in production:

- `DATABASE_URL`
- `SECRET_KEY`
- `OPENAI_API_KEY` (if using OpenAI)
- `ANTHROPIC_API_KEY` (if using Anthropic)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the example agents in the `examples/` directory

## 🔮 Roadmap

- [ ] Agent marketplace
- [ ] Visual agent workflow builder
- [ ] Advanced scheduling and cron jobs
- [ ] Multi-tenant support
- [ ] Agent performance analytics
- [ ] Integration with more AI providers
- [ ] WebSocket support for real-time updates
