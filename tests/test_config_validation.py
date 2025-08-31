"""
Test cases for enhanced config command validation and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from saldo.cli import cli
from saldo.exceptions import ValidationError, ConfigurationError, DatabaseError


class TestConfigValidation:
    """Test cases for config command input validation and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("saldo.cli.TransactionManager")
    def test_config_negative_rate_validation(self, mock_tm_class):
        """Test config command with negative rate (should fail with clear error)."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }

        result = self.runner.invoke(cli, ["config", "--rate", "-2.5"])

        assert result.exit_code != 0
        assert "❌" in result.output
        assert "positive" in result.output.lower()
        assert "💡" in result.output  # Should have helpful tip

    @patch("saldo.cli.TransactionManager")
    def test_config_zero_rate_validation(self, mock_tm_class):
        """Test config command with zero rate (should fail with clear error)."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }

        result = self.runner.invoke(cli, ["config", "--rate", "0"])

        assert result.exit_code != 0
        assert "❌" in result.output
        assert "positive" in result.output.lower()
        assert "💡" in result.output  # Should have helpful tip

    @patch("saldo.cli.TransactionManager")
    def test_config_very_small_rate_validation(self, mock_tm_class):
        """Test config command with very small rate (should fail with clear error)."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }

        result = self.runner.invoke(cli, ["config", "--rate", "0.005"])

        assert result.exit_code != 0
        assert "❌" in result.output
        assert "too small" in result.output.lower()
        assert "💡" in result.output  # Should have helpful tip

    @patch("saldo.cli.TransactionManager")
    def test_config_high_rate_confirmation_decline(self, mock_tm_class):
        """Test config command with high rate and user declines confirmation."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }

        # User declines the confirmation
        result = self.runner.invoke(cli, ["config", "--rate", "150"], input="n\n")

        assert result.exit_code == 0  # Should exit cleanly
        assert "cancelled" in result.output.lower()
        assert "⚠️" in result.output  # Should show warning
        # Should not call update_rate since user declined
        mock_tm.update_rate.assert_not_called()

    @patch("saldo.cli.TransactionManager")
    def test_config_very_high_rate_with_no_confirm(self, mock_tm_class):
        """Test config command with very high rate using --no-confirm flag."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }
        
        # Mock successful update
        mock_tm.update_rate.return_value = {
            'old_rate': 2.50,
            'new_rate': 1500.0,
            'updated_at': '2024-01-01 10:00:00'
        }

        result = self.runner.invoke(cli, ["config", "--rate", "1500", "--no-confirm"])

        assert result.exit_code == 0
        assert "⚠️" in result.output  # Should show warning even with --no-confirm
        assert "✅" in result.output  # Should show success
        mock_tm.update_rate.assert_called_once_with(1500.0)

    @patch("saldo.cli.TransactionManager")
    def test_config_database_error_handling(self, mock_tm_class):
        """Test config command with database error (should show user-friendly message)."""
        # Mock TransactionManager to raise DatabaseError
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock database error on configuration retrieval
        mock_tm.db_manager.get_configuration.side_effect = DatabaseError(
            "Database is locked by another process"
        )

        result = self.runner.invoke(cli, ["config"])

        assert result.exit_code != 0
        assert "❌" in result.output
        assert "locked" in result.output.lower()
        assert "💡" in result.output  # Should have helpful tip

    @patch("saldo.cli.TransactionManager")
    def test_config_no_configuration_error_handling(self, mock_tm_class):
        """Test config command when no configuration exists (should show helpful message)."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock no configuration found
        mock_tm.db_manager.get_configuration.return_value = None

        result = self.runner.invoke(cli, ["config"])

        assert result.exit_code != 0
        assert "❌" in result.output
        assert "No configuration found" in result.output
        assert "saldo setup" in result.output
        assert "💡" in result.output  # Should have helpful tip

    @patch("saldo.cli.TransactionManager")
    def test_config_update_validation_error_handling(self, mock_tm_class):
        """Test config command when update_rate raises ValidationError."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }
        
        # Mock ValidationError on update
        mock_tm.update_rate.side_effect = ValidationError("Rate per item seems unusually high")

        result = self.runner.invoke(cli, ["config", "--rate", "3.50", "--no-confirm"])

        assert result.exit_code != 0
        assert "❌" in result.output
        assert "Rate validation failed" in result.output
        assert "too high" in result.output
        assert "💡" in result.output  # Should have helpful tip

    @patch("saldo.cli.TransactionManager")
    def test_config_update_database_error_handling(self, mock_tm_class):
        """Test config command when update_rate raises DatabaseError."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }
        
        # Mock DatabaseError on update
        mock_tm.update_rate.side_effect = DatabaseError("Database constraint violation")

        result = self.runner.invoke(cli, ["config", "--rate", "3.50", "--no-confirm"])

        assert result.exit_code != 0
        assert "❌" in result.output
        assert "Failed to update rate" in result.output
        assert "constraint" in result.output.lower()
        assert "💡" in result.output  # Should have helpful tip

    @patch("saldo.cli.TransactionManager")
    def test_config_display_configuration_error_handling(self, mock_tm_class):
        """Test config command display when get_configuration_display raises ConfigurationError."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration check passes
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }
        
        # Mock ConfigurationError on display
        mock_tm.get_configuration_display.side_effect = ConfigurationError("Configuration is corrupted")

        result = self.runner.invoke(cli, ["config"])

        assert result.exit_code != 0
        assert "❌" in result.output
        assert "Configuration Error" in result.output
        assert "💡" in result.output  # Should have helpful tip

    @patch("saldo.cli.TransactionManager")
    def test_config_display_balance_error_handling(self, mock_tm_class):
        """Test config command display when get_current_balance raises DatabaseError."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }
        
        # Mock successful configuration display
        mock_tm.get_configuration_display.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }
        
        # Mock DatabaseError on balance retrieval
        mock_tm.get_current_balance.side_effect = DatabaseError("Cannot access transactions")

        result = self.runner.invoke(cli, ["config"])

        assert result.exit_code == 0  # Should still succeed
        assert "⚙️" in result.output  # Should show configuration
        assert "⚠️" in result.output  # Should show warning about balance
        assert "Could not retrieve current balance" in result.output

    @patch("saldo.cli.TransactionManager")
    def test_config_valid_rate_update_success(self, mock_tm_class):
        """Test config command with valid rate update (should succeed with clear messages)."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }
        
        # Mock successful update
        mock_tm.update_rate.return_value = {
            'old_rate': 2.50,
            'new_rate': 3.50,
            'updated_at': '2024-01-01 10:00:00'
        }

        result = self.runner.invoke(cli, ["config", "--rate", "3.50", "--no-confirm"])

        assert result.exit_code == 0
        assert "✅" in result.output  # Should show success
        assert "Rate updated successfully" in result.output
        assert "₹3.50" in result.output
        assert "Historical transactions remain unchanged" in result.output
        mock_tm.update_rate.assert_called_once_with(3.50)

    def test_config_invalid_rate_format_click_validation(self):
        """Test config command with invalid rate format (handled by Click)."""
        result = self.runner.invoke(cli, ["config", "--rate", "abc"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output or "Error" in result.output

    @patch("saldo.cli.TransactionManager")
    def test_config_moderate_high_rate_confirmation(self, mock_tm_class):
        """Test config command with moderately high rate (100-1000) shows softer warning."""
        # Mock TransactionManager
        mock_tm = MagicMock()
        mock_tm_class.return_value = mock_tm
        
        # Mock existing configuration
        mock_tm.db_manager.get_configuration.return_value = {
            'rate_per_item': 2.50,
            'initial_balance': 0.0,
            'created_at': '2024-01-01 10:00:00'
        }

        # User declines the confirmation
        result = self.runner.invoke(cli, ["config", "--rate", "150"], input="n\n")

        assert result.exit_code == 0
        assert "quite high" in result.output  # Should show softer warning
        assert "cancelled" in result.output.lower()
        mock_tm.update_rate.assert_not_called()