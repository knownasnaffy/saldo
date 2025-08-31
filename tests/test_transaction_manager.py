"""Unit tests for TransactionManager business logic."""

import pytest
import tempfile
import os
from datetime import datetime

from saldo.transaction_manager import TransactionManager
from saldo.database import DatabaseManager
from saldo.exceptions import ValidationError, ConfigurationError, DatabaseError


class TestTransactionManager:
    """Test cases for TransactionManager class."""

    def setup_method(self):
        """Set up test environment with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.transaction_manager = TransactionManager(self.db_manager)

    def teardown_method(self):
        """Clean up test environment."""
        self.db_manager.close()
        os.unlink(self.temp_db.name)

    def test_setup_account_valid_inputs(self):
        """Test setup_account with valid rate and initial balance."""
        rate = 2.50
        initial_balance = 10.0

        # Should not raise any exceptions
        self.transaction_manager.setup_account(rate, initial_balance)

        # Verify configuration was saved
        config = self.db_manager.get_configuration()
        assert config is not None
        assert config["rate_per_item"] == rate
        assert config["initial_balance"] == initial_balance

    def test_setup_account_zero_initial_balance(self):
        """Test setup_account with zero initial balance."""
        rate = 1.75
        initial_balance = 0.0

        self.transaction_manager.setup_account(rate, initial_balance)

        config = self.db_manager.get_configuration()
        assert config["rate_per_item"] == rate
        assert config["initial_balance"] == initial_balance

    def test_setup_account_negative_initial_balance(self):
        """Test setup_account with negative initial balance (credit)."""
        rate = 3.00
        initial_balance = -15.50

        self.transaction_manager.setup_account(rate, initial_balance)

        config = self.db_manager.get_configuration()
        assert config["rate_per_item"] == rate
        assert config["initial_balance"] == initial_balance

    def test_setup_account_invalid_rate_zero(self):
        """Test setup_account with zero rate (should fail)."""
        with pytest.raises(ValidationError, match="Rate per item must be positive"):
            self.transaction_manager.setup_account(0.0, 10.0)

    def test_setup_account_invalid_rate_negative(self):
        """Test setup_account with negative rate (should fail)."""
        with pytest.raises(ValidationError, match="Rate per item must be positive"):
            self.transaction_manager.setup_account(-2.50, 10.0)

    def test_setup_account_invalid_rate_type(self):
        """Test setup_account with non-numeric rate (should fail)."""
        with pytest.raises(ValidationError, match="Rate must be a number"):
            self.transaction_manager.setup_account("invalid", 10.0)

    def test_setup_account_invalid_balance_type(self):
        """Test setup_account with non-numeric initial balance (should fail)."""
        with pytest.raises(ValidationError, match="Initial balance must be a number"):
            self.transaction_manager.setup_account(2.50, "invalid")

    def test_setup_account_integer_inputs(self):
        """Test setup_account with integer inputs (should work)."""
        rate = 3  # integer
        initial_balance = -5  # integer

        self.transaction_manager.setup_account(rate, initial_balance)

        config = self.db_manager.get_configuration()
        assert config["rate_per_item"] == float(rate)
        assert config["initial_balance"] == float(initial_balance)

    def test_calculate_cost_valid_items(self):
        """Test calculate_cost with valid number of items."""
        # Set up configuration first
        rate = 2.50
        self.transaction_manager.setup_account(rate, 0.0)

        # Test various item counts
        assert self.transaction_manager.calculate_cost(0) == 0.0
        assert self.transaction_manager.calculate_cost(1) == 2.50
        assert self.transaction_manager.calculate_cost(5) == 12.50
        assert self.transaction_manager.calculate_cost(10) == 25.0

    def test_calculate_cost_different_rates(self):
        """Test calculate_cost with different rates."""
        # Test with rate 1.75
        self.transaction_manager.setup_account(1.75, 0.0)
        assert self.transaction_manager.calculate_cost(4) == 7.0

        # Update configuration with new rate
        self.transaction_manager.setup_account(3.25, 0.0)
        assert self.transaction_manager.calculate_cost(3) == 9.75

    def test_calculate_cost_no_configuration(self):
        """Test calculate_cost when no configuration exists."""
        # Don't set up configuration
        with pytest.raises(ConfigurationError, match="No configuration found"):
            self.transaction_manager.calculate_cost(5)

    def test_calculate_cost_invalid_items_negative(self):
        """Test calculate_cost with negative items (should fail)."""
        self.transaction_manager.setup_account(2.50, 0.0)

        with pytest.raises(ValidationError, match="Number of items cannot be negative"):
            self.transaction_manager.calculate_cost(-1)

    def test_calculate_cost_invalid_items_type(self):
        """Test calculate_cost with non-integer items (should fail)."""
        self.transaction_manager.setup_account(2.50, 0.0)

        with pytest.raises(ValidationError, match="Number of items must be an integer"):
            self.transaction_manager.calculate_cost(2.5)

        with pytest.raises(ValidationError, match="Number of items must be an integer"):
            self.transaction_manager.calculate_cost("5")

    def test_get_configuration_exists(self):
        """Test _get_configuration when configuration exists."""
        rate = 2.75
        initial_balance = 20.0
        self.transaction_manager.setup_account(rate, initial_balance)

        config = self.transaction_manager._get_configuration()
        assert config["rate_per_item"] == rate
        assert config["initial_balance"] == initial_balance
        assert "created_at" in config

    def test_get_configuration_not_exists(self):
        """Test _get_configuration when no configuration exists."""
        with pytest.raises(ConfigurationError, match="No configuration found"):
            self.transaction_manager._get_configuration()

    def test_add_transaction_valid_inputs(self):
        """Test add_transaction with valid inputs."""
        # Setup account
        rate = 2.50
        initial_balance = 10.0
        self.transaction_manager.setup_account(rate, initial_balance)

        # Add transaction
        items = 3
        payment = 5.0
        expected_cost = 7.50  # 3 * 2.50
        expected_balance = 12.50  # 10.0 + 7.50 - 5.0

        result = self.transaction_manager.add_transaction(items, payment)

        assert result["items"] == items
        assert result["cost"] == expected_cost
        assert result["payment"] == payment
        assert result["balance_after"] == expected_balance
        assert "id" in result
        assert "created_at" in result

    def test_add_transaction_zero_items(self):
        """Test add_transaction with zero items."""
        self.transaction_manager.setup_account(2.50, 5.0)

        result = self.transaction_manager.add_transaction(0, 3.0)

        assert result["items"] == 0
        assert result["cost"] == 0.0
        assert result["payment"] == 3.0
        assert result["balance_after"] == 2.0  # 5.0 + 0.0 - 3.0

    def test_add_transaction_zero_payment(self):
        """Test add_transaction with zero payment."""
        self.transaction_manager.setup_account(3.0, 0.0)

        result = self.transaction_manager.add_transaction(2, 0.0)

        assert result["items"] == 2
        assert result["cost"] == 6.0
        assert result["payment"] == 0.0
        assert result["balance_after"] == 6.0  # 0.0 + 6.0 - 0.0

    def test_add_transaction_overpayment(self):
        """Test add_transaction with payment exceeding cost."""
        self.transaction_manager.setup_account(2.0, 5.0)

        result = self.transaction_manager.add_transaction(2, 10.0)

        assert result["items"] == 2
        assert result["cost"] == 4.0
        assert result["payment"] == 10.0
        assert result["balance_after"] == -1.0  # 5.0 + 4.0 - 10.0 (credit)

    def test_add_transaction_negative_payment(self):
        """Test add_transaction with negative payment (refund scenario)."""
        self.transaction_manager.setup_account(1.5, 0.0)

        result = self.transaction_manager.add_transaction(1, -2.0)

        assert result["items"] == 1
        assert result["cost"] == 1.5
        assert result["payment"] == -2.0
        assert result["balance_after"] == 3.5  # 0.0 + 1.5 - (-2.0)

    def test_add_transaction_multiple_transactions(self):
        """Test multiple transactions updating balance correctly."""
        self.transaction_manager.setup_account(2.0, 0.0)

        # First transaction
        result1 = self.transaction_manager.add_transaction(2, 3.0)
        assert result1["balance_after"] == 1.0  # 0.0 + 4.0 - 3.0

        # Second transaction
        result2 = self.transaction_manager.add_transaction(1, 0.5)
        assert result2["balance_after"] == 2.5  # 1.0 + 2.0 - 0.5

        # Third transaction
        result3 = self.transaction_manager.add_transaction(0, 2.5)
        assert result3["balance_after"] == 0.0  # 2.5 + 0.0 - 2.5

    def test_add_transaction_invalid_items_negative(self):
        """Test add_transaction with negative items."""
        self.transaction_manager.setup_account(2.0, 0.0)

        with pytest.raises(ValidationError, match="Number of items cannot be negative"):
            self.transaction_manager.add_transaction(-1, 5.0)

    def test_add_transaction_invalid_items_type(self):
        """Test add_transaction with non-integer items."""
        self.transaction_manager.setup_account(2.0, 0.0)

        with pytest.raises(ValidationError, match="Number of items must be an integer"):
            self.transaction_manager.add_transaction(2.5, 5.0)

        with pytest.raises(ValidationError, match="Number of items must be an integer"):
            self.transaction_manager.add_transaction("3", 5.0)

    def test_add_transaction_invalid_payment_type(self):
        """Test add_transaction with non-numeric payment."""
        self.transaction_manager.setup_account(2.0, 0.0)

        with pytest.raises(ValidationError, match="Payment amount must be a number"):
            self.transaction_manager.add_transaction(2, "invalid")

    def test_add_transaction_no_configuration(self):
        """Test add_transaction when no configuration exists."""
        with pytest.raises(ConfigurationError, match="No configuration found"):
            self.transaction_manager.add_transaction(2, 5.0)

    def test_get_current_balance_initial_balance(self):
        """Test get_current_balance with only initial balance."""
        initial_balance = 15.0
        self.transaction_manager.setup_account(2.0, initial_balance)

        balance = self.transaction_manager.get_current_balance()
        assert balance == initial_balance

    def test_get_current_balance_with_transactions(self):
        """Test get_current_balance after transactions."""
        self.transaction_manager.setup_account(2.5, 10.0)

        # Add first transaction
        self.transaction_manager.add_transaction(2, 3.0)
        balance1 = self.transaction_manager.get_current_balance()
        assert balance1 == 12.0  # 10.0 + 5.0 - 3.0

        # Add second transaction
        self.transaction_manager.add_transaction(1, 5.0)
        balance2 = self.transaction_manager.get_current_balance()
        assert balance2 == 9.5  # 12.0 + 2.5 - 5.0

    def test_get_current_balance_negative_balance(self):
        """Test get_current_balance with negative (credit) balance."""
        self.transaction_manager.setup_account(2.0, -5.0)

        balance = self.transaction_manager.get_current_balance()
        assert balance == -5.0

        # Add transaction that increases credit
        self.transaction_manager.add_transaction(1, 5.0)
        balance = self.transaction_manager.get_current_balance()
        assert balance == -8.0  # -5.0 + 2.0 - 5.0

    def test_get_current_balance_no_configuration(self):
        """Test get_current_balance when no configuration exists."""
        with pytest.raises(ConfigurationError, match="No configuration found"):
            self.transaction_manager.get_current_balance()

    def test_update_rate_valid(self):
        """Test update_rate with valid new rate."""
        # Setup initial configuration
        initial_rate = 2.50
        initial_balance = 10.0
        self.transaction_manager.setup_account(initial_rate, initial_balance)

        # Update rate
        new_rate = 3.75
        result = self.transaction_manager.update_rate(new_rate)

        # Verify result
        assert result["old_rate"] == initial_rate
        assert result["new_rate"] == new_rate
        assert "updated_at" in result

        # Verify rate was actually updated in database
        config = self.db_manager.get_configuration()
        assert config["rate_per_item"] == new_rate
        assert config["initial_balance"] == initial_balance  # Should be preserved

    def test_update_rate_integer_input(self):
        """Test update_rate with integer input."""
        self.transaction_manager.setup_account(2.0, 5.0)

        new_rate = 4  # integer
        result = self.transaction_manager.update_rate(new_rate)

        assert result["old_rate"] == 2.0
        assert result["new_rate"] == 4.0

        # Verify in database
        config = self.db_manager.get_configuration()
        assert config["rate_per_item"] == 4.0

    def test_update_rate_same_rate(self):
        """Test update_rate with same rate as current."""
        rate = 2.25
        self.transaction_manager.setup_account(rate, 0.0)

        result = self.transaction_manager.update_rate(rate)

        assert result["old_rate"] == rate
        assert result["new_rate"] == rate

    def test_update_rate_invalid_negative(self):
        """Test update_rate with negative rate."""
        self.transaction_manager.setup_account(2.0, 0.0)

        with pytest.raises(ValidationError, match="Rate per item must be positive"):
            self.transaction_manager.update_rate(-1.5)

    def test_update_rate_invalid_zero(self):
        """Test update_rate with zero rate."""
        self.transaction_manager.setup_account(2.0, 0.0)

        with pytest.raises(ValidationError, match="Rate per item must be positive"):
            self.transaction_manager.update_rate(0.0)

    def test_update_rate_invalid_type(self):
        """Test update_rate with non-numeric rate."""
        self.transaction_manager.setup_account(2.0, 0.0)

        with pytest.raises(ValidationError, match="Rate must be a number"):
            self.transaction_manager.update_rate("invalid")

        with pytest.raises(ValidationError, match="Rate must be a number"):
            self.transaction_manager.update_rate(None)

    def test_update_rate_extremely_high(self):
        """Test update_rate with extremely high rate."""
        self.transaction_manager.setup_account(2.0, 0.0)

        with pytest.raises(ValidationError, match="Rate per item seems unusually high"):
            self.transaction_manager.update_rate(1500.0)

    def test_update_rate_no_configuration(self):
        """Test update_rate when no configuration exists."""
        with pytest.raises(ConfigurationError, match="No configuration found"):
            self.transaction_manager.update_rate(3.0)

    def test_get_configuration_display_valid(self):
        """Test get_configuration_display with valid configuration."""
        rate = 2.75
        initial_balance = 15.50
        self.transaction_manager.setup_account(rate, initial_balance)

        result = self.transaction_manager.get_configuration_display()

        # Check raw values
        assert result["rate_per_item"] == rate
        assert result["initial_balance"] == initial_balance
        assert "created_at" in result

        # Check formatted values
        assert result["formatted_rate"] == "₹2.75"
        assert result["formatted_initial_balance"] == "₹15.50"

    def test_get_configuration_display_negative_balance(self):
        """Test get_configuration_display with negative initial balance."""
        rate = 3.00
        initial_balance = -25.75
        self.transaction_manager.setup_account(rate, initial_balance)

        result = self.transaction_manager.get_configuration_display()

        assert result["rate_per_item"] == rate
        assert result["initial_balance"] == initial_balance
        assert result["formatted_rate"] == "₹3.00"
        assert result["formatted_initial_balance"] == "₹-25.75"

    def test_get_configuration_display_zero_balance(self):
        """Test get_configuration_display with zero initial balance."""
        rate = 1.25
        initial_balance = 0.0
        self.transaction_manager.setup_account(rate, initial_balance)

        result = self.transaction_manager.get_configuration_display()

        assert result["rate_per_item"] == rate
        assert result["initial_balance"] == initial_balance
        assert result["formatted_rate"] == "₹1.25"
        assert result["formatted_initial_balance"] == "₹0.00"

    def test_get_configuration_display_formatting_precision(self):
        """Test get_configuration_display formatting with various decimal places."""
        rate = 2.123456  # Many decimal places
        initial_balance = 10.1  # One decimal place
        self.transaction_manager.setup_account(rate, initial_balance)

        result = self.transaction_manager.get_configuration_display()

        # Raw values should preserve precision
        assert result["rate_per_item"] == rate
        assert result["initial_balance"] == initial_balance

        # Formatted values should have 2 decimal places
        assert result["formatted_rate"] == "₹2.12"  # Rounded to 2 decimals
        assert result["formatted_initial_balance"] == "₹10.10"

    def test_get_configuration_display_no_configuration(self):
        """Test get_configuration_display when no configuration exists."""
        with pytest.raises(ConfigurationError, match="No configuration found"):
            self.transaction_manager.get_configuration_display()


class TestTransactionManagerIntegration:
    """Integration tests for TransactionManager with real database operations."""

    def setup_method(self):
        """Set up test environment with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.transaction_manager = TransactionManager(
            DatabaseManager(self.temp_db.name)
        )

    def teardown_method(self):
        """Clean up test environment."""
        self.transaction_manager.db_manager.close()
        os.unlink(self.temp_db.name)

    def test_setup_and_calculate_workflow(self):
        """Test complete workflow of setup followed by cost calculations."""
        # Setup account
        rate = 2.25
        initial_balance = 15.0
        self.transaction_manager.setup_account(rate, initial_balance)

        # Calculate costs for different item counts
        assert self.transaction_manager.calculate_cost(0) == 0.0
        assert self.transaction_manager.calculate_cost(2) == 4.50
        assert self.transaction_manager.calculate_cost(7) == 15.75

    def test_reconfigure_account(self):
        """Test updating account configuration."""
        # Initial setup
        self.transaction_manager.setup_account(2.00, 10.0)
        assert self.transaction_manager.calculate_cost(3) == 6.0

        # Update configuration
        self.transaction_manager.setup_account(3.50, -5.0)
        assert self.transaction_manager.calculate_cost(3) == 10.50

        # Verify new configuration is used
        config = self.transaction_manager._get_configuration()
        assert config["rate_per_item"] == 3.50
        assert config["initial_balance"] == -5.0

    def test_complete_transaction_workflow(self):
        """Test complete workflow with setup, transactions, and balance checks."""
        # Setup account
        self.transaction_manager.setup_account(2.0, 5.0)

        # Initial balance should be 5.0
        assert self.transaction_manager.get_current_balance() == 5.0

        # Add first transaction: 3 items, pay 4.0
        # Cost: 3 * 2.0 = 6.0, Balance: 5.0 + 6.0 - 4.0 = 7.0
        result1 = self.transaction_manager.add_transaction(3, 4.0)
        assert result1["balance_after"] == 7.0
        assert self.transaction_manager.get_current_balance() == 7.0

        # Add second transaction: 1 item, pay 10.0 (overpayment)
        # Cost: 1 * 2.0 = 2.0, Balance: 7.0 + 2.0 - 10.0 = -1.0 (credit)
        result2 = self.transaction_manager.add_transaction(1, 10.0)
        assert result2["balance_after"] == -1.0
        assert self.transaction_manager.get_current_balance() == -1.0

        # Add third transaction: 2 items, pay 0.0
        # Cost: 2 * 2.0 = 4.0, Balance: -1.0 + 4.0 - 0.0 = 3.0
        result3 = self.transaction_manager.add_transaction(2, 0.0)
        assert result3["balance_after"] == 3.0
        assert self.transaction_manager.get_current_balance() == 3.0
