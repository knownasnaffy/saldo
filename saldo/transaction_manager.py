"""
Business logic layer for Saldo application.

Handles transaction processing, balance calculations, and core business operations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .database import DatabaseManager
from .models import Configuration, Transaction
from .exceptions import ValidationError, ConfigurationError, DatabaseError


class TransactionManager:
    """Manages transaction processing and business logic for the Saldo application."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize TransactionManager with database manager.
        
        Args:
            db_manager: Optional DatabaseManager instance. Creates new one if None.
        """
        self.db_manager = db_manager or DatabaseManager()
        self.db_manager.initialize_database()
    
    def setup_account(self, rate: float, initial_balance: float) -> None:
        """
        Initialize rate and balance configuration for the account.
        
        Args:
            rate: Fixed rate per clothing item (must be positive)
            initial_balance: Starting balance (positive = owed, negative = credit)
            
        Raises:
            ValidationError: If rate is not positive or inputs are invalid
            DatabaseError: If database operation fails
        """
        # Validate inputs
        if not isinstance(rate, (int, float)):
            raise ValidationError("Rate must be a number")
        
        if rate <= 0:
            raise ValidationError("Rate per item must be positive")
        
        if not isinstance(initial_balance, (int, float)):
            raise ValidationError("Initial balance must be a number")
        
        # Create configuration object for validation
        config = Configuration(
            rate_per_item=float(rate),
            initial_balance=float(initial_balance),
            created_at=datetime.now()
        )
        
        # Save to database
        try:
            self.db_manager.save_configuration(config.rate_per_item, config.initial_balance)
        except Exception as e:
            raise DatabaseError(f"Failed to save account configuration: {e}")
    
    def calculate_cost(self, items: int) -> float:
        """
        Calculate total cost for a given number of items.
        
        Args:
            items: Number of clothing items (must be non-negative integer)
            
        Returns:
            Total cost (items * rate_per_item)
            
        Raises:
            ValidationError: If items is invalid
            ConfigurationError: If no configuration exists
            DatabaseError: If database operation fails
        """
        # Validate input
        if not isinstance(items, int):
            raise ValidationError("Number of items must be an integer")
        
        if items < 0:
            raise ValidationError("Number of items cannot be negative")
        
        # Get configuration
        try:
            config_data = self.db_manager.get_configuration()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve configuration: {e}")
        
        if not config_data:
            raise ConfigurationError("No configuration found. Please run setup first.")
        
        rate = config_data['rate_per_item']
        return float(items * rate)
    
    def add_transaction(self, items: int, payment: float) -> Dict[str, Any]:
        """
        Handle new transaction with balance updates.
        
        Args:
            items: Number of clothing items processed (must be non-negative integer)
            payment: Amount paid by user (can be any number)
            
        Returns:
            Dictionary with transaction details including new balance
            
        Raises:
            ValidationError: If inputs are invalid
            ConfigurationError: If no configuration exists
            DatabaseError: If database operation fails
        """
        # Validate inputs
        if not isinstance(items, int):
            raise ValidationError("Number of items must be an integer")
        
        if items < 0:
            raise ValidationError("Number of items cannot be negative")
        
        if not isinstance(payment, (int, float)):
            raise ValidationError("Payment amount must be a number")
        
        # Get current configuration and balance
        config_data = self._get_configuration()
        current_balance = self.get_current_balance()
        
        # Calculate cost and new balance
        cost = self.calculate_cost(items)
        new_balance = current_balance + cost - payment
        
        # Create transaction record
        transaction_data = {
            'items': items,
            'cost': cost,
            'payment': float(payment),
            'balance_after': new_balance,
            'created_at': datetime.now()
        }
        
        # Save transaction to database
        try:
            transaction_id = self.db_manager.save_transaction(transaction_data)
            transaction_data['id'] = transaction_id
        except Exception as e:
            raise DatabaseError(f"Failed to save transaction: {e}")
        
        return transaction_data
    
    def get_current_balance(self) -> float:
        """
        Retrieve current balance with transaction history.
        
        Returns:
            Current balance amount (positive = owed, negative = credit)
            
        Raises:
            ConfigurationError: If no configuration exists
            DatabaseError: If database operation fails
        """
        # Ensure configuration exists
        self._get_configuration()
        
        # Get current balance from database
        try:
            return self.db_manager.get_current_balance()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve current balance: {e}")
    
    def _get_configuration(self) -> Dict[str, Any]:
        """
        Get current configuration from database.
        
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationError: If no configuration exists
            DatabaseError: If database operation fails
        """
        try:
            config_data = self.db_manager.get_configuration()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve configuration: {e}")
        
        if not config_data:
            raise ConfigurationError("No configuration found. Please run setup first.")
        
        return config_data