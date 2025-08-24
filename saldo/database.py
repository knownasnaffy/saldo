"""
Database layer for Saldo application.

Handles SQLite database operations, schema management, and data persistence.
"""

import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .exceptions import DatabaseError


class DatabaseManager:
    """Manages SQLite database operations for the Saldo application."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize DatabaseManager with database path.
        
        Args:
            db_path: Optional custom database path. Defaults to ~/.saldo/saldo.db
        """
        if db_path is None:
            # Create ~/.saldo directory if it doesn't exist
            saldo_dir = Path.home() / '.saldo'
            saldo_dir.mkdir(exist_ok=True)
            self.db_path = str(saldo_dir / 'saldo.db')
        else:
            self.db_path = db_path
            
        self._connection = None
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection, creating it if necessary."""
        if self._connection is None:
            try:
                # Check if directory exists and is writable
                db_dir = os.path.dirname(self.db_path)
                if db_dir and not os.path.exists(db_dir):
                    try:
                        os.makedirs(db_dir, exist_ok=True)
                    except OSError as e:
                        raise DatabaseError(f"Cannot create database directory: {e}", 
                                          f"Please check permissions for: {db_dir}")
                
                self._connection = sqlite3.connect(self.db_path)
                self._connection.row_factory = sqlite3.Row  # Enable dict-like access
                
                # Test the connection
                self._connection.execute("SELECT 1")
                
            except sqlite3.Error as e:
                raise DatabaseError(f"Failed to connect to database: {e}", 
                                  f"Database path: {self.db_path}")
            except OSError as e:
                raise DatabaseError(f"Database file access error: {e}", 
                                  f"Please check permissions for: {self.db_path}")
        return self._connection
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def initialize_database(self) -> None:
        """
        Create database tables with proper schema.
        
        Creates configuration and transactions tables if they don't exist.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create configuration table (single row)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuration (
                    id INTEGER PRIMARY KEY,
                    rate_per_item REAL NOT NULL CHECK(rate_per_item > 0),
                    initial_balance REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create transactions table with constraints
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    items INTEGER NOT NULL CHECK(items >= 0),
                    cost REAL NOT NULL CHECK(cost >= 0),
                    payment REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
        except sqlite3.Error as e:
            if "database is locked" in str(e).lower():
                raise DatabaseError(f"Database is locked by another process: {e}", 
                                  "Please close other instances of the application")
            elif "disk" in str(e).lower() or "space" in str(e).lower():
                raise DatabaseError(f"Insufficient disk space: {e}", 
                                  "Please free up disk space and try again")
            else:
                raise DatabaseError(f"Failed to initialize database: {e}", 
                                  f"Database path: {self.db_path}") 
   
    def save_configuration(self, rate: float, initial_balance: float) -> None:
        """
        Save configuration data to database.
        
        Args:
            rate: Rate per clothing item
            initial_balance: Initial balance amount
            
        Raises:
            DatabaseError: If database operation fails
            ValueError: If rate is not positive
        """
        if rate <= 0:
            raise ValueError("Rate must be positive")
        
        # Additional validation
        if not isinstance(rate, (int, float)) or not isinstance(initial_balance, (int, float)):
            raise ValueError("Rate and initial balance must be numbers")
            
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Delete existing configuration (single row table)
            cursor.execute("DELETE FROM configuration")
            
            # Insert new configuration
            cursor.execute("""
                INSERT INTO configuration (rate_per_item, initial_balance)
                VALUES (?, ?)
            """, (float(rate), float(initial_balance)))
            
            conn.commit()
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "rate_per_item" in str(e):
                raise DatabaseError("Rate must be positive", f"Database constraint violation: {e}")
            else:
                raise DatabaseError(f"Data integrity error: {e}")
        except sqlite3.Error as e:
            conn.rollback()
            if "database is locked" in str(e).lower():
                raise DatabaseError("Database is locked by another process", 
                                  "Please close other instances of the application")
            else:
                raise DatabaseError(f"Failed to save configuration: {e}")
    
    def get_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Get configuration data from database.
        
        Returns:
            Dictionary with configuration data or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT rate_per_item, initial_balance, created_at
                FROM configuration
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                return {
                    'rate_per_item': row['rate_per_item'],
                    'initial_balance': row['initial_balance'],
                    'created_at': row['created_at']
                }
            return None
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get configuration: {e}")
    
    def save_transaction(self, transaction: Dict[str, Any]) -> int:
        """
        Save transaction data to database.
        
        Args:
            transaction: Dictionary with transaction data
            
        Returns:
            ID of the saved transaction
            
        Raises:
            DatabaseError: If database operation fails
        """
        required_fields = ['items', 'cost', 'payment', 'balance_after']
        for field in required_fields:
            if field not in transaction:
                raise ValueError(f"Missing required field: {field}")
        
        # Additional validation
        try:
            items = int(transaction['items'])
            cost = float(transaction['cost'])
            payment = float(transaction['payment'])
            balance_after = float(transaction['balance_after'])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid transaction data types: {e}")
        
        if items < 0:
            raise ValueError("Items cannot be negative")
        if cost < 0:
            raise ValueError("Cost cannot be negative")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO transactions (items, cost, payment, balance_after)
                VALUES (?, ?, ?, ?)
            """, (items, cost, payment, balance_after))
            
            conn.commit()
            return cursor.lastrowid
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "items" in str(e):
                raise DatabaseError("Items must be non-negative", f"Database constraint violation: {e}")
            elif "cost" in str(e):
                raise DatabaseError("Cost must be non-negative", f"Database constraint violation: {e}")
            else:
                raise DatabaseError(f"Data integrity error: {e}")
        except sqlite3.Error as e:
            conn.rollback()
            if "database is locked" in str(e).lower():
                raise DatabaseError("Database is locked by another process", 
                                  "Please close other instances of the application")
            else:
                raise DatabaseError(f"Failed to save transaction: {e}")
    
    def get_transactions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transactions from database.
        
        Args:
            limit: Optional limit on number of transactions to return
            
        Returns:
            List of transaction dictionaries, ordered by creation date (newest first)
        """
        # Validate limit parameter
        if limit is not None:
            if not isinstance(limit, int):
                raise ValueError("Limit must be an integer")
            if limit < 0:
                raise ValueError("Limit cannot be negative")
            if limit > 10000:
                raise ValueError("Limit is too large (maximum 10000)")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, items, cost, payment, balance_after, created_at
                FROM transactions
                ORDER BY created_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [
                {
                    'id': row['id'],
                    'items': row['items'],
                    'cost': row['cost'],
                    'payment': row['payment'],
                    'balance_after': row['balance_after'],
                    'created_at': row['created_at']
                }
                for row in rows
            ]
            
        except sqlite3.Error as e:
            if "database is locked" in str(e).lower():
                raise DatabaseError("Database is locked by another process", 
                                  "Please close other instances of the application")
            else:
                raise DatabaseError(f"Failed to get transactions: {e}")
    
    def get_current_balance(self) -> float:
        """
        Get current balance from the most recent transaction or initial balance.
        
        Returns:
            Current balance amount
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Try to get balance from most recent transaction
            # Order by id DESC as well to ensure we get the most recent
            cursor.execute("""
                SELECT balance_after
                FROM transactions
                ORDER BY id DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                balance = row['balance_after']
                # Validate the balance value
                if not isinstance(balance, (int, float)):
                    raise DatabaseError("Invalid balance data in database", 
                                      f"Balance value: {balance} (type: {type(balance)})")
                return float(balance)
            
            # If no transactions, get initial balance from configuration
            config = self.get_configuration()
            if config:
                balance = config['initial_balance']
                if not isinstance(balance, (int, float)):
                    raise DatabaseError("Invalid initial balance in configuration", 
                                      f"Balance value: {balance} (type: {type(balance)})")
                return float(balance)
            
            # If no configuration exists, return 0
            return 0.0
            
        except sqlite3.Error as e:
            if "database is locked" in str(e).lower():
                raise DatabaseError("Database is locked by another process", 
                                  "Please close other instances of the application")
            else:
                raise DatabaseError(f"Failed to get current balance: {e}")