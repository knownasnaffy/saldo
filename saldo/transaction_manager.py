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
        # Validate inputs with enhanced error messages
        if not isinstance(rate, (int, float)):
            raise ValidationError(
                "Rate must be a number", f"Received type: {type(rate).__name__}"
            )

        if rate <= 0:
            raise ValidationError(
                "Rate per item must be positive", f"Received value: {rate}"
            )

        # Check for extremely large values that might cause issues
        if rate > 1000:
            raise ValidationError(
                "Rate per item seems unusually high",
                f"Received value: {rate}. Please verify this is correct.",
            )

        if not isinstance(initial_balance, (int, float)):
            raise ValidationError(
                "Initial balance must be a number",
                f"Received type: {type(initial_balance).__name__}",
            )

        # Check for extremely large balance values
        if abs(initial_balance) > 1000000:
            raise ValidationError(
                "Initial balance seems unusually large",
                f"Received value: {initial_balance}. Please verify this is correct.",
            )

        # Create configuration object for validation
        config = Configuration(
            rate_per_item=float(rate),
            initial_balance=float(initial_balance),
            created_at=datetime.now(),
        )

        # Save to database with enhanced error handling
        try:
            self.db_manager.save_configuration(
                config.rate_per_item, config.initial_balance
            )
        except ValueError as e:
            raise ValidationError(f"Invalid configuration data: {e}")
        except Exception as e:
            raise DatabaseError(
                f"Failed to save account configuration: {e}",
                "Please check database permissions and disk space",
            )

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
        # Validate input with enhanced error messages
        if not isinstance(items, int):
            raise ValidationError(
                "Number of items must be an integer",
                f"Received type: {type(items).__name__}",
            )

        if items < 0:
            raise ValidationError(
                "Number of items cannot be negative", f"Received value: {items}"
            )

        # Check for extremely large item counts
        if items > 10000:
            raise ValidationError(
                "Number of items seems unusually large",
                f"Received value: {items}. Please verify this is correct.",
            )

        # Get configuration with enhanced error handling
        try:
            config_data = self.db_manager.get_configuration()
        except Exception as e:
            raise DatabaseError(
                f"Failed to retrieve configuration: {e}",
                "Please check database connectivity",
            )

        if not config_data:
            raise ConfigurationError(
                "No configuration found. Please run 'saldo setup' first.",
                "Use 'saldo setup --help' for more information",
            )

        rate = config_data["rate_per_item"]

        # Validate rate from database
        if rate <= 0:
            raise ConfigurationError(
                "Invalid rate in configuration",
                f"Rate: {rate}. Please run setup again.",
            )

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
        # Validate inputs with enhanced error messages
        if not isinstance(items, int):
            raise ValidationError(
                "Number of items must be an integer",
                f"Received type: {type(items).__name__}",
            )

        if items < 0:
            raise ValidationError(
                "Number of items cannot be negative", f"Received value: {items}"
            )

        # Check for extremely large item counts
        if items > 10000:
            raise ValidationError(
                "Number of items seems unusually large",
                f"Received value: {items}. Please verify this is correct.",
            )

        if not isinstance(payment, (int, float)):
            raise ValidationError(
                "Payment amount must be a number",
                f"Received type: {type(payment).__name__}",
            )

        # Check for extremely large payment amounts
        if abs(payment) > 1000000:
            raise ValidationError(
                "Payment amount seems unusually large",
                f"Received value: {payment}. Please verify this is correct.",
            )

        # Get current configuration and balance with enhanced error handling
        try:
            config_data = self._get_configuration()
            current_balance = self.get_current_balance()
        except ConfigurationError:
            raise  # Re-raise configuration errors as-is
        except Exception as e:
            raise DatabaseError(
                f"Failed to retrieve account data: {e}",
                "Please check database connectivity",
            )

        # Calculate cost and new balance
        cost = self.calculate_cost(items)
        new_balance = current_balance + cost - payment

        # Validate the resulting balance isn't unreasonably large
        if abs(new_balance) > 1000000:
            raise ValidationError(
                "Resulting balance would be unusually large",
                f"New balance would be: {new_balance}. Please verify transaction amounts.",
            )

        # Create transaction record
        transaction_data = {
            "items": items,
            "cost": cost,
            "payment": float(payment),
            "balance_after": new_balance,
            "created_at": datetime.now(),
        }

        # Save transaction to database with enhanced error handling
        try:
            transaction_id = self.db_manager.save_transaction(transaction_data)
            transaction_data["id"] = transaction_id
        except ValueError as e:
            raise ValidationError(f"Invalid transaction data: {e}")
        except Exception as e:
            raise DatabaseError(
                f"Failed to save transaction: {e}",
                "Please check database permissions and disk space",
            )

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
            raise DatabaseError(
                f"Failed to retrieve configuration: {e}",
                "Please check database connectivity",
            )

        if not config_data:
            raise ConfigurationError(
                "No configuration found. Please run 'saldo setup' first.",
                "Use 'saldo setup --help' for more information",
            )

        # Validate configuration data integrity
        required_fields = ["rate_per_item", "initial_balance"]
        for field in required_fields:
            if field not in config_data:
                raise ConfigurationError(
                    f"Configuration is missing required field: {field}",
                    "Please run setup again to fix the configuration",
                )

        # Validate configuration values
        if config_data["rate_per_item"] <= 0:
            raise ConfigurationError(
                "Invalid rate in configuration",
                f"Rate: {config_data['rate_per_item']}. Please run setup again.",
            )

        return config_data

    def update_rate(self, new_rate: float) -> Dict[str, Any]:
        """
        Update the rate per item in configuration.

        Args:
            new_rate: New rate per clothing item (must be positive)

        Returns:
            Dictionary with update details including old and new rates

        Raises:
            ValidationError: If new rate is invalid
            ConfigurationError: If no configuration exists
            DatabaseError: If database operation fails
        """
        # Validate new rate with enhanced error messages
        if not isinstance(new_rate, (int, float)):
            raise ValidationError(
                "Rate must be a number", f"Received type: {type(new_rate).__name__}"
            )

        if new_rate <= 0:
            raise ValidationError(
                "Rate per item must be positive", f"Received value: {new_rate}"
            )

        # Check for extremely large values that might cause issues
        if new_rate > 1000:
            raise ValidationError(
                "Rate per item seems unusually high",
                f"Received value: {new_rate}. Please verify this is correct.",
            )

        # Get current configuration to compare rates
        try:
            current_config = self._get_configuration()
        except ConfigurationError:
            raise  # Re-raise configuration errors as-is
        except Exception as e:
            raise DatabaseError(
                f"Failed to retrieve current configuration: {e}",
                "Please check database connectivity",
            )

        old_rate = current_config["rate_per_item"]

        # Update rate in database
        try:
            self.db_manager.update_configuration_rate(float(new_rate))
        except ValueError as e:
            raise ValidationError(f"Invalid rate value: {e}")
        except Exception as e:
            raise DatabaseError(
                f"Failed to update configuration rate: {e}",
                "Please check database permissions and connectivity",
            )

        return {
            "old_rate": old_rate,
            "new_rate": float(new_rate),
            "updated_at": datetime.now(),
        }

    def get_configuration_display(self) -> Dict[str, Any]:
        """
        Get configuration data formatted for display.

        Returns:
            Dictionary with formatted configuration data for user display

        Raises:
            ConfigurationError: If no configuration exists
            DatabaseError: If database operation fails
        """
        try:
            config_data = self._get_configuration()
        except ConfigurationError:
            raise  # Re-raise configuration errors as-is
        except Exception as e:
            raise DatabaseError(
                f"Failed to retrieve configuration: {e}",
                "Please check database connectivity",
            )

        # Format the configuration data for display
        return {
            "rate_per_item": config_data["rate_per_item"],
            "initial_balance": config_data["initial_balance"],
            "created_at": config_data["created_at"],
            "formatted_rate": f"₹{config_data['rate_per_item']:.2f}",
            "formatted_initial_balance": f"₹{config_data['initial_balance']:.2f}",
        }
