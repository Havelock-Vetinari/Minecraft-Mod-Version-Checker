# Mods Checker Project Documentation

## Project Structure

The project follows a modular layered architecture to ensure separation of concerns and maintainability.

```text
.
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point & assembly
│   ├── core/                # Core configuration & infrastructure
│   │   ├── config.py        # Environment variables
│   │   └── database.py      # Database connection & session management
│   ├── models/              # SQLAlchemy ORM models
│   │   └── all.py           # Domain entities (MCVersion, Mod, etc.)
│   ├── schemas/             # Pydantic data transfer objects
│   │   └── all.py           # Request/Response schemas
│   ├── services/            # Business logic & external integrations
│   │   ├── modrinth.py      # Modrinth API client
│   │   └── background.py    # Periodic background tasks
│   └── routers/             # API Endpoints
│       ├── versions.py      # version management
│       ├── mods.py          # mod tracking management
│       └── results.py       # viewing results & logs
├── tests/                   # Test suite (pytest)
├── docker-compose.yml       # Docker deployment config
└── Dockerfile               # Container build definition
```

## Key Components

### Core
- **Database**: Uses SQLite with SQLAlchemy.
- **Config**: Settings managed via Pydantic BaseSettings, supporting `.env` files and environment variables.

### Services
- **Modrinth Service**: Handles all interactions with the Modrinth API.
- **Background Service**: Runs periodic checks to update mod compatibility status.

### API
- Built with FastAPI.
- Routers are separated by resource (Versions, Mods, Results).

## Development

- **Run Locally**: `uvicorn app.main:app --reload`
- **Run Tests**: `pytest`
- **Docker**: `docker-compose up --build`
