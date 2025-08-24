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
                self._connection = sqlite3.connect(self.db_path)
                self._connection.row_factory = sqlite3.Row  # Enable dict-like access
            except sqlite3.Error as e:
                raise DatabaseError(f"Failed to connect to database: {e}")
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
                    rate_per_item REAL NOT NULL,
                    initial_balance REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    items INTEGER NOT NULL,
                    cost REAL NOT NULL,
                    payment REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database: {e}") 
   
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
            
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Delete existing configuration (single row table)
            cursor.execute("DELETE FROM configuration")
            
            # Insert new configuration
            cursor.execute("""
                INSERT INTO configuration (rate_per_item, initial_balance)
                VALUES (?, ?)
            """, (rate, initial_balance))
            
            conn.commit()
            
        except sqlite3.Error as e:
            conn.rollback()
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
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO transactions (items, cost, payment, balance_after)
                VALUES (?, ?, ?, ?)
            """, (
                transaction['items'],
                transaction['cost'],
                transaction['payment'],
                transaction['balance_after']
            ))
            
            conn.commit()
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to save transaction: {e}")
    
    def get_transactions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transactions from database.
        
        Args:
            limit: Optional limit on number of transactions to return
            
        Returns:
            List of transaction dictionaries, ordered by creation date (newest first)
        """
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
                return row['balance_after']
            
            # If no transactions, get initial balance from configuration
            config = self.get_configuration()
            if config:
                return config['initial_balance']
            
            # If no configuration exists, return 0
            return 0.0
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get current balance: {e}")