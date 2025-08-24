"""
Tests for the CLI interface of the Saldo application.

Tests Click commands, user interaction, input validation, and error handling.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from saldo.cli import cli, setup
from saldo.database import DatabaseManager
from saldo.exceptions import ValidationError, ConfigurationError, DatabaseError


class TestSetupCommand:
    """Test cases for the setup command."""
    
    def setup_method(self):
        """Set up test environment with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Clean up temporary database file."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_with_options_success(self, mock_tm_class):
        """Test setup command with rate and balance options."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Run setup command with options
        result = self.runner.invoke(setup, ['--rate', '2.50', '--balance', '10.00'])
        
        # Verify success
        assert result.exit_code == 0
        assert "Account setup completed successfully!" in result.output
        assert "Rate per item: $2.50" in result.output
        assert "$10.00 (you owe)" in result.output
        
        # Verify TransactionManager was called correctly
        mock_tm.setup_account.assert_called_once_with(2.50, 10.00)
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_interactive_prompts(self, mock_tm_class):
        """Test setup command with interactive prompts."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Run setup command with interactive input
        result = self.runner.invoke(setup, input='2.50\n-5.00\n')
        
        # Verify success
        assert result.exit_code == 0
        assert "Account setup completed successfully!" in result.output
        assert "Rate per item: $2.50" in result.output
        assert "$5.00 (you have credit)" in result.output
        
        # Verify TransactionManager was called correctly
        mock_tm.setup_account.assert_called_once_with(2.50, -5.00)
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_zero_balance(self, mock_tm_class):
        """Test setup command with zero balance."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Run setup command with zero balance
        result = self.runner.invoke(setup, ['--rate', '3.00', '--balance', '0'])
        
        # Verify success
        assert result.exit_code == 0
        assert "Rate per item: $3.00" in result.output
        assert "$0.00 (starting fresh)" in result.output
        
        mock_tm.setup_account.assert_called_once_with(3.00, 0.0)
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_default_balance_prompt(self, mock_tm_class):
        """Test setup command with default balance from prompt."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Run setup command with default balance (just press enter)
        result = self.runner.invoke(setup, input='2.00\n\n')
        
        # Verify success
        assert result.exit_code == 0
        assert "Rate per item: $2.00" in result.output
        assert "$0.00 (starting fresh)" in result.output
        
        mock_tm.setup_account.assert_called_once_with(2.00, 0.0)
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_negative_rate_option(self, mock_tm_class):
        """Test setup command with negative rate option."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        result = self.runner.invoke(setup, ['--rate', '-1.00', '--balance', '0'])
        
        # Verify error
        assert result.exit_code != 0
        assert "Validation Error" in result.output
        assert "Rate must be a positive number" in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_zero_rate_option(self, mock_tm_class):
        """Test setup command with zero rate option."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        result = self.runner.invoke(setup, ['--rate', '0', '--balance', '0'])
        
        # Verify error
        assert result.exit_code != 0
        assert "Validation Error" in result.output
        assert "Rate must be a positive number" in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_invalid_rate_input(self, mock_tm_class):
        """Test setup command with invalid rate input."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Run setup command with invalid then valid rate input
        result = self.runner.invoke(setup, input='abc\n-2.0\n0\n2.50\n0\n')
        
        # Verify success after retries
        assert result.exit_code == 0
        assert "Please enter a valid number" in result.output
        assert "Rate must be a positive number" in result.output
        assert "Account setup completed successfully!" in result.output
        
        mock_tm.setup_account.assert_called_once_with(2.50, 0.0)
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_invalid_balance_input(self, mock_tm_class):
        """Test setup command with invalid balance input."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Run setup command with invalid then valid balance input
        result = self.runner.invoke(setup, input='2.50\nxyz\n10.00\n')
        
        # Verify success after retry
        assert result.exit_code == 0
        assert "Please enter a valid number" in result.output
        assert "Account setup completed successfully!" in result.output
        
        mock_tm.setup_account.assert_called_once_with(2.50, 10.00)
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_existing_configuration_confirm_overwrite(self, mock_tm_class):
        """Test setup command with existing configuration and confirm overwrite."""
        # Mock TransactionManager with existing configuration
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 5.00
        }
        
        # Run setup command and confirm overwrite
        result = self.runner.invoke(setup, input='y\n3.00\n0\n')
        
        # Verify success
        assert result.exit_code == 0
        assert "Configuration already exists!" in result.output
        assert "Current rate: $2.00 per item" in result.output
        assert "Initial balance: $5.00" in result.output
        assert "Account setup completed successfully!" in result.output
        
        mock_tm.setup_account.assert_called_once_with(3.00, 0.0)
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_existing_configuration_cancel(self, mock_tm_class):
        """Test setup command with existing configuration and cancel."""
        # Mock TransactionManager with existing configuration
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 5.00
        }
        
        # Run setup command and cancel
        result = self.runner.invoke(setup, input='n\n')
        
        # Verify cancellation
        assert result.exit_code == 0
        assert "Configuration already exists!" in result.output
        assert "Setup cancelled." in result.output
        
        # Verify setup_account was not called
        mock_tm.setup_account.assert_not_called()
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_validation_error(self, mock_tm_class):
        """Test setup command with validation error from TransactionManager."""
        # Mock TransactionManager to raise ValidationError
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        mock_tm.setup_account.side_effect = ValidationError("Invalid rate value")
        
        # Run setup command
        result = self.runner.invoke(setup, ['--rate', '2.50', '--balance', '0'])
        
        # Verify error handling
        assert result.exit_code != 0
        assert "Validation Error: Invalid rate value" in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_database_error(self, mock_tm_class):
        """Test setup command with database error from TransactionManager."""
        # Mock TransactionManager to raise DatabaseError
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        mock_tm.setup_account.side_effect = DatabaseError("Database connection failed")
        
        # Run setup command
        result = self.runner.invoke(setup, ['--rate', '2.50', '--balance', '0'])
        
        # Verify error handling
        assert result.exit_code != 0
        assert "Database Error: Database connection failed" in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_configuration_error(self, mock_tm_class):
        """Test setup command with configuration error from TransactionManager."""
        # Mock TransactionManager to raise ConfigurationError
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        mock_tm.setup_account.side_effect = ConfigurationError("Configuration invalid")
        
        # Run setup command
        result = self.runner.invoke(setup, ['--rate', '2.50', '--balance', '0'])
        
        # Verify error handling
        assert result.exit_code != 0
        assert "Configuration Error: Configuration invalid" in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_unexpected_error(self, mock_tm_class):
        """Test setup command with unexpected error."""
        # Mock TransactionManager to raise unexpected error
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        mock_tm.setup_account.side_effect = RuntimeError("Unexpected error")
        
        # Run setup command
        result = self.runner.invoke(setup, ['--rate', '2.50', '--balance', '0'])
        
        # Verify error handling
        assert result.exit_code != 0
        assert "Unexpected error: Unexpected error" in result.output


class TestCLIGroup:
    """Test cases for the main CLI group."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test CLI help message."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Saldo - A command-line balance tracking application" in result.output
        assert "setup" in result.output
    
    def test_cli_version(self):
        """Test CLI version option."""
        result = self.runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "saldo, version 0.1.0" in result.output
    
    def test_setup_help(self):
        """Test setup command help."""
        result = self.runner.invoke(cli, ['setup', '--help'])
        
        assert result.exit_code == 0
        assert "Initialize the application" in result.output
        assert "--rate" in result.output
        assert "--balance" in result.output


class TestAddTransactionCommand:
    """Test cases for the add-transaction command."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_with_options_success(self, mock_tm_class):
        """Test add-transaction command with items and payment options."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 5.00
        mock_tm.calculate_cost.return_value = 12.50
        mock_tm.add_transaction.return_value = {
            'id': 1,
            'items': 5,
            'cost': 12.50,
            'payment': 15.00,
            'balance_after': 2.50
        }
        
        # Run add-transaction command with options
        result = self.runner.invoke(cli, ['add-transaction', '--items', '5', '--payment', '15.00'])
        
        # Verify success
        assert result.exit_code == 0
        assert "Transaction recorded successfully!" in result.output
        assert "Items processed: 5" in result.output
        assert "Total cost: $12.50" in result.output
        assert "Payment received: $15.00" in result.output
        assert "New balance: $2.50 (you owe)" in result.output
        assert "Overpayment: $2.50 (applied as credit)" in result.output
        
        # Verify TransactionManager was called correctly
        mock_tm.add_transaction.assert_called_once_with(5, 15.00)
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_interactive_prompts(self, mock_tm_class):
        """Test add-transaction command with interactive prompts."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 3.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 0.0
        mock_tm.calculate_cost.return_value = 9.00
        mock_tm.add_transaction.return_value = {
            'id': 1,
            'items': 3,
            'cost': 9.00,
            'payment': 10.00,
            'balance_after': -1.00
        }
        
        # Run add-transaction command with interactive input
        result = self.runner.invoke(cli, ['add-transaction'], input='3\n10.00\n')
        
        # Verify success
        assert result.exit_code == 0
        assert "Transaction recorded successfully!" in result.output
        assert "Items processed: 3" in result.output
        assert "Total cost: $9.00" in result.output
        assert "New balance: $1.00 (you have credit)" in result.output
        
        mock_tm.add_transaction.assert_called_once_with(3, 10.00)
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_zero_balance_result(self, mock_tm_class):
        """Test add-transaction command resulting in zero balance."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 0.0
        mock_tm.calculate_cost.return_value = 10.00
        mock_tm.add_transaction.return_value = {
            'id': 1,
            'items': 5,
            'cost': 10.00,
            'payment': 10.00,
            'balance_after': 0.0
        }
        
        # Run add-transaction command
        result = self.runner.invoke(cli, ['add-transaction', '--items', '5', '--payment', '10.00'])
        
        # Verify success
        assert result.exit_code == 0
        assert "New balance: $0.00 (all settled)" in result.output
        
        mock_tm.add_transaction.assert_called_once_with(5, 10.00)
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_underpayment(self, mock_tm_class):
        """Test add-transaction command with underpayment."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 5.00
        mock_tm.calculate_cost.return_value = 10.00
        mock_tm.add_transaction.return_value = {
            'id': 1,
            'items': 5,
            'cost': 10.00,
            'payment': 8.00,
            'balance_after': 7.00
        }
        
        # Run add-transaction command
        result = self.runner.invoke(cli, ['add-transaction', '--items', '5', '--payment', '8.00'])
        
        # Verify success
        assert result.exit_code == 0
        assert "New balance: $7.00 (you owe)" in result.output
        assert "Underpayment: $2.00 (added to balance)" in result.output
        
        mock_tm.add_transaction.assert_called_once_with(5, 8.00)
    
    def test_add_transaction_negative_items_option(self):
        """Test add-transaction command with negative items option."""
        result = self.runner.invoke(cli, ['add-transaction', '--items', '-1', '--payment', '10.00'])
        
        # Verify error
        assert result.exit_code != 0
        assert "Validation Error" in result.output
        assert "Number of items cannot be negative" in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_invalid_items_input(self, mock_tm_class):
        """Test add-transaction command with invalid items input."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 0.0
        mock_tm.calculate_cost.return_value = 4.00
        mock_tm.add_transaction.return_value = {
            'id': 1,
            'items': 2,
            'cost': 4.00,
            'payment': 5.00,
            'balance_after': -1.00
        }
        
        # Run add-transaction command with invalid then valid items input
        result = self.runner.invoke(cli, ['add-transaction'], input='abc\n-1\n2\n5.00\n')
        
        # Verify success after retries
        assert result.exit_code == 0
        assert "Please enter a valid whole number" in result.output
        assert "Number of items cannot be negative" in result.output
        assert "Transaction recorded successfully!" in result.output
        
        mock_tm.add_transaction.assert_called_once_with(2, 5.00)
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_invalid_payment_input(self, mock_tm_class):
        """Test add-transaction command with invalid payment input."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 0.0
        mock_tm.calculate_cost.return_value = 4.00
        mock_tm.add_transaction.return_value = {
            'id': 1,
            'items': 2,
            'cost': 4.00,
            'payment': 5.00,
            'balance_after': -1.00
        }
        
        # Run add-transaction command with invalid then valid payment input
        result = self.runner.invoke(cli, ['add-transaction'], input='2\nxyz\n5.00\n')
        
        # Verify success after retry
        assert result.exit_code == 0
        assert "Please enter a valid number" in result.output
        assert "Transaction recorded successfully!" in result.output
        
        mock_tm.add_transaction.assert_called_once_with(2, 5.00)
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_no_configuration(self, mock_tm_class):
        """Test add-transaction command with no configuration."""
        # Mock TransactionManager with no configuration
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Run add-transaction command
        result = self.runner.invoke(cli, ['add-transaction', '--items', '5', '--payment', '10.00'])
        
        # Verify error
        assert result.exit_code != 0
        assert "No configuration found. Please run 'saldo setup' first." in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_validation_error(self, mock_tm_class):
        """Test add-transaction command with validation error from TransactionManager."""
        # Mock TransactionManager to raise ValidationError
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 0.0
        mock_tm.calculate_cost.return_value = 10.00
        mock_tm.add_transaction.side_effect = ValidationError("Invalid transaction data")
        
        # Run add-transaction command
        result = self.runner.invoke(cli, ['add-transaction', '--items', '5', '--payment', '10.00'])
        
        # Verify error handling
        assert result.exit_code != 0
        assert "Validation Error: Invalid transaction data" in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_database_error(self, mock_tm_class):
        """Test add-transaction command with database error from TransactionManager."""
        # Mock TransactionManager to raise DatabaseError
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 0.0
        mock_tm.calculate_cost.return_value = 10.00
        mock_tm.add_transaction.side_effect = DatabaseError("Database connection failed")
        
        # Run add-transaction command
        result = self.runner.invoke(cli, ['add-transaction', '--items', '5', '--payment', '10.00'])
        
        # Verify error handling
        assert result.exit_code != 0
        assert "Database Error: Database connection failed" in result.output
    
    def test_add_transaction_help(self):
        """Test add-transaction command help."""
        result = self.runner.invoke(cli, ['add-transaction', '--help'])
        
        assert result.exit_code == 0
        assert "Add a new ironing transaction" in result.output
        assert "--items" in result.output
        assert "--payment" in result.output


class TestBalanceCommand:
    """Test cases for the balance command."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_positive_balance(self, mock_tm_class):
        """Test balance command with positive balance (owed)."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 15.75
        
        # Run balance command
        result = self.runner.invoke(cli, ['balance'])
        
        # Verify success
        assert result.exit_code == 0
        assert "Saldo Balance Summary" in result.output
        assert "Rate per item: $2.50" in result.output
        assert "Current balance: $15.75 (you owe)" in result.output
        assert "You have an outstanding balance to pay." in result.output
        assert "Use 'saldo balance --detailed' to see transaction history." in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_negative_balance(self, mock_tm_class):
        """Test balance command with negative balance (credit)."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 3.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = -5.50
        
        # Run balance command
        result = self.runner.invoke(cli, ['balance'])
        
        # Verify success
        assert result.exit_code == 0
        assert "Rate per item: $3.00" in result.output
        assert "Current balance: $5.50 (you have credit)" in result.output
        assert "You have credit available for future transactions." in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_zero_balance(self, mock_tm_class):
        """Test balance command with zero balance."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 0.0
        
        # Run balance command
        result = self.runner.invoke(cli, ['balance'])
        
        # Verify success
        assert result.exit_code == 0
        assert "Rate per item: $2.00" in result.output
        assert "Current balance: $0.00 (all settled)" in result.output
        assert "Your account is fully settled." in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_detailed_with_transactions(self, mock_tm_class):
        """Test balance command with detailed flag and transactions."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 7.50
        mock_tm.db_manager.get_transactions.return_value = [
            {
                'id': 2,
                'items': 3,
                'cost': 7.50,
                'payment': 5.00,
                'balance_after': 7.50,
                'created_at': '2024-01-15 10:30:00'
            },
            {
                'id': 1,
                'items': 2,
                'cost': 5.00,
                'payment': 10.00,
                'balance_after': -5.00,
                'created_at': '2024-01-10 14:20:00'
            }
        ]
        
        # Run balance command with detailed flag
        result = self.runner.invoke(cli, ['balance', '--detailed'])
        
        # Verify success
        assert result.exit_code == 0
        assert "Current balance: $7.50 (you owe)" in result.output
        assert "Recent Transactions (last 2):" in result.output
        assert "2024-01-15" in result.output
        assert "2024-01-10" in result.output
        assert "Total items processed: 5" in result.output
        assert "Total cost: $12.50" in result.output
        assert "Total payments: $15.00" in result.output
        
        # Verify get_transactions was called with default limit
        mock_tm.db_manager.get_transactions.assert_called_once_with(limit=10)
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_detailed_with_custom_limit(self, mock_tm_class):
        """Test balance command with detailed flag and custom limit."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 0.0
        mock_tm.db_manager.get_transactions.return_value = []
        
        # Run balance command with detailed flag and custom limit
        result = self.runner.invoke(cli, ['balance', '--detailed', '--limit', '5'])
        
        # Verify success
        assert result.exit_code == 0
        
        # Verify get_transactions was called with custom limit
        mock_tm.db_manager.get_transactions.assert_called_once_with(limit=5)
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_detailed_no_transactions(self, mock_tm_class):
        """Test balance command with detailed flag but no transactions."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 10.0
        }
        mock_tm.get_current_balance.return_value = 10.0
        mock_tm.db_manager.get_transactions.return_value = []
        
        # Run balance command with detailed flag
        result = self.runner.invoke(cli, ['balance', '--detailed'])
        
        # Verify success
        assert result.exit_code == 0
        assert "Current balance: $10.00 (you owe)" in result.output
        assert "No transactions found." in result.output
        assert "Use 'saldo add-transaction' to record your first transaction." in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_no_configuration(self, mock_tm_class):
        """Test balance command with no configuration."""
        # Mock TransactionManager with no configuration
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Run balance command
        result = self.runner.invoke(cli, ['balance'])
        
        # Verify error
        assert result.exit_code != 0
        assert "No configuration found. Please run 'saldo setup' first." in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_database_error_config(self, mock_tm_class):
        """Test balance command with database error getting configuration."""
        # Mock TransactionManager to raise DatabaseError
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.side_effect = DatabaseError("Database connection failed")
        
        # Run balance command
        result = self.runner.invoke(cli, ['balance'])
        
        # Verify error handling
        assert result.exit_code != 0
        assert "Database Error: Database connection failed" in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_database_error_transactions(self, mock_tm_class):
        """Test balance command with database error getting transactions."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 5.0
        mock_tm.db_manager.get_transactions.side_effect = DatabaseError("Transaction query failed")
        
        # Run balance command with detailed flag
        result = self.runner.invoke(cli, ['balance', '--detailed'])
        
        # Verify partial success with error message
        assert result.exit_code == 0
        assert "Current balance: $5.00 (you owe)" in result.output
        assert "Could not retrieve transaction history: Transaction query failed" in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_configuration_error(self, mock_tm_class):
        """Test balance command with configuration error from TransactionManager."""
        # Mock TransactionManager to raise ConfigurationError
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.00,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.side_effect = ConfigurationError("Configuration invalid")
        
        # Run balance command
        result = self.runner.invoke(cli, ['balance'])
        
        # Verify error handling
        assert result.exit_code != 0
        assert "Configuration Error: Configuration invalid" in result.output
    
    def test_balance_help(self):
        """Test balance command help."""
        result = self.runner.invoke(cli, ['balance', '--help'])
        
        assert result.exit_code == 0
        assert "Display current balance and rate information" in result.output
        assert "--detailed" in result.output
        assert "--limit" in result.output