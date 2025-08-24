# Design Document

## Overview

Saldo is a Python-based command-line application that manages ironing service transactions and balance tracking. The application follows a simple CLI pattern with three main commands and uses SQLite for persistent data storage. The design emphasizes simplicity, reliability, and clear user interaction patterns.

## Architecture

The application follows a layered architecture pattern:

```
┌─────────────────────────────────────┐
│           CLI Interface             │
│        (Click Commands)             │
├─────────────────────────────────────┤
│         Business Logic              │
│    (Transaction Management)         │
├─────────────────────────────────────┤
│         Data Access Layer           │
│      (SQLite Operations)            │
├─────────────────────────────────────┤
│         Data Storage                │
│       (SQLite Database)             │
└─────────────────────────────────────┘
```

### Key Design Principles

- **Single Responsibility**: Each module handles one aspect of functionality
- **Separation of Concerns**: CLI, business logic, and data access are separate
- **Error Handling**: Graceful handling of user input and database errors
- **Data Integrity**: Transactional operations to maintain consistency

## Components and Interfaces

### CLI Interface (`cli.py`)

Uses Click library for command-line interface management:

- `saldo setup` - Initialize application with rate and balance
- `saldo add-transaction` - Add new transaction with items and payment
- `saldo balance` - Display current balance and optional history

### Business Logic (`transaction_manager.py`)

Core business logic for transaction processing:

```python
class TransactionManager:
    def setup_account(self, rate: float, initial_balance: float) -> None
    def add_transaction(self, items: int, payment: float) -> dict
    def get_current_balance(self) -> dict
    def calculate_cost(self, items: int) -> float
```

### Data Access Layer (`database.py`)

SQLite database operations and schema management:

```python
class DatabaseManager:
    def initialize_database(self) -> None
    def save_configuration(self, rate: float, initial_balance: float) -> None
    def get_configuration(self) -> dict
    def save_transaction(self, transaction: dict) -> None
    def get_transactions(self, limit: int = None) -> list
    def get_current_balance(self) -> float
```

### Models (`models.py`)

Data structures for application entities:

```python
@dataclass
class Configuration:
    rate_per_item: float
    initial_balance: float
    created_at: datetime

@dataclass
class Transaction:
    id: int
    items: int
    cost: float
    payment: float
    balance_after: float
    created_at: datetime
```

## Data Models

### Database Schema

```sql
-- Configuration table (single row)
CREATE TABLE configuration (
    id INTEGER PRIMARY KEY,
    rate_per_item REAL NOT NULL,
    initial_balance REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    items INTEGER NOT NULL,
    cost REAL NOT NULL,
    payment REAL NOT NULL,
    balance_after REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Data Flow

1. **Setup**: Store rate and initial balance in configuration table
2. **Add Transaction**: Calculate cost, store transaction, update running balance
3. **Balance Query**: Retrieve current balance from latest transaction or initial balance

## Error Handling

### Input Validation

- Numeric validation for rates, amounts, and item counts
- Range validation (positive values where required)
- Database connection error handling

### Error Categories

```python
class SaldoError(Exception):
    """Base exception for Saldo application"""

class DatabaseError(SaldoError):
    """Database operation errors"""

class ValidationError(SaldoError):
    """Input validation errors"""

class ConfigurationError(SaldoError):
    """Configuration and setup errors"""
```

### Error Recovery

- Graceful degradation for database issues
- Clear error messages with suggested actions
- Rollback capabilities for failed transactions

## Testing Strategy

### Unit Tests

- **Database operations**: CRUD operations, schema creation
- **Business logic**: Cost calculations, balance updates
- **Input validation**: Edge cases and error conditions

### Integration Tests

- **End-to-end workflows**: Setup → Add Transaction → Check Balance
- **CLI command testing**: Command parsing and output validation
- **Database persistence**: Data integrity across application restarts

### Test Structure

```
tests/
├── test_database.py          # Database layer tests
├── test_transaction_manager.py # Business logic tests
├── test_cli.py              # CLI interface tests
└── test_integration.py      # End-to-end tests
```

## Implementation Details

### File Structure

```
saldo/
├── saldo/
│   ├── __init__.py
│   ├── cli.py               # Click CLI commands
│   ├── transaction_manager.py # Business logic
│   ├── database.py          # SQLite operations
│   ├── models.py            # Data structures
│   └── exceptions.py        # Custom exceptions
├── tests/
│   └── [test files]
├── setup.py                 # Package configuration
├── requirements.txt         # Dependencies
└── README.md               # Usage documentation
```

### Dependencies

- **Click**: CLI framework for command handling
- **SQLite3**: Built-in Python database (no external dependency)
- **pytest**: Testing framework
- **dataclasses**: For model definitions (Python 3.7+)

### Configuration Management

- Database file location: `~/.saldo/saldo.db`
- Automatic directory creation on first run
- Configuration validation on startup

### User Experience Considerations

- Clear prompts with examples
- Confirmation messages for important operations
- Helpful error messages with suggested fixes
- Consistent output formatting for balance display
