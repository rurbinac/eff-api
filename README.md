# EFF (Fantasy Football) Platform

A fantasy football application built with FastAPI, SQLModel, and Google Cloud Run.

## Overview

The EFF platform manages fantasy football leagues with support for:
- User authentication (sign in, sign up, profile management)
- League management (create, join, view leagues)
- Team management (roster management, player selection)
- Real-world data synchronization (players, matches, standings)
- Gaming API endpoints for integration with gaming platforms

## Architecture

### Core Components

- **app/main.py** - FastAPI application entry point
- **app/database.py** - Database configuration and session management
- **app/models.py** - SQLModel data models
- **app/context.py** - Request context management
- **app/constants.py** - Application constants and configuration

### Services

Located in `app/services/`:

- **sync_fantasy.py** - Synchronizes fantasy football application data (leagues, divisions, teams, matches)
- **sync_real.py** - Synchronizes real-world data from external sources (competitions, teams, players, matches, standings)
- **sync_standings.py** - Calculates and manages league standings with member statistics
- **query.py** - Common database queries and validations

### Actions

Located in `app/actions/` - Business logic for API endpoints:

- **sign.py** - Authentication actions (sign in, sign out, sign up, profile updates)
- **leagues.py** - League management (create, read, join)
- **divisions.py** - Division operations
- **teams.py** - Team roster and member management
- **division_notes.py** - Division-level notes and communications
- **lookups.py** - Reference data lookups

### Utilities

Located in `app/utils/`:

- **member_keys.py** - Fantasy team roster management with position-based constraints and draft operations

### Routers

Located in `app/routers/` - API endpoint definitions:

- **auth.py** - Authentication endpoints
- **leagues.py** - League endpoints
- **divisions.py** - Division endpoints
- **teams.py** - Team endpoints
- **gaming_api.py** - Gaming platform integration endpoints
- **legacy.py** - Legacy PHP-compatible endpoints
- And others for specific resources

## Installation

### Prerequisites

- Python 3.14+
- SQLite or MySQL
- Google Cloud CLI (for deployment)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations (if needed)
python -m alembic upgrade head

# Run the development server
uvicorn app.main:app --reload
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_auth_actions.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app
```

### Test Database

Tests use a temporary SQLite database (`test_eff.db`) that is created and destroyed for each test session.

## Sync Operations

The application includes comprehensive data synchronization:

### Fantasy Sync

Synchronizes application-level fantasy football data:

```python
from app.services import SyncFantasyService

sync = SyncFantasyService(db)
sync.sync_leagues(real_competition_id=3)
sync.sync_divisions(real_competition_id=3)
sync.sync_teams(real_competition_id=3)
sync.sync_matches(real_competition_id=3)
```

### Real Data Sync

Synchronizes real-world sports data from external sources:

```python
from app.services import SyncRealService

sync = SyncRealService(db)
sync.sync_competitions()
sync.sync_teams(real_competition_id=3)
sync.sync_players(real_competition_id=3)
sync.sync_matches(real_competition_id=3)
sync.sync_match_events(real_competition_id=3, match_day=1)
sync.sync_team_members(real_competition_id=3)
```

### Standings Sync

Calculates league standings and manages team member statistics:

```python
from app.services import SyncStandingsService

sync = SyncStandingsService(db)
sync.sync_standings(real_competition_id=3, match_day=1)
sync.sync_real_standings(real_competition_id=3)
```

## Team Member Management

The `MKeys` and related classes in `member_keys.py` handle:

- Position-based roster constraints (goalkeepers, defenders, midfielders, strikers)
- Min/max member counts per position
- Automatic roster allocation during drafting
- Hierarchical key management for complex roster structures

### Example Usage

```python
from app.utils import MKeys

# Create roster manager
members = TeamMembers(team_id=1)

# Check if roster change is valid
if members.can_change(remove_keys=["GK.1"], add_keys=["GK.2"]):
    members.change(remove_keys=["GK.1"], add_keys=["GK.2"])

# Check available draft positions
available = members.available_dp()  # Returns positions available to draft
```

## API Endpoints

### Authentication

- `POST /eff/eff_api/SignIn.php` - Sign in with email/password
- `POST /eff/eff_api/SignUp.php` - Create new user account
- `POST /eff/eff_api/SignOut.php` - Sign out
- `POST /api/auth/signin` - REST sign in endpoint

### Leagues

- `POST /eff/eff_api/Leagues.php?f=ReadList` - Get user's leagues
- `POST /api/leagues/readlist` - REST leagues endpoint
- `POST /gaming/api/Leagues.php?f=Build` - Create new league
- `POST /gaming/api/Leagues.php?f=Join` - Join existing league

### Teams

- `POST /eff/eff_api/Teams.php?f=ReadList` - Get teams
- `POST /api/teams/readlist` - REST teams endpoint
- `POST /gaming/api/Teams.php?f=GetCurrentMembers` - Get team roster
- `POST /gaming/api/Teams.php?f=SetRealMembersRanking` - Update player rankings

### Other Endpoints

See `IMPLEMENTED_ENDPOINTS.txt` for a complete list of legacy endpoints.

## Deployment

### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy eff-api \
  --source . \
  --region us-central1 \
  --platform managed

# View logs
gcloud run logs read eff-api --region us-central1 --limit 50
```

### Environment Variables

Required environment variables for production:

- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT secret key
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `ALLOWED_ORIGINS` - CORS allowed origins (comma-separated)

## Development

### Code Style

- Format with Black: `black app tests`
- Lint with Pylint: `pylint app tests`
- Type check with mypy: `mypy app`

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Troubleshooting

### Import Errors

If you encounter `ImportError: cannot import name 'QueryService'`, ensure:
1. The `app/services/` directory has `__init__.py` with proper imports
2. The `query.py` file exists in `app/services/`

### Database Connection Issues

Verify:
1. DATABASE_URL environment variable is set correctly
2. Database is running and accessible
3. Database user has proper permissions

### Test Failures

For test database issues:
1. Check that SQLite temporary directory has write permissions
2. Ensure no other tests are using the same database file
3. Run with `pytest -v` for detailed error messages

## Recent Changes

### Sync Services Consolidation

- Created modular sync services for fantasy and real data
- Implemented streaming XML parser for memory-efficient data loading
- Added two-pass processing for data relationships
- Integrated standings calculation with team member management

### Member Keys Management

- Implemented hierarchical key management system
- Added position-based constraint validation
- Integrated automatic draft position selection
- Created position-specific fantasy points scoring

### Import Structure

- Reorganized services into `app/services/` package
- Moved `QueryService` into dedicated `query.py` module
- Updated all imports to use new structure
- Fixed namespace conflicts between module and package names

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues and questions:
- Check existing issues in the project repository
- Review test files for usage examples
- Consult `IMPLEMENTED_ENDPOINTS.txt` for API reference
