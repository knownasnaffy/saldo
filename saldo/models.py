"""Data models for the Saldo balance tracking application."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Configuration:
    """Configuration data for the Saldo application.
    
    Attributes:
        rate_per_item: Fixed rate charged per clothing item
        initial_balance: Starting balance (positive = owed, negative = credit)
        created_at: Timestamp when configuration was created
    """
    rate_per_item: float
    initial_balance: float
    created_at: datetime
    
    def __post_init__(self):
        """Validate configuration data after initialization."""
        if not isinstance(self.rate_per_item, (int, float)):
            raise TypeError("Rate per item must be a number")
        
        if self.rate_per_item <= 0:
            raise ValueError("Rate per item must be positive")
        
        if not isinstance(self.initial_balance, (int, float)):
            raise TypeError("Initial balance must be a number")


@dataclass
class Transaction:
    """Transaction record for the Saldo application.
    
    Attributes:
        id: Unique transaction identifier (None for new transactions)
        items: Number of clothing items processed
        cost: Total cost calculated (items * rate)
        payment: Amount paid by user
        balance_after: Running balance after this transaction
        created_at: Timestamp when transaction was created
    """
    items: int
    cost: float
    payment: float
    balance_after: float
    created_at: datetime
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate transaction data after initialization."""
        if not isinstance(self.items, int):
            raise TypeError("Number of items must be an integer")
        
        if self.items < 0:
            raise ValueError("Number of items cannot be negative")
        
        if not isinstance(self.cost, (int, float)):
            raise TypeError("Cost must be a number")
        
        if self.cost < 0:
            raise ValueError("Cost cannot be negative")
        
        if not isinstance(self.payment, (int, float)):
            raise TypeError("Payment must be a number")
        
        if not isinstance(self.balance_after, (int, float)):
            raise TypeError("Balance after must be a number")