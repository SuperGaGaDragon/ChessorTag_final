# ChessOrTag

> A comprehensive chess analysis platform combining AI-powered style reports with intelligent study organization

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

ChessOrTag is an advanced chess analysis platform that goes beyond traditional game analysis. It generates comprehensive playing style reports, provides AI-powered move explanations, and offers an intelligent workspace for organizing chess materials. The platform analyzes your games to identify patterns, compare your style with grandmasters, and help you understand and improve your chess.

**Live Platform:** [chessortag.org](https://chessortag.org)

## Key Features

### 🎯 Chess Style Analysis
- **Comprehensive Style Reports**: Analyze your games to identify your unique playing style
- **GM Comparison**: Compare your playing patterns with grandmaster styles
- **Pattern Recognition**: Automatic detection of tactical and strategic themes
- **Visual Metrics**: Interactive charts and visualizations of your chess statistics

### 🤖 AI-Powered Insights
- **LLM Explanations**: Natural language explanations for positions and moves
- **Chess Imitator Engine**: UCI-compatible engine that plays in specific styles
- **Intelligent Analysis**: Deep learning-based position evaluation and recommendations

### 📚 Study Organization
- **Hierarchical Workspace**: Organize studies with folders and subfolders
- **Color-Coded System**: Visual organization with customizable folder colors
- **Public/Private Studies**: Control visibility and sharing of your chess materials
- **Flexible Storage**: JSON-based study storage supporting any chess data format

### 🔐 User Management
- **Secure Authentication**: JWT-based user authentication system
- **Personal Workspace**: Each user gets their own isolated study space
- **Account Persistence**: All studies and materials saved to your account

## Architecture

### Technology Stack

**Frontend:**
- HTML5, CSS3, JavaScript
- Chess.js for chess logic
- Chessboard.js for interactive boards
- Responsive design for mobile and desktop

**Backend:**
- FastAPI (Python web framework)
- PostgreSQL database
- SQLAlchemy ORM
- OpenAI API for LLM features

**Chess Analysis:**
- Python-chess library
- Custom rule-based pattern detection
- Style scoring algorithms
- UCI engine interface

### Project Structure

```
chess_report_page/
├── backend/                 # FastAPI backend server
│   ├── app.py              # Main application entry
│   ├── main.py             # FastAPI app configuration
│   ├── auth_api.py         # Authentication endpoints
│   ├── study_api.py        # Study management endpoints
│   ├── workspace_api.py    # Workspace/folder endpoints
│   ├── models.py           # Database models
│   └── auth_models.py      # User authentication models
│
├── website/                # Frontend web interface
│   ├── home/              # Homepage
│   ├── login/             # Login/signup pages
│   ├── study/             # Chess study interface
│   ├── new_report/        # Report generation UI
│   └── assets/            # JavaScript libraries and resources
│
├── style_report/          # Report generation pipeline
│   ├── report_service.py  # Main report generation logic
│   ├── explanation.py     # LLM explanation generation
│   ├── llm_client.py      # OpenAI API client
│   ├── metrics/           # Chess metrics calculation
│   ├── templates/         # HTML report templates
│   └── scripts/           # Report building scripts
│
├── chess_imitator /       # Style-based chess engine
│   ├── imitator_uci_engine.py  # UCI engine implementation
│   ├── style_scorer.py         # Style-based move scoring
│   ├── rule_tagger2/           # Move classification
│   └── players/                # Player style profiles
│
├── Work_Flow/             # Data processing workflows
│
└── requirements.txt       # Python dependencies
```

## Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Node.js (for frontend development)
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/chess_report_page.git
   cd chess_report_page
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb chessortag

   # Update database connection in backend/db.py
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file
   cp .env.example .env

   # Edit .env with your configurations:
   # - DATABASE_URL
   # - SECRET_KEY
   # - OPENAI_API_KEY
   ```

5. **Run database migrations**
   ```bash
   cd backend
   python -c "from db import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

6. **Start the backend server**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Serve the frontend**
   ```bash
   # In a new terminal
   cd website
   python -m http.server 8080
   ```

8. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Docker Deployment

```bash
# Build Docker image
docker build -t chessortag .

# Run with Docker Compose
docker-compose up -d
```

## API Documentation

### Authentication

```http
POST /auth/signup
Content-Type: application/json

{
  "username": "player123",
  "email": "player@example.com",
  "password": "securepassword"
}
```

```http
POST /auth/login
Content-Type: application/json

{
  "username": "player123",
  "password": "securepassword"
}
```

### Studies

```http
POST /studies
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Opening Study",
  "data": {...},
  "folder_id": "abc123"
}
```

```http
GET /studies/{study_id}
Authorization: Bearer <token>
```

### Workspace

```http
GET /workspace
Authorization: Bearer <token>
```

```http
POST /folders
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Opening Repertoire",
  "color": "#ff6b6b",
  "parent_id": null
}
```

For complete API documentation, visit `/docs` endpoint when running the server.

## Core Pipelines

### 1. rule_tagger2
Pattern recognition and move classification system that identifies tactical and strategic themes in chess games.

**Features:**
- Tactical motif detection (pins, forks, skewers, etc.)
- Strategic pattern recognition
- Position classification
- Move quality evaluation

### 2. chess_imitator
UCI chess engine that plays moves based on specific playing styles.

**Features:**
- Style-based move selection
- Configurable playing characteristics
- Real-time position evaluation
- Compatible with standard chess GUIs

### 3. style_report
Comprehensive report generation pipeline with AI-powered insights.

**Features:**
- Multi-dimensional style analysis
- Statistical metrics calculation
- GM comparison benchmarks
- LLM-generated explanations
- Visual report generation

## Usage Examples

### Generate a Style Report

```python
from style_report.report_service import generate_report

# Generate report from PGN
report = generate_report(
    pgn_data="1. e4 e5 2. Nf3...",
    player_name="Magnus Carlsen"
)
```

### Use Chess Imitator Engine

```bash
# Start UCI engine
python chess_imitator\ /imitator_uci_engine.py

# In your chess GUI, connect to the engine
# Configure style parameters via UCI options
```

### Create a Study via API

```javascript
const response = await fetch('http://localhost:8000/studies', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Sicilian Defense Study',
    data: {
      pgn: '1. e4 c5...',
      chapters: [...]
    }
  })
});
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_study_api.py

# Run with coverage
pytest --cov=backend
```

### Code Style

This project follows PEP 8 for Python code. Format your code using:

```bash
# Format code
black backend/ style_report/

# Lint code
flake8 backend/ style_report/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Contributing

We welcome contributions to ChessOrTag! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Guidelines

- Write clear, descriptive commit messages
- Add tests for new features
- Update documentation as needed
- Follow existing code style and conventions
- Ensure all tests pass before submitting PR

## Roadmap

- [ ] Mobile app development (iOS/Android)
- [ ] Real-time multiplayer analysis
- [ ] Integration with major chess platforms (Chess.com, Lichess)
- [ ] Advanced ML models for style prediction
- [ ] Tournament preparation tools
- [ ] Social features and study sharing
- [ ] Video analysis integration
- [ ] Custom training plans based on style analysis

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Chess.js and Chessboard.js for chess visualization
- Python-chess library for chess logic
- OpenAI for LLM capabilities
- FastAPI framework for the backend
- The chess community for inspiration and feedback

## Support

- **Documentation:** [Website Function Introduction](Website_function_introduction.txt)
- **Issues:** [GitHub Issues](https://github.com/yourusername/chess_report_page/issues)
- **Email:** support@chessortag.org
- **Website:** [chessortag.org](https://chessortag.org)

## Authors

ChessOrTag Development Team

---

Made with ♟️ by chess enthusiasts, for chess enthusiasts.
