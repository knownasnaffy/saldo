# Saldo - Balance Tracking Application

A command-line balance tracking application for managing financial transactions with an ironing service provider. Saldo helps you track clothing items processed, calculate costs at a fixed rate, manage payments, and maintain accurate running balances with persistent data storage.

## Features

- 🧾 **Transaction Tracking**: Record clothing items processed and payments made
- 💰 **Balance Management**: Maintain accurate running balances with clear owed/credit indicators
- 📊 **Cost Calculation**: Automatic cost calculation based on configurable rate per item
- 📈 **Transaction History**: View detailed transaction history with summary statistics
- 💾 **Persistent Storage**: SQLite database for reliable data persistence
- 🖥️ **User-Friendly CLI**: Interactive prompts with validation and helpful error messages

## Installation

### Prerequisites

- Python 3.7 or higher
- Linux operating system
- Git (for cloning the repository)

### Quick Install

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd saldo
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the package:**

   ```bash
   pip install -e .
   ```

4. **Verify installation:**
   ```bash
   saldo --help
   ```

### Alternative Installation

If you prefer to install dependencies separately:

```bash
# Install dependencies first
pip install -r requirements.txt

# Then install the package
pip install -e .
```

## Usage

### 1. Initial Setup

Before using Saldo, you need to configure your account with the ironing service rate and any existing balance:

```bash
# Interactive setup (recommended)
saldo setup

# Or specify values directly
saldo setup --rate 2.50 --balance 10.00
```

**Example setup session:**

```
$ saldo setup
Enter the rate per clothing item (e.g., 2.50): 2.50
Enter your current balance (positive if you owe money, negative if you have credit, 0 for new account) [0]: 15.00
✅ Account setup completed successfully!
Rate per item: ₹2.50
Initial balance: ₹15.00 (you owe)

You can now use 'saldo add-transaction' to record transactions.
```

### 2. Adding Transactions

Record new transactions when you drop off or pick up clothing:

```bash
# Interactive transaction entry (recommended)
saldo add-transaction

# Or specify values directly
saldo add-transaction --items 5 --payment 10.00
```

**Example transaction session:**

```
$ saldo add-transaction
Enter the number of clothing items processed: 3

📊 Transaction Summary:
Items processed: 3
Cost per item: ₹2.50
Total cost: ₹7.50
Previous balance: ₹15.00
Total amount due: ₹22.50

Enter payment amount (total due: ₹22.50): 20.00

✅ Transaction recorded successfully!
Payment received: ₹20.00
New balance: ₹2.50 (you owe)
Underpayment: ₹2.50 (added to balance)
```

### 3. Checking Balance

View your current balance and optionally see transaction history:

```bash
# Basic balance check
saldo balance

# Detailed view with transaction history
saldo balance --detailed

# Limit number of transactions shown
saldo balance --detailed --limit 5
```

**Example balance output:**

```
$ saldo balance --detailed
💰 Saldo Balance Summary
=========================
Rate per item: ₹2.50
Current balance: ₹2.50 (you owe)
💳 You have an outstanding balance to pay.

📋 Recent Transactions (last 3):
----------------------------------------------------------------------
Date         Items  Cost     Payment  Balance
----------------------------------------------------------------------
2024-01-15   3      ₹7.50    ₹20.00   ₹2.50
2024-01-10   5      ₹12.50   ₹12.50   ₹15.00
2024-01-05   2      ₹5.00    ₹0.00    ₹15.00
----------------------------------------------------------------------

📊 Summary (last 3 transactions):
Total items processed: 10
Total cost: ₹25.00
Total payments: ₹32.50
```

## Command Reference

### `saldo setup`

Initialize or reconfigure your account settings.

**Options:**

- `--rate FLOAT`: Rate per clothing item
- `--balance FLOAT`: Initial balance (positive = owed, negative = credit)

**Examples:**

```bash
saldo setup                           # Interactive setup
saldo setup --rate 3.00 --balance 0  # Set rate to ₹3.00, start with ₹0 balance
```

### `saldo add-transaction`

Record a new transaction with items processed and payment made.

**Options:**

- `--items INTEGER`: Number of clothing items
- `--payment FLOAT`: Payment amount

**Examples:**

```bash
saldo add-transaction                    # Interactive entry
saldo add-transaction --items 4 --payment 8.00  # 4 items, ₹8.00 payment
```

### `saldo balance`

Display current balance and account information.

**Options:**

- `-d, --detailed`: Show transaction history
- `--limit INTEGER`: Number of recent transactions to show (default: 10)

**Examples:**

```bash
saldo balance                    # Basic balance
saldo balance --detailed         # With transaction history
saldo balance -d --limit 20      # Show last 20 transactions
```

## Data Storage

Saldo stores all data in a SQLite database located at:

```
~/.saldo/saldo.db
```

The database contains:

- **Configuration**: Your rate per item and initial balance
- **Transactions**: Complete history of all transactions with timestamps

## Development

### Setting Up Development Environment

```bash
# Clone and enter directory
git clone <repository-url>
cd saldo

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=saldo

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

### Project Structure

```
saldo/
├── saldo/                   # Main package
│   ├── __init__.py
│   ├── cli.py              # Click CLI commands
│   ├── transaction_manager.py # Business logic
│   ├── database.py         # SQLite operations
│   ├── models.py           # Data models
│   └── exceptions.py       # Custom exceptions
├── tests/                  # Test suite
├── setup.py               # Package configuration
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Troubleshooting

### Common Issues

**"No configuration found" error:**

```bash
# Run setup first
saldo setup
```

**"Command not found: saldo":**

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall the package
pip install -e .
```

**Database permission errors:**

```bash
# Check ~/.saldo directory permissions
ls -la ~/.saldo/

# If needed, fix permissions
chmod 755 ~/.saldo
chmod 644 ~/.saldo/saldo.db
```

### Getting Help

- Use `--help` with any command for detailed usage information
- Check the transaction history with `saldo balance --detailed` to verify data
- All monetary amounts are displayed with 2 decimal places for clarity

## Requirements

- **Python**: 3.7 or higher
- **Operating System**: Linux (tested on Ubuntu, should work on other distributions)
- **Dependencies**: Click 7.0+ (automatically installed)
- **Storage**: SQLite (included with Python, no separate installation needed)

## License

This project is licensed under the MIT License - see the setup.py file for details.
