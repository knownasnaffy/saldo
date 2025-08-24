# Saldo - Balance Tracking Application

A command-line balance tracking application for managing financial transactions with an ironing service provider.

## Features

- Track clothing items processed and calculate costs at a fixed rate
- Manage payments and maintain accurate running balances
- Store transaction history persistently using SQLite
- View current balance and recent transaction history

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install the package:
   ```bash
   pip install -e .
   ```

## Usage

### Initial Setup

```bash
saldo setup
```

### Add Transaction

```bash
saldo add-transaction
```

### Check Balance

```bash
saldo balance
```

## Development

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=saldo
```

## Requirements

- Python 3.7+
- Linux operating system
- SQLite (included with Python)
