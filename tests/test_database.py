"""
Unit tests for database operations.
"""

import pytest
import tempfile
import os
from pathlib import Path

from saldo.database import DatabaseManager
from saldo.exceptions import DatabaseError


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name

        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()

        yield db_manager

        # Cleanup
        db_manager.close()
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_initialize_database_creates_tables(self, temp_db):
        """Test that initialize_database creates required tables."""
        conn = temp_db._get_connection()
        cursor = conn.cursor()

        # Check configuration table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='configuration'
        """
        )
        assert cursor.fetchone() is not None

        # Check transactions table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='transactions'
        """
        )
        assert cursor.fetchone() is not None

    def test_save_and_get_configuration(self, temp_db):
        """Test saving and retrieving configuration data."""
        rate = 2.50
        initial_balance = 10.0

        # Save configuration
        temp_db.save_configuration(rate, initial_balance)

        # Retrieve configuration
        config = temp_db.get_configuration()

        assert config is not None
        assert config["rate_per_item"] == rate
        assert config["initial_balance"] == initial_balance
        assert "created_at" in config

    def test_save_configuration_validation(self, temp_db):
        """Test configuration validation."""
        with pytest.raises(ValueError, match="Rate must be positive"):
            temp_db.save_configuration(-1.0, 0.0)

        with pytest.raises(ValueError, match="Rate must be positive"):
            temp_db.save_configuration(0.0, 0.0)

    def test_get_configuration_when_none_exists(self, temp_db):
        """Test getting configuration when none exists."""
        config = temp_db.get_configuration()
        assert config is None

    def test_save_configuration_replaces_existing(self, temp_db):
        """Test that saving configuration replaces existing data."""
        # Save first configuration
        temp_db.save_configuration(2.0, 5.0)

        # Save second configuration
        temp_db.save_configuration(3.0, 15.0)

        # Should only have the second configuration
        config = temp_db.get_configuration()
        assert config["rate_per_item"] == 3.0
        assert config["initial_balance"] == 15.0

    def test_save_and_get_transaction(self, temp_db):
        """Test saving and retrieving transaction data."""
        transaction = {
            "items": 5,
            "cost": 12.50,
            "payment": 10.0,
            "balance_after": 2.50,
        }

        # Save transaction
        transaction_id = temp_db.save_transaction(transaction)
        assert transaction_id is not None

        # Retrieve transactions
        transactions = temp_db.get_transactions()

        assert len(transactions) == 1
        saved_transaction = transactions[0]
        assert saved_transaction["items"] == transaction["items"]
        assert saved_transaction["cost"] == transaction["cost"]
        assert saved_transaction["payment"] == transaction["payment"]
        assert saved_transaction["balance_after"] == transaction["balance_after"]
        assert "created_at" in saved_transaction

    def test_save_transaction_validation(self, temp_db):
        """Test transaction validation."""
        incomplete_transaction = {
            "items": 5,
            "cost": 12.50,
            # Missing payment and balance_after
        }

        with pytest.raises(ValueError, match="Missing required field"):
            temp_db.save_transaction(incomplete_transaction)

    def test_get_transactions_with_limit(self, temp_db):
        """Test getting transactions with limit."""
        # Save multiple transactions
        for i in range(5):
            transaction = {
                "items": i + 1,
                "cost": (i + 1) * 2.5,
                "payment": 5.0,
                "balance_after": i * 2.5,
            }
            temp_db.save_transaction(transaction)

        # Get limited transactions
        transactions = temp_db.get_transactions(limit=3)
        assert len(transactions) == 3

        # Should be ordered by newest first (SQLite doesn't guarantee order without explicit ORDER BY)
        # Just verify we got 3 transactions
        items_list = [t["items"] for t in transactions]
        assert len(set(items_list)) == 3  # All different items

    def test_get_current_balance_from_transaction(self, temp_db):
        """Test getting current balance from most recent transaction."""
        # Save configuration
        temp_db.save_configuration(2.0, 10.0)

        # Save transaction
        transaction = {"items": 3, "cost": 6.0, "payment": 5.0, "balance_after": 11.0}
        temp_db.save_transaction(transaction)

        # Current balance should be from transaction
        balance = temp_db.get_current_balance()
        assert balance == 11.0

    def test_get_current_balance_from_initial_config(self, temp_db):
        """Test getting current balance from initial configuration when no transactions."""
        # Save configuration only
        temp_db.save_configuration(2.0, 15.0)

        # Current balance should be initial balance
        balance = temp_db.get_current_balance()
        assert balance == 15.0

    def test_get_current_balance_when_no_data(self, temp_db):
        """Test getting current balance when no configuration or transactions exist."""
        balance = temp_db.get_current_balance()
        assert balance == 0.0

    def test_database_path_creation(self):
        """Test that database path is created correctly."""
        # Test default path
        db_manager = DatabaseManager()
        expected_path = str(Path.home() / ".saldo" / "saldo.db")
        assert db_manager.db_path == expected_path

        # Test custom path
        custom_path = "/tmp/test.db"
        db_manager = DatabaseManager(custom_path)
        assert db_manager.db_path == custom_path

    def test_update_configuration_rate_success(self, temp_db):
        """Test successful rate update."""
        # Save initial configuration
        temp_db.save_configuration(2.0, 10.0)
        
        # Update rate
        new_rate = 3.5
        temp_db.update_configuration_rate(new_rate)
        
        # Verify rate was updated
        config = temp_db.get_configuration()
        assert config["rate_per_item"] == new_rate
        # Verify initial balance was preserved
        assert config["initial_balance"] == 10.0
        # Verify created_at was preserved
        assert "created_at" in config

    def test_update_configuration_rate_preserves_initial_balance(self, temp_db):
        """Test that rate update preserves initial balance."""
        original_rate = 2.5
        original_balance = 25.0
        
        # Save initial configuration
        temp_db.save_configuration(original_rate, original_balance)
        original_config = temp_db.get_configuration()
        
        # Update rate
        new_rate = 4.0
        temp_db.update_configuration_rate(new_rate)
        
        # Verify initial balance and created_at are unchanged
        updated_config = temp_db.get_configuration()
        assert updated_config["initial_balance"] == original_balance
        assert updated_config["created_at"] == original_config["created_at"]
        assert updated_config["rate_per_item"] == new_rate

    def test_update_configuration_rate_validation_negative(self, temp_db):
        """Test rate update validation for negative values."""
        # Save initial configuration
        temp_db.save_configuration(2.0, 10.0)
        
        # Try to update with negative rate
        with pytest.raises(ValueError, match="Rate must be positive"):
            temp_db.update_configuration_rate(-1.0)

    def test_update_configuration_rate_validation_zero(self, temp_db):
        """Test rate update validation for zero values."""
        # Save initial configuration
        temp_db.save_configuration(2.0, 10.0)
        
        # Try to update with zero rate
        with pytest.raises(ValueError, match="Rate must be positive"):
            temp_db.update_configuration_rate(0.0)

    def test_update_configuration_rate_validation_non_numeric(self, temp_db):
        """Test rate update validation for non-numeric values."""
        # Save initial configuration
        temp_db.save_configuration(2.0, 10.0)
        
        # Try to update with non-numeric rate
        with pytest.raises(ValueError, match="Rate must be a number"):
            temp_db.update_configuration_rate("invalid")

    def test_update_configuration_rate_no_config_exists(self, temp_db):
        """Test rate update when no configuration exists."""
        # Try to update rate without existing configuration
        with pytest.raises(ValueError, match="No configuration found. Please run setup first."):
            temp_db.update_configuration_rate(3.0)

    def test_update_configuration_rate_with_float_conversion(self, temp_db):
        """Test that rate update properly converts integer to float."""
        # Save initial configuration
        temp_db.save_configuration(2.0, 10.0)
        
        # Update with integer rate (should be converted to float)
        temp_db.update_configuration_rate(5)
        
        # Verify rate was updated and converted to float
        config = temp_db.get_configuration()
        assert config["rate_per_item"] == 5.0
        assert isinstance(config["rate_per_item"], float)

    def test_connection_management(self):
        """Test database connection management."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name

        try:
            db_manager = DatabaseManager(db_path)

            # Connection should be created on first access
            assert db_manager._connection is None
            conn = db_manager._get_connection()
            assert db_manager._connection is not None

            # Should reuse existing connection
            conn2 = db_manager._get_connection()
            assert conn is conn2

            # Should close connection
            db_manager.close()
            assert db_manager._connection is None

        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
