# Technology Stack

## Core Technologies

- **Python 3.7+** - Primary language with dataclasses support
- **Click** - CLI framework for command handling and user interaction
- **SQLite3** - Built-in database for persistent storage (no external dependency)
- **pytest** - Testing framework for unit and integration tests

## Project Structure

```
saldo/
├── saldo/                   # Main package directory
│   ├── __init__.py
│   ├── cli.py              # Click CLI commands
│   ├── transaction_manager.py # Business logic layer
│   ├── database.py         # SQLite operations
│   ├── models.py           # Data structures (dataclasses)
│   └── exceptions.py       # Custom exception hierarchy
├── tests/                  # Test suite
├── setup.py               # Package configuration
├── requirements.txt       # Dependencies
└── README.md             # Documentation
```

## Architecture Pattern

Layered architecture with clear separation:

- CLI Interface (Click commands)
- Business Logic (Transaction management)
- Data Access Layer (SQLite operations)
- Data Storage (SQLite database)

## Common Commands

### Development Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=saldo

# Run specific test file
pytest tests/test_database.py
```

### Package Installation

```bash
# Install from source
pip install -e .

# Verify CLI availability
saldo --help
```

## Data Storage

- Database location: `~/.saldo/saldo.db`
- Automatic directory creation on first run
- SQLite schema with configuration and transactions tables
