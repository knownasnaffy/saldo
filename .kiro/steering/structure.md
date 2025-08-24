# Project Structure and Organization

## Directory Layout

```
saldo/                       # Root project directory
├── saldo/                   # Main Python package
│   ├── __init__.py         # Package initialization
│   ├── cli.py              # Click CLI commands and user interface
│   ├── transaction_manager.py # Core business logic
│   ├── database.py         # SQLite database operations
│   ├── models.py           # Data models using dataclasses
│   └── exceptions.py       # Custom exception hierarchy
├── tests/                   # Test suite directory
│   ├── test_database.py    # Database layer tests
│   ├── test_transaction_manager.py # Business logic tests
│   ├── test_cli.py         # CLI interface tests
│   └── test_integration.py # End-to-end workflow tests
├── setup.py                # Package configuration and entry points
├── requirements.txt        # Python dependencies
└── README.md              # Usage documentation and examples
```

## Code Organization Principles

### Separation of Concerns

- **CLI Layer** (`cli.py`) - User interaction, command parsing, input/output
- **Business Logic** (`transaction_manager.py`) - Core application logic, calculations
- **Data Access** (`database.py`) - SQLite operations, schema management
- **Models** (`models.py`) - Data structures and validation
- **Exceptions** (`exceptions.py`) - Error handling hierarchy

### Single Responsibility

Each module handles one specific aspect:

- CLI commands and user prompts
- Transaction processing and balance calculations
- Database CRUD operations
- Data model definitions
- Custom error types

## File Naming Conventions

- Use snake_case for Python files and functions
- Use PascalCase for class names
- Use UPPER_CASE for constants
- Test files prefixed with `test_`
- Main package directory matches project name

## Database Schema Location

- User data stored in `~/.saldo/saldo.db`
- Configuration table (single row with rate and initial balance)
- Transactions table (historical transaction records)
- Automatic directory and schema creation on first run

## Testing Structure

- Unit tests for each module in corresponding test files
- Integration tests for complete user workflows
- Test database isolation using temporary files
- CLI testing using Click's testing utilities

## Development Workflow

### Git Commit Strategy

- Commit changes as soon as they reach a stable, working state
- Each functional milestone should be committed to track progress
- Use descriptive commit messages that explain what was implemented
- Commit after completing each major task or feature component
- This helps maintain a clear development history and makes it easier to track what's working
