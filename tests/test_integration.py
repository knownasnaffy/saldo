"""
Integration tests for the Saldo application.

Tests complete user workflows, data persistence across application restarts,
and error recovery scenarios.
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

from saldo.cli import cli
from saldo.database import DatabaseManager
from saldo.transaction_manager import TransactionManager


class TestEndToEndWorkflows:
    """Test complete user workflows from setup to balance checking."""

    def setup_method(self):
        """Set up test environment with temporary database directory."""
        # Create temporary directory for database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "saldo.db")
        self.runner = CliRunner()

        # Patch DatabaseManager to use our test database path
        self.db_patcher = patch.object(DatabaseManager, "__init__", self._mock_db_init)
        self.db_patcher.start()

    def _mock_db_init(self, instance, db_path=None):
        """Mock DatabaseManager.__init__ to use test database path."""
        instance.db_path = self.db_path
        instance._connection = None

    def teardown_method(self):
        """Clean up test environment."""
        # Stop the patcher
        self.db_patcher.stop()

        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_complete_workflow_setup_to_balance(self):
        """Test complete workflow: setup → add-transaction → balance."""
        # Step 1: Setup account
        setup_result = self.runner.invoke(
            cli, ["setup", "--rate", "2.50", "--balance", "10.00"]
        )
        assert setup_result.exit_code == 0
        assert "Account setup completed successfully!" in setup_result.output
        assert "Rate per item: ₹2.50" in setup_result.output
        assert "₹10.00 (you owe)" in setup_result.output

        # Step 2: Add first transaction
        transaction1_result = self.runner.invoke(
            cli, ["add-transaction", "--items", "3", "--payment", "5.00"]
        )
        assert transaction1_result.exit_code == 0
        assert "Transaction recorded successfully!" in transaction1_result.output
        assert "Items processed: 3" in transaction1_result.output
        assert "Total cost: ₹7.50" in transaction1_result.output
        assert "Payment received: ₹5.00" in transaction1_result.output
        # Balance: 10.00 + 7.50 - 5.00 = 12.50
        assert "₹12.50 (you owe)" in transaction1_result.output

        # Step 3: Check balance
        balance_result = self.runner.invoke(cli, ["balance"])
        assert balance_result.exit_code == 0
        assert "Current balance: ₹12.50 (you owe)" in balance_result.output
        assert "Rate per item: ₹2.50" in balance_result.output

        # Step 4: Add second transaction with overpayment
        transaction2_result = self.runner.invoke(
            cli, ["add-transaction", "--items", "2", "--payment", "20.00"]
        )
        assert transaction2_result.exit_code == 0
        assert "Items processed: 2" in transaction2_result.output
        assert "Total cost: ₹5.00" in transaction2_result.output
        # Balance: 12.50 + 5.00 - 20.00 = -2.50 (credit)
        assert "₹2.50 (you have credit)" in transaction2_result.output
        assert "Overpayment: ₹15.00 (applied as credit)" in transaction2_result.output

        # Step 5: Check final balance
        final_balance_result = self.runner.invoke(cli, ["balance"])
        assert final_balance_result.exit_code == 0
        assert "₹2.50 (you have credit)" in final_balance_result.output
        assert "You have credit available" in final_balance_result.output

    def test_workflow_with_zero_balance_result(self):
        """Test workflow that results in exactly zero balance."""
        # Setup with initial balance
        self.runner.invoke(cli, ["setup", "--rate", "3.00", "--balance", "5.00"])

        # Add transaction that exactly settles the balance
        # Balance: 5.00 + 6.00 - 11.00 = 0.00
        transaction_result = self.runner.invoke(
            cli, ["add-transaction", "--items", "2", "--payment", "11.00"]
        )
        assert transaction_result.exit_code == 0
        assert "₹0.00 (all settled)" in transaction_result.output

        # Check balance shows settled
        balance_result = self.runner.invoke(cli, ["balance"])
        assert balance_result.exit_code == 0
        assert "₹0.00 (all settled)" in balance_result.output
        assert "Your account is fully settled" in balance_result.output

    def test_workflow_with_detailed_balance_history(self):
        """Test workflow with detailed balance checking."""
        # Setup account
        self.runner.invoke(cli, ["setup", "--rate", "2.00", "--balance", "0.00"])

        # Add multiple transactions
        self.runner.invoke(
            cli, ["add-transaction", "--items", "3", "--payment", "4.00"]
        )
        self.runner.invoke(
            cli, ["add-transaction", "--items", "1", "--payment", "3.00"]
        )
        self.runner.invoke(
            cli, ["add-transaction", "--items", "2", "--payment", "1.00"]
        )

        # Check detailed balance
        detailed_result = self.runner.invoke(cli, ["balance", "--detailed"])
        assert detailed_result.exit_code == 0
        assert "Recent Transactions" in detailed_result.output
        assert "Total items processed: 6" in detailed_result.output
        assert "Total cost: ₹12.00" in detailed_result.output
        assert "Total payments: ₹8.00" in detailed_result.output

        # Check with custom limit
        limited_result = self.runner.invoke(
            cli, ["balance", "--detailed", "--limit", "2"]
        )
        assert limited_result.exit_code == 0
        assert "Recent Transactions (last 2)" in limited_result.output

    def test_interactive_setup_workflow(self):
        """Test interactive setup with prompts."""
        # Test interactive setup
        setup_result = self.runner.invoke(cli, ["setup"], input="2.75\n-5.50\n")
        assert setup_result.exit_code == 0
        assert "Account setup completed successfully!" in setup_result.output
        assert "Rate per item: ₹2.75" in setup_result.output
        assert "₹5.50 (you have credit)" in setup_result.output

        # Test interactive transaction
        transaction_result = self.runner.invoke(
            cli, ["add-transaction"], input="4\n10.00\n"
        )
        assert transaction_result.exit_code == 0
        assert "Items processed: 4" in transaction_result.output
        assert "Total cost: ₹11.00" in transaction_result.output
        # Balance: -5.50 + 11.00 - 10.00 = -4.50 (credit)
        assert "₹4.50 (you have credit)" in transaction_result.output

    def test_workflow_with_zero_items_transaction(self):
        """Test workflow with zero items transaction (payment only)."""
        # Setup account
        self.runner.invoke(cli, ["setup", "--rate", "2.00", "--balance", "10.00"])

        # Add transaction with zero items (payment towards balance)
        transaction_result = self.runner.invoke(
            cli, ["add-transaction", "--items", "0", "--payment", "5.00"]
        )
        assert transaction_result.exit_code == 0
        assert "Items processed: 0" in transaction_result.output
        assert "Total cost: ₹0.00" in transaction_result.output
        # Balance: 10.00 + 0.00 - 5.00 = 5.00
        assert "₹5.00 (you owe)" in transaction_result.output

        # Verify balance
        balance_result = self.runner.invoke(cli, ["balance"])
        assert balance_result.exit_code == 0
        assert "₹5.00 (you owe)" in balance_result.output


class TestDataPersistence:
    """Test data persistence across application restarts."""

    def setup_method(self):
        """Set up test environment with temporary database directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "saldo.db")
        self.runner = CliRunner()

        # Patch DatabaseManager to use our test database path
        self.db_patcher = patch.object(DatabaseManager, "__init__", self._mock_db_init)
        self.db_patcher.start()

    def _mock_db_init(self, instance, db_path=None):
        """Mock DatabaseManager.__init__ to use test database path."""
        instance.db_path = self.db_path
        instance._connection = None

    def teardown_method(self):
        """Clean up test environment."""
        # Stop the patcher
        self.db_patcher.stop()

        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_configuration_persistence(self):
        """Test that configuration persists across application restarts."""
        # First session: Setup account
        setup_result = self.runner.invoke(
            cli, ["setup", "--rate", "3.25", "--balance", "15.75"]
        )
        assert setup_result.exit_code == 0

        # Verify database file was created
        assert os.path.exists(self.db_path)

        # Second session: Check that configuration is remembered
        balance_result = self.runner.invoke(cli, ["balance"])
        assert balance_result.exit_code == 0
        assert "Rate per item: ₹3.25" in balance_result.output
        assert "₹15.75 (you owe)" in balance_result.output

        # Third session: Try to setup again (should warn about existing config)
        setup_again_result = self.runner.invoke(cli, ["setup"], input="n\n")
        assert setup_again_result.exit_code == 0
        assert "Configuration already exists!" in setup_again_result.output
        assert "Current rate: ₹3.25 per item" in setup_again_result.output
        assert "Setup cancelled." in setup_again_result.output

    def test_transaction_history_persistence(self):
        """Test that transaction history persists across application restarts."""
        # First session: Setup and add transactions
        self.runner.invoke(cli, ["setup", "--rate", "2.00", "--balance", "0.00"])
        self.runner.invoke(
            cli, ["add-transaction", "--items", "5", "--payment", "8.00"]
        )
        self.runner.invoke(
            cli, ["add-transaction", "--items", "2", "--payment", "6.00"]
        )

        # Second session: Check balance and history
        balance_result = self.runner.invoke(cli, ["balance"])
        assert balance_result.exit_code == 0
        # Balance: 0 + 10 - 8 + 4 - 6 = 0
        assert "₹0.00 (all settled)" in balance_result.output

        # Check detailed history
        detailed_result = self.runner.invoke(cli, ["balance", "--detailed"])
        assert detailed_result.exit_code == 0
        assert "Total items processed: 7" in detailed_result.output
        assert "Total cost: ₹14.00" in detailed_result.output
        assert "Total payments: ₹14.00" in detailed_result.output

        # Third session: Add another transaction
        self.runner.invoke(
            cli, ["add-transaction", "--items", "3", "--payment", "5.00"]
        )

        # Fourth session: Verify all history is preserved
        final_detailed_result = self.runner.invoke(cli, ["balance", "--detailed"])
        assert final_detailed_result.exit_code == 0
        assert "Total items processed: 10" in final_detailed_result.output
        assert "Total cost: ₹20.00" in final_detailed_result.output
        assert "Total payments: ₹19.00" in final_detailed_result.output

    def test_balance_calculation_persistence(self):
        """Test that balance calculations remain consistent across restarts."""
        # Session 1: Setup with credit balance
        self.runner.invoke(cli, ["setup", "--rate", "2.50", "--balance", "-10.00"])

        # Session 2: Add transaction
        transaction_result = self.runner.invoke(
            cli, ["add-transaction", "--items", "4", "--payment", "5.00"]
        )
        # Balance: -10.00 + 10.00 - 5.00 = -5.00 (credit)
        assert "₹5.00 (you have credit)" in transaction_result.output

        # Session 3: Verify balance persisted correctly
        balance_result = self.runner.invoke(cli, ["balance"])
        assert balance_result.exit_code == 0
        assert "₹5.00 (you have credit)" in balance_result.output

        # Session 4: Add another transaction
        self.runner.invoke(
            cli, ["add-transaction", "--items", "6", "--payment", "10.00"]
        )
        # Balance: -5.00 + 15.00 - 10.00 = 0.00

        # Session 5: Verify final balance
        final_balance_result = self.runner.invoke(cli, ["balance"])
        assert final_balance_result.exit_code == 0
        assert "₹0.00 (all settled)" in final_balance_result.output

    def test_database_file_location(self):
        """Test that database file is created in the correct location."""
        # Setup account
        self.runner.invoke(cli, ["setup", "--rate", "2.00", "--balance", "5.00"])

        # Verify database file exists at expected location
        assert os.path.exists(self.db_path)
        assert os.path.isfile(self.db_path)

        # Verify database contains expected data
        db_manager = DatabaseManager(self.db_path)
        config = db_manager.get_configuration()
        assert config is not None
        assert config["rate_per_item"] == 2.00
        assert config["initial_balance"] == 5.00
        db_manager.close()


class TestErrorRecoveryAndEdgeCases:
    """Test error recovery scenarios and edge case handling."""

    def setup_method(self):
        """Set up test environment with temporary database directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "saldo.db")
        self.runner = CliRunner()

        # Patch DatabaseManager to use our test database path
        self.db_patcher = patch.object(DatabaseManager, "__init__", self._mock_db_init)
        self.db_patcher.start()

    def _mock_db_init(self, instance, db_path=None):
        """Mock DatabaseManager.__init__ to use test database path."""
        instance.db_path = self.db_path
        instance._connection = None

    def teardown_method(self):
        """Clean up test environment."""
        # Stop the patcher
        self.db_patcher.stop()

        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_commands_without_setup(self):
        """Test that commands fail gracefully when no setup exists."""
        # Try to add transaction without setup
        transaction_result = self.runner.invoke(
            cli, ["add-transaction", "--items", "5", "--payment", "10.00"]
        )
        assert transaction_result.exit_code != 0
        assert "No configuration found" in transaction_result.output
        assert "Please run 'saldo setup' first" in transaction_result.output

        # Try to check balance without setup
        balance_result = self.runner.invoke(cli, ["balance"])
        assert balance_result.exit_code != 0
        assert "No configuration found" in balance_result.output
        assert "Please run 'saldo setup' first" in balance_result.output

    def test_invalid_input_recovery_setup(self):
        """Test recovery from invalid inputs during setup."""
        # Test setup with invalid then valid inputs
        setup_result = self.runner.invoke(
            cli, ["setup"], input="abc\n-2.0\n0\n2.50\nxyz\n10.00\n"
        )
        assert setup_result.exit_code == 0
        assert "Please enter a valid number" in setup_result.output
        assert "Rate must be a positive number" in setup_result.output
        assert "Account setup completed successfully!" in setup_result.output
        assert "Rate per item: ₹2.50" in setup_result.output
        assert "₹10.00 (you owe)" in setup_result.output

    def test_invalid_input_recovery_transaction(self):
        """Test recovery from invalid inputs during transaction."""
        # Setup first
        self.runner.invoke(cli, ["setup", "--rate", "2.00", "--balance", "0.00"])

        # Test transaction with invalid then valid inputs
        transaction_result = self.runner.invoke(
            cli, ["add-transaction"], input="abc\n-1\n3\nxyz\n6.00\n"
        )
        assert transaction_result.exit_code == 0
        assert "Please enter a valid whole number" in transaction_result.output
        assert "Number of items cannot be negative" in transaction_result.output
        assert "Please enter a valid number" in transaction_result.output
        assert "Transaction recorded successfully!" in transaction_result.output

    def test_setup_overwrite_confirmation(self):
        """Test setup overwrite confirmation workflow."""
        # Initial setup
        self.runner.invoke(cli, ["setup", "--rate", "2.00", "--balance", "5.00"])

        # Try to setup again and cancel
        cancel_result = self.runner.invoke(cli, ["setup"], input="n\n")
        assert cancel_result.exit_code == 0
        assert "Configuration already exists!" in cancel_result.output
        assert "Setup cancelled." in cancel_result.output

        # Verify original configuration unchanged
        balance_result = self.runner.invoke(cli, ["balance"])
        assert "Rate per item: ₹2.00" in balance_result.output
        assert "₹5.00 (you owe)" in balance_result.output

        # Try to setup again and confirm overwrite
        overwrite_result = self.runner.invoke(cli, ["setup"], input="y\n3.50\n-10.00\n")
        assert overwrite_result.exit_code == 0
        assert "Configuration already exists!" in overwrite_result.output
        assert "Account setup completed successfully!" in overwrite_result.output
        assert "Rate per item: ₹3.50" in overwrite_result.output
        assert "₹10.00 (you have credit)" in overwrite_result.output

        # Verify new configuration is active
        new_balance_result = self.runner.invoke(cli, ["balance"])
        assert "Rate per item: ₹3.50" in new_balance_result.output
        assert "₹10.00 (you have credit)" in new_balance_result.output

    def test_large_numbers_handling(self):
        """Test handling of unusually large numbers."""
        # Setup with large rate (should prompt for confirmation)
        large_rate_result = self.runner.invoke(cli, ["setup"], input="1500.00\ny\n0\n")
        assert large_rate_result.exit_code == 0
        assert "Rate ₹1500.00 seems very high" in large_rate_result.output
        assert "Account setup completed successfully!" in large_rate_result.output

        # Add transaction with large item count (should prompt for confirmation)
        large_items_result = self.runner.invoke(
            cli, ["add-transaction"], input="2000\ny\n1000.00\n"
        )
        assert large_items_result.exit_code == 0
        assert "2000 items seems like a lot" in large_items_result.output
        assert "Transaction recorded successfully!" in large_items_result.output

    def test_negative_payment_handling(self):
        """Test handling of negative payments (refunds)."""
        # Setup account
        self.runner.invoke(cli, ["setup", "--rate", "2.00", "--balance", "10.00"])

        # Add transaction with negative payment (refund)
        refund_result = self.runner.invoke(
            cli, ["add-transaction"], input="2\n-5.00\ny\n"
        )
        assert refund_result.exit_code == 0
        assert "Negative payment (₹5.00 refund)" in refund_result.output
        assert "Transaction recorded successfully!" in refund_result.output
        # Balance: 10.00 + 4.00 - (-5.00) = 19.00
        assert "₹19.00 (you owe)" in refund_result.output

    def test_edge_case_zero_rate_validation(self):
        """Test that zero rate is properly rejected."""
        zero_rate_result = self.runner.invoke(
            cli, ["setup", "--rate", "0", "--balance", "10.00"]
        )
        assert zero_rate_result.exit_code != 0
        assert "Validation Error" in zero_rate_result.output
        assert "Rate must be a positive number" in zero_rate_result.output

    def test_edge_case_negative_items_validation(self):
        """Test that negative items are properly rejected."""
        # Setup first
        self.runner.invoke(cli, ["setup", "--rate", "2.00", "--balance", "0.00"])

        # Try negative items
        negative_items_result = self.runner.invoke(
            cli, ["add-transaction", "--items", "-5", "--payment", "10.00"]
        )
        assert negative_items_result.exit_code != 0
        assert "Validation Error" in negative_items_result.output
        assert "Number of items cannot be negative" in negative_items_result.output

    def test_database_directory_creation(self):
        """Test that database directory is created if it doesn't exist."""
        # Stop the current patcher
        self.db_patcher.stop()

        # Use a nested path that doesn't exist
        nested_db_path = os.path.join(self.temp_dir, "nested", "subdir", "saldo.db")

        # Create a new patcher for this specific test
        def mock_nested_db_init(instance, db_path=None):
            instance.db_path = nested_db_path
            instance._connection = None

        nested_patcher = patch.object(DatabaseManager, "__init__", mock_nested_db_init)
        nested_patcher.start()

        try:
            # Setup should create the directory structure
            setup_result = self.runner.invoke(
                cli, ["setup", "--rate", "2.00", "--balance", "5.00"]
            )
            assert setup_result.exit_code == 0
            assert "Account setup completed successfully!" in setup_result.output

            # Verify directory and file were created
            assert os.path.exists(nested_db_path)
            assert os.path.isfile(nested_db_path)

            # Verify data is accessible
            balance_result = self.runner.invoke(cli, ["balance"])
            assert balance_result.exit_code == 0
            assert "Rate per item: ₹2.00" in balance_result.output
            assert "₹5.00 (you owe)" in balance_result.output
        finally:
            # Clean up the nested patcher and restart the original
            nested_patcher.stop()
            self.db_patcher.start()


class TestCLIHelpAndVersion:
    """Test CLI help and version functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_main_cli_help(self):
        """Test main CLI help message."""
        help_result = self.runner.invoke(cli, ["--help"])
        assert help_result.exit_code == 0
        assert (
            "Saldo - A command-line balance tracking application" in help_result.output
        )
        assert "setup" in help_result.output
        assert "add-transaction" in help_result.output
        assert "balance" in help_result.output

    def test_cli_version(self):
        """Test CLI version display."""
        version_result = self.runner.invoke(cli, ["--version"])
        assert version_result.exit_code == 0
        assert "saldo, version 0.1.0" in version_result.output

    def test_setup_command_help(self):
        """Test setup command help."""
        setup_help_result = self.runner.invoke(cli, ["setup", "--help"])
        assert setup_help_result.exit_code == 0
        assert "Initialize the application" in setup_help_result.output
        assert "--rate" in setup_help_result.output
        assert "--balance" in setup_help_result.output

    def test_add_transaction_command_help(self):
        """Test add-transaction command help."""
        transaction_help_result = self.runner.invoke(cli, ["add-transaction", "--help"])
        assert transaction_help_result.exit_code == 0
        assert "Add a new ironing transaction" in transaction_help_result.output
        assert "--items" in transaction_help_result.output
        assert "--payment" in transaction_help_result.output

    def test_balance_command_help(self):
        """Test balance command help."""
        balance_help_result = self.runner.invoke(cli, ["balance", "--help"])
        assert balance_help_result.exit_code == 0
        assert "Display current balance" in balance_help_result.output
        assert "--detailed" in balance_help_result.output
        assert "--limit" in balance_help_result.output
