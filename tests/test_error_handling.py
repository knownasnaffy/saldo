"""
Comprehensive tests for error handling and validation across the Saldo application.

Tests edge cases, validation scenarios, and error recovery mechanisms.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from saldo.cli import cli
from saldo.transaction_manager import TransactionManager
from saldo.database import DatabaseManager
from saldo.exceptions import ValidationError, ConfigurationError, DatabaseError, SaldoError


class TestInputValidation:
    """Test cases for input validation across all components."""
    
    def setup_method(self):
        """Set up test environment with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.transaction_manager = TransactionManager(self.db_manager)
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Clean up test environment."""
        self.db_manager.close()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_setup_account_extreme_values(self):
        """Test setup_account with extreme values."""
        # Test very high rate
        with pytest.raises(ValidationError, match="Rate per item seems unusually high"):
            self.transaction_manager.setup_account(1500.0, 0.0)
        
        # Test very large initial balance
        with pytest.raises(ValidationError, match="Initial balance seems unusually large"):
            self.transaction_manager.setup_account(2.50, 2000000.0)
        
        # Test very large negative initial balance
        with pytest.raises(ValidationError, match="Initial balance seems unusually large"):
            self.transaction_manager.setup_account(2.50, -2000000.0)
    
    def test_setup_account_invalid_types(self):
        """Test setup_account with invalid data types."""
        # Test string rate
        with pytest.raises(ValidationError, match="Rate must be a number"):
            self.transaction_manager.setup_account("invalid", 0.0)
        
        # Test None rate
        with pytest.raises(ValidationError, match="Rate must be a number"):
            self.transaction_manager.setup_account(None, 0.0)
        
        # Test list as balance
        with pytest.raises(ValidationError, match="Initial balance must be a number"):
            self.transaction_manager.setup_account(2.50, [1, 2, 3])
    
    def test_calculate_cost_extreme_values(self):
        """Test calculate_cost with extreme values."""
        self.transaction_manager.setup_account(2.50, 0.0)
        
        # Test very large item count
        with pytest.raises(ValidationError, match="Number of items seems unusually large"):
            self.transaction_manager.calculate_cost(15000)
    
    def test_calculate_cost_invalid_types(self):
        """Test calculate_cost with invalid data types."""
        self.transaction_manager.setup_account(2.50, 0.0)
        
        # Test float items
        with pytest.raises(ValidationError, match="Number of items must be an integer"):
            self.transaction_manager.calculate_cost(2.5)
        
        # Test string items
        with pytest.raises(ValidationError, match="Number of items must be an integer"):
            self.transaction_manager.calculate_cost("5")
        
        # Test None items
        with pytest.raises(ValidationError, match="Number of items must be an integer"):
            self.transaction_manager.calculate_cost(None)
    
    def test_add_transaction_extreme_values(self):
        """Test add_transaction with extreme values."""
        self.transaction_manager.setup_account(2.50, 0.0)
        
        # Test very large item count
        with pytest.raises(ValidationError, match="Number of items seems unusually large"):
            self.transaction_manager.add_transaction(15000, 10.0)
        
        # Test very large payment
        with pytest.raises(ValidationError, match="Payment amount seems unusually large"):
            self.transaction_manager.add_transaction(5, 2000000.0)
        
        # Test transaction that would result in very large balance
        # First we need to get past the item count validation
        with pytest.raises(ValidationError, match="Number of items seems unusually large"):
            self.transaction_manager.add_transaction(500000, 0.0)  # This will fail on item count first
    
    def test_add_transaction_invalid_types(self):
        """Test add_transaction with invalid data types."""
        self.transaction_manager.setup_account(2.50, 0.0)
        
        # Test string payment
        with pytest.raises(ValidationError, match="Payment amount must be a number"):
            self.transaction_manager.add_transaction(5, "invalid")
        
        # Test None payment
        with pytest.raises(ValidationError, match="Payment amount must be a number"):
            self.transaction_manager.add_transaction(5, None)


class TestDatabaseErrorHandling:
    """Test cases for database error handling."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    def test_database_connection_failure(self):
        """Test handling of database connection failures."""
        # Try to create database in non-existent directory with no permissions
        with pytest.raises(DatabaseError, match="Cannot create database directory"):
            db_manager = DatabaseManager("/invalid/path/test.db")
            db_manager._get_connection()
    
    def test_database_locked_error(self):
        """Test handling of database locked errors."""
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        
        try:
            db_manager = DatabaseManager(temp_db.name)
            
            # Mock the cursor execute to raise database locked error
            with patch.object(db_manager, '_get_connection') as mock_get_conn:
                mock_conn = MagicMock()
                mock_cursor = MagicMock()
                mock_conn.cursor.return_value = mock_cursor
                mock_cursor.execute.side_effect = Exception("database is locked")
                mock_get_conn.return_value = mock_conn
                
                with pytest.raises(DatabaseError, match="Database is locked by another process"):
                    db_manager.initialize_database()
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)
    
    def test_disk_space_error(self):
        """Test handling of disk space errors."""
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        
        try:
            db_manager = DatabaseManager(temp_db.name)
            
            # Mock the cursor execute to raise disk I/O error
            with patch.object(db_manager, '_get_connection') as mock_get_conn:
                mock_conn = MagicMock()
                mock_cursor = MagicMock()
                mock_conn.cursor.return_value = mock_cursor
                mock_cursor.execute.side_effect = Exception("disk I/O error")
                mock_get_conn.return_value = mock_conn
                
                with pytest.raises(DatabaseError, match="Failed to initialize database"):
                    db_manager.initialize_database()
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)
    
    def test_corrupted_configuration_data(self):
        """Test handling of corrupted configuration data."""
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        
        try:
            db_manager = DatabaseManager(temp_db.name)
            db_manager.initialize_database()
            
            # Manually corrupt the configuration data by bypassing constraints
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            # First disable foreign key constraints to allow invalid data
            cursor.execute("PRAGMA foreign_keys = OFF")
            # Drop and recreate table without constraints
            cursor.execute("DROP TABLE configuration")
            cursor.execute("""
                CREATE TABLE configuration (
                    id INTEGER PRIMARY KEY,
                    rate_per_item REAL NOT NULL,
                    initial_balance REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("INSERT INTO configuration (rate_per_item, initial_balance) VALUES (?, ?)", 
                          (-1.0, 0.0))  # Invalid negative rate
            conn.commit()
            
            transaction_manager = TransactionManager(db_manager)
            
            with pytest.raises(ConfigurationError, match="Invalid rate in configuration"):
                transaction_manager._get_configuration()
        finally:
            db_manager.close()
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)


class TestCLIErrorHandling:
    """Test cases for CLI error handling and user interaction."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_command_high_rate_confirmation(self, mock_tm_class):
        """Test setup command with high rate requiring confirmation."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Test declining high rate confirmation
        result = self.runner.invoke(cli, ['setup'], input='1500.0\nn\n2.50\n0\n')
        
        assert result.exit_code == 0
        assert "Rate $1500.00 seems very high" in result.output
        assert "Account setup completed successfully!" in result.output
        mock_tm.setup_account.assert_called_once_with(2.50, 0.0)
    
    @patch('saldo.cli.TransactionManager')
    def test_setup_command_large_balance_confirmation(self, mock_tm_class):
        """Test setup command with large balance requiring confirmation."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Test accepting large balance confirmation
        result = self.runner.invoke(cli, ['setup'], input='2.50\n150000\ny\n')
        
        assert result.exit_code == 0
        assert "Balance $150000.00 seems very large" in result.output
        assert "Account setup completed successfully!" in result.output
        mock_tm.setup_account.assert_called_once_with(2.50, 150000.0)
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_large_items_confirmation(self, mock_tm_class):
        """Test add-transaction command with large item count requiring confirmation."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 0.0
        mock_tm.calculate_cost.return_value = 2500.0
        mock_tm.add_transaction.return_value = {
            'id': 1,
            'items': 1000,
            'cost': 2500.0,
            'payment': 2500.0,
            'balance_after': 0.0
        }
        
        # Test declining large item count confirmation
        result = self.runner.invoke(cli, ['add-transaction'], input='1500\nn\n5\n12.50\n')
        
        assert result.exit_code == 0
        assert "1500 items seems like a lot" in result.output
        assert "Transaction recorded successfully!" in result.output
        mock_tm.add_transaction.assert_called_once_with(5, 12.50)
    
    @patch('saldo.cli.TransactionManager')
    def test_add_transaction_negative_payment_confirmation(self, mock_tm_class):
        """Test add-transaction command with negative payment requiring confirmation."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 0.0
        mock_tm.calculate_cost.return_value = 12.50
        mock_tm.add_transaction.return_value = {
            'id': 1,
            'items': 5,
            'cost': 12.50,
            'payment': -10.0,
            'balance_after': 22.50
        }
        
        # Test accepting negative payment confirmation
        result = self.runner.invoke(cli, ['add-transaction'], input='5\n-10.0\ny\n')
        
        assert result.exit_code == 0
        assert "Negative payment ($10.00 refund)" in result.output
        assert "Transaction recorded successfully!" in result.output
        mock_tm.add_transaction.assert_called_once_with(5, -10.0)
    
    @patch('saldo.cli.TransactionManager')
    def test_empty_input_handling(self, mock_tm_class):
        """Test handling of empty inputs in CLI prompts."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None
        
        # Test empty rate input followed by valid input
        result = self.runner.invoke(cli, ['setup'], input=' \n2.50\n\n')  # Space then empty
        
        assert result.exit_code == 0
        assert "Rate cannot be empty" in result.output
        assert "Account setup completed successfully!" in result.output
        mock_tm.setup_account.assert_called_once_with(2.50, 0.0)


class TestErrorRecovery:
    """Test cases for error recovery and graceful degradation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    @patch('saldo.cli.TransactionManager')
    def test_balance_command_transaction_history_error(self, mock_tm_class):
        """Test balance command when transaction history retrieval fails."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0
        }
        mock_tm.get_current_balance.return_value = 15.0
        mock_tm.db_manager.get_transactions.side_effect = DatabaseError("Transaction query failed")
        
        # Should still show balance even if transaction history fails
        result = self.runner.invoke(cli, ['balance', '--detailed'])
        
        assert result.exit_code == 0
        assert "Current balance: $15.00 (you owe)" in result.output
        assert "Could not retrieve transaction history" in result.output
    
    @patch('saldo.cli.TransactionManager')
    def test_configuration_validation_error_recovery(self, mock_tm_class):
        """Test recovery from configuration validation errors."""
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        mock_tm.db_manager.get_configuration.return_value = None  # No existing config
        
        # Mock setup_account to raise validation error
        mock_tm.setup_account.side_effect = ValidationError("Rate per item seems unusually high", "Received value: 1500.0")
        
        result = self.runner.invoke(cli, ['setup', '--rate', '1500.0', '--balance', '0'])
        
        assert result.exit_code != 0
        assert "Validation Error" in result.output
        assert "Rate per item seems unusually high" in result.output
        assert "Received value: 1500.0" in result.output


class TestBusinessRuleValidation:
    """Test cases for business rule validation."""
    
    def setup_method(self):
        """Set up test environment with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.transaction_manager = TransactionManager(self.db_manager)
    
    def teardown_method(self):
        """Clean up test environment."""
        self.db_manager.close()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_configuration_integrity_validation(self):
        """Test validation of configuration data integrity."""
        self.transaction_manager.setup_account(2.50, 0.0)
        
        # Manually corrupt configuration by removing required field
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE configuration DROP COLUMN rate_per_item")
        
        # This should be caught by the enhanced validation
        with pytest.raises(Exception):  # Could be DatabaseError or ConfigurationError
            self.transaction_manager._get_configuration()
    
    def test_transaction_data_validation(self):
        """Test validation of transaction data before saving."""
        self.transaction_manager.setup_account(2.50, 0.0)
        
        # Test invalid transaction data
        invalid_transaction = {
            'items': -1,  # Invalid negative items
            'cost': 5.0,
            'payment': 5.0,
            'balance_after': 0.0
        }
        
        with pytest.raises(ValueError, match="Items cannot be negative"):
            self.db_manager.save_transaction(invalid_transaction)
    
    def test_cost_calculation_consistency(self):
        """Test that cost calculations remain consistent."""
        self.transaction_manager.setup_account(2.50, 0.0)
        
        # Calculate cost multiple times - should be consistent
        cost1 = self.transaction_manager.calculate_cost(5)
        cost2 = self.transaction_manager.calculate_cost(5)
        cost3 = self.transaction_manager.calculate_cost(5)
        
        assert cost1 == cost2 == cost3 == 12.50
        
        # Test with zero items
        assert self.transaction_manager.calculate_cost(0) == 0.0


class TestExceptionHierarchy:
    """Test cases for proper exception hierarchy and handling."""
    
    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit properly."""
        # All custom exceptions should inherit from SaldoError
        assert issubclass(DatabaseError, SaldoError)
        assert issubclass(ValidationError, SaldoError)
        assert issubclass(ConfigurationError, SaldoError)
        
        # All should ultimately inherit from Exception
        assert issubclass(SaldoError, Exception)
        assert issubclass(DatabaseError, Exception)
        assert issubclass(ValidationError, Exception)
        assert issubclass(ConfigurationError, Exception)
    
    def test_exception_details_handling(self):
        """Test that exception details are handled properly."""
        # Test with details
        error = ValidationError("Main message", "Additional details")
        assert str(error) == "Main message: Additional details"
        assert error.message == "Main message"
        assert error.details == "Additional details"
        
        # Test without details
        error = ValidationError("Main message")
        assert str(error) == "Main message"
        assert error.message == "Main message"
        assert error.details is None
    
    def test_exception_catching_hierarchy(self):
        """Test that exceptions can be caught at different levels."""
        # Specific exception should be caught by base class
        try:
            raise ValidationError("Test error")
        except SaldoError as e:
            assert isinstance(e, ValidationError)
            assert isinstance(e, SaldoError)
        
        # Base exception should not be caught by specific class
        with pytest.raises(SaldoError):
            try:
                raise SaldoError("Base error")
            except ValidationError:
                pytest.fail("Base SaldoError should not be caught as ValidationError")